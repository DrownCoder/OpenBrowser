#!/usr/bin/env python3
"""
Bridge OpenBrowser's SSE conversation API into a CLI that Clawdbot/OpenClaw can call.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional, TextIO, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_SERVER_URL = "http://127.0.0.1:8765"
DEFAULT_STATE_FILE = ".openbrowser_clawdbot_session.json"


def utc_now_iso() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class BridgeSessionState:
    """Persisted bridge session metadata."""

    conversation_id: str
    cwd: str
    server_url: str
    updated_at: str


def state_file_for(cwd: str, filename: str = DEFAULT_STATE_FILE) -> Path:
    """Resolve the session state file path for a workspace."""
    return Path(cwd).resolve() / filename


def load_state(cwd: str, filename: str = DEFAULT_STATE_FILE) -> Optional[BridgeSessionState]:
    """Load persisted bridge session state if it exists."""
    state_file = state_file_for(cwd, filename)
    if not state_file.exists():
        return None

    with state_file.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return BridgeSessionState(**data)


def save_state(
    cwd: str,
    conversation_id: str,
    server_url: str,
    filename: str = DEFAULT_STATE_FILE,
) -> BridgeSessionState:
    """Persist bridge session state for future rounds."""
    state = BridgeSessionState(
        conversation_id=conversation_id,
        cwd=str(Path(cwd).resolve()),
        server_url=server_url.rstrip("/"),
        updated_at=utc_now_iso(),
    )
    state_file = state_file_for(cwd, filename)
    state_file.write_text(
        json.dumps(asdict(state), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return state


def clear_state(cwd: str, filename: str = DEFAULT_STATE_FILE) -> bool:
    """Remove persisted bridge session state if it exists."""
    state_file = state_file_for(cwd, filename)
    if state_file.exists():
        state_file.unlink()
        return True
    return False


def request_json(url: str, method: str = "GET", payload: Optional[dict] = None) -> dict:
    """Execute a JSON request against the OpenBrowser server."""
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = Request(url, data=data, headers=headers, method=method)
    with urlopen(req, timeout=20) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body) if body else {}


def create_conversation(server_url: str, cwd: str) -> str:
    """Create a new OpenBrowser conversation."""
    response = request_json(
        f"{server_url.rstrip('/')}/agent/conversations",
        method="POST",
        payload={"cwd": str(Path(cwd).resolve())},
    )
    return response["conversation_id"]


def check_server(base_url: str) -> dict:
    """Return a compact readiness snapshot for callers."""
    base_url = base_url.rstrip("/")
    health = request_json(f"{base_url}/health")
    api = request_json(f"{base_url}/api")
    llm = request_json(f"{base_url}/api/config/llm")
    return {
        "health": health,
        "api": api,
        "llm": llm,
    }


def parse_sse_stream(lines: Iterable[str]) -> Iterator[Tuple[str, dict]]:
    """Parse an SSE response into event tuples."""
    event_type = None
    data_lines = []

    for raw_line in lines:
        line = raw_line.rstrip("\r\n")
        if not line:
            if event_type and data_lines:
                payload = json.loads("\n".join(data_lines))
                yield event_type, payload
            event_type = None
            data_lines = []
            continue

        if line.startswith(":"):
            continue
        if line.startswith("event:"):
            event_type = line[6:].strip()
        elif line.startswith("data:"):
            data_lines.append(line[5:].strip())

    if event_type and data_lines:
        payload = json.loads("\n".join(data_lines))
        yield event_type, payload


def format_event(event_type: str, payload: dict) -> str:
    """Convert an SSE event into concise human-readable output."""
    if event_type == "complete":
        return f"[complete] {payload.get('message', 'Conversation completed')}"
    if event_type == "error":
        return f"[error] {payload.get('error', 'Unknown error')}"
    if event_type != "agent_event":
        return f"[{event_type}] {json.dumps(payload, ensure_ascii=False)}"

    payload_type = payload.get("type", "unknown")
    if payload_type == "MessageEvent":
        role = payload.get("role", "unknown")
        text = payload.get("text", "").strip()
        return f"[message:{role}] {text}"
    if payload_type == "ThoughtEvent":
        thought = payload.get("thought") or payload.get("content") or ""
        return f"[thought] {thought.strip()}"
    if payload_type == "ActionEvent":
        text = payload.get("text", "").strip()
        return f"[action] {text}"
    if payload_type == "ObservationEvent":
        success = payload.get("success", False)
        message = payload.get("message") or payload.get("text") or ""
        status = "ok" if success else "failed"
        return f"[observation:{status}] {message.strip()}"
    if payload_type == "ErrorEvent":
        return f"[agent-error] {payload.get('error', 'Unknown error')}"
    return f"[agent:{payload_type}] {json.dumps(payload, ensure_ascii=False)}"


def extract_text_result(event_type: str, payload: dict) -> Optional[str]:
    """Extract the final user-facing text from an SSE event."""
    if event_type == "error":
        return payload.get("error")
    if event_type != "agent_event":
        return None

    payload_type = payload.get("type", "unknown")
    if payload_type == "MessageEvent" and payload.get("role") == "assistant":
        text = payload.get("text", "").strip()
        return text or None
    if payload_type == "ErrorEvent":
        return payload.get("error")
    return None


def stream_message(
    server_url: str,
    conversation_id: str,
    task: str,
    cwd: str,
    output: TextIO,
    as_jsonl: bool = False,
    stream: bool = False,
) -> int:
    """Send a message to OpenBrowser and return either streamed or final text output."""
    req = Request(
        f"{server_url.rstrip('/')}/agent/conversations/{conversation_id}/messages",
        data=json.dumps({"text": task, "cwd": str(Path(cwd).resolve())}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
        method="POST",
    )

    exit_code = 0
    latest_text_result: Optional[str] = None
    error_result: Optional[str] = None
    with urlopen(req, timeout=None) as resp:
        lines = (line.decode("utf-8") for line in resp)
        for event_type, payload in parse_sse_stream(lines):
            extracted_text = extract_text_result(event_type, payload)
            if extracted_text:
                if event_type == "error" or (
                    event_type == "agent_event" and payload.get("type") == "ErrorEvent"
                ):
                    error_result = extracted_text
                else:
                    latest_text_result = extracted_text

            if stream:
                if as_jsonl:
                    output.write(
                        json.dumps(
                            {"event": event_type, "payload": payload},
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                else:
                    output.write(format_event(event_type, payload) + "\n")
                output.flush()

            if event_type == "error":
                exit_code = 1

    if not stream:
        if error_result:
            output.write(error_result + "\n")
            output.flush()
            return 1

        if latest_text_result:
            output.write(latest_text_result + "\n")
            output.flush()
        else:
            output.write("OpenBrowser task finished, but no assistant text was returned.\n")
            output.flush()
    return exit_code


def resolve_conversation_id(
    server_url: str,
    cwd: str,
    explicit_conversation_id: Optional[str],
    new_session: bool,
    state_filename: str,
) -> BridgeSessionState:
    """Resolve or create a reusable OpenBrowser conversation."""
    if explicit_conversation_id:
        return save_state(cwd, explicit_conversation_id, server_url, state_filename)

    if not new_session:
        saved = load_state(cwd, state_filename)
        if saved and saved.server_url.rstrip("/") == server_url.rstrip("/"):
            return save_state(cwd, saved.conversation_id, server_url, state_filename)

    conversation_id = create_conversation(server_url, cwd)
    return save_state(cwd, conversation_id, server_url, state_filename)


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(
        description="Bridge Clawdbot/OpenClaw conversations into OpenBrowser.",
    )
    def add_shared_options(target: argparse.ArgumentParser) -> None:
        target.add_argument(
            "--server",
            default=DEFAULT_SERVER_URL,
            help=f"OpenBrowser server URL (default: {DEFAULT_SERVER_URL})",
        )
        target.add_argument(
            "--cwd",
            default=".",
            help="Workspace directory whose session state should be reused.",
        )
        target.add_argument(
            "--state-file",
            default=DEFAULT_STATE_FILE,
            help=f"Session state filename stored under --cwd (default: {DEFAULT_STATE_FILE})",
        )

    add_shared_options(parser)

    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run", help="Send a prompt to OpenBrowser, reusing the saved conversation."
    )
    add_shared_options(run_parser)
    run_parser.add_argument("task", help="Prompt to send to OpenBrowser.")
    run_parser.add_argument(
        "--conversation-id",
        help="Force a specific conversation ID instead of the saved session.",
    )
    run_parser.add_argument(
        "--new-session",
        action="store_true",
        help="Create a fresh OpenBrowser conversation before sending the prompt.",
    )
    run_parser.add_argument(
        "--jsonl",
        action="store_true",
        help="Emit raw SSE events as JSON lines instead of formatted text.",
    )
    run_parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream intermediate OpenBrowser events instead of returning only the final text result.",
    )

    check_parser = subparsers.add_parser("check", help="Check OpenBrowser readiness.")
    add_shared_options(check_parser)
    status_parser = subparsers.add_parser(
        "status", help="Show the saved bridge conversation state."
    )
    add_shared_options(status_parser)
    reset_parser = subparsers.add_parser(
        "reset", help="Delete the saved bridge conversation state."
    )
    add_shared_options(reset_parser)

    return parser


def handle_check(server_url: str) -> int:
    """Handle the readiness check command."""
    try:
        data = check_server(server_url)
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"[error] unable to reach OpenBrowser: {exc}", file=sys.stderr)
        return 1

    health_ok = data.get("health", {}).get("status") == "healthy"
    api = data.get("api", {})
    llm = data.get("llm", {}).get("config", {})
    ready = bool(health_ok and api.get("websocket_connected") and llm.get("has_api_key"))

    summary = {
        "ready": ready,
        "server_healthy": health_ok,
        "extension_connected": api.get("websocket_connected", False),
        "extension_connections": api.get("websocket_connections", 0),
        "llm_model": llm.get("model"),
        "llm_has_api_key": llm.get("has_api_key", False),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if ready else 1


def handle_status(cwd: str, state_filename: str) -> int:
    """Handle the status command."""
    state = load_state(cwd, state_filename)
    if not state:
        print(json.dumps({"saved_session": False}, indent=2))
        return 1

    print(
        json.dumps(
            {"saved_session": True, **asdict(state)},
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def handle_reset(cwd: str, state_filename: str) -> int:
    """Handle the reset command."""
    deleted = clear_state(cwd, state_filename)
    print(json.dumps({"deleted": deleted}, indent=2))
    return 0


def handle_run(args: argparse.Namespace) -> int:
    """Handle the main run command."""
    cwd = str(Path(args.cwd).resolve())
    try:
        state = resolve_conversation_id(
            args.server,
            cwd,
            args.conversation_id,
            args.new_session,
            args.state_file,
        )
        print(
            json.dumps(
                {
                    "conversation_id": state.conversation_id,
                    "cwd": state.cwd,
                    "server_url": state.server_url,
                },
                ensure_ascii=False,
            )
        )
        return stream_message(
            args.server,
            state.conversation_id,
            args.task,
            cwd,
            sys.stdout,
            as_jsonl=args.jsonl,
            stream=args.stream,
        )
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"[error] request failed: {exc}", file=sys.stderr)
        return 1


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "check":
        return handle_check(args.server)
    if args.command == "status":
        return handle_status(args.cwd, args.state_file)
    if args.command == "reset":
        return handle_reset(args.cwd, args.state_file)
    if args.command == "run":
        return handle_run(args)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
