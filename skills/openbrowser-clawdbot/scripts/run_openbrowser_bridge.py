#!/usr/bin/env python3
"""
Self-contained bridge from OpenClaw/Clawdbot into a running OpenBrowser server.

This script intentionally avoids importing from the OpenBrowser repo so the skill
can be installed and executed as a standalone skill package.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Optional, TextIO, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_SERVER_URL = "http://127.0.0.1:8765"
DEFAULT_STATE_FILE = ".openbrowser_clawdbot_session.json"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class BridgeSessionState:
    conversation_id: str
    cwd: str
    server_url: str
    updated_at: str


def state_file_for(cwd: str, filename: str = DEFAULT_STATE_FILE) -> Path:
    return Path(cwd).resolve() / filename


def load_state(cwd: str, filename: str = DEFAULT_STATE_FILE) -> Optional[BridgeSessionState]:
    state_file = state_file_for(cwd, filename)
    if not state_file.exists():
        return None
    with state_file.open("r", encoding="utf-8") as fh:
        return BridgeSessionState(**json.load(fh))


def save_state(
    cwd: str,
    conversation_id: str,
    server_url: str,
    filename: str = DEFAULT_STATE_FILE,
) -> BridgeSessionState:
    state = BridgeSessionState(
        conversation_id=conversation_id,
        cwd=str(Path(cwd).resolve()),
        server_url=server_url.rstrip("/"),
        updated_at=utc_now_iso(),
    )
    state_file_for(cwd, filename).write_text(
        json.dumps(asdict(state), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return state


def clear_state(cwd: str, filename: str = DEFAULT_STATE_FILE) -> bool:
    state_file = state_file_for(cwd, filename)
    if state_file.exists():
        state_file.unlink()
        return True
    return False


def request_json(url: str, method: str = "GET", payload: Optional[dict] = None) -> dict:
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
    response = request_json(
        f"{server_url.rstrip('/')}/agent/conversations",
        method="POST",
        payload={"cwd": str(Path(cwd).resolve())},
    )
    return response["conversation_id"]


def check_server(server_url: str) -> dict:
    server_url = server_url.rstrip("/")
    health = request_json(f"{server_url}/health")
    api = request_json(f"{server_url}/api")
    llm = request_json(f"{server_url}/api/config/llm")
    return {"health": health, "api": api, "llm": llm}


def parse_sse_stream(lines: Iterable[str]) -> Iterator[Tuple[str, dict]]:
    event_type = None
    data_lines: list[str] = []
    for raw_line in lines:
        line = raw_line.rstrip("\r\n")
        if not line:
            if event_type and data_lines:
                yield event_type, json.loads("\n".join(data_lines))
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
        yield event_type, json.loads("\n".join(data_lines))


def format_event(event_type: str, payload: dict) -> str:
    if event_type == "complete":
        return f"[complete] {payload.get('message', 'Conversation completed')}"
    if event_type == "error":
        return f"[error] {payload.get('error', 'Unknown error')}"
    if event_type != "agent_event":
        return f"[{event_type}] {json.dumps(payload, ensure_ascii=False)}"

    payload_type = payload.get("type", "unknown")
    if payload_type == "MessageEvent":
        return f"[message:{payload.get('role', 'unknown')}] {payload.get('text', '').strip()}"
    if payload_type == "ThoughtEvent":
        return f"[thought] {(payload.get('thought') or payload.get('content') or '').strip()}"
    if payload_type == "ActionEvent":
        return f"[action] {payload.get('text', '').strip()}"
    if payload_type == "ObservationEvent":
        status = "ok" if payload.get("success", False) else "failed"
        message = payload.get("message") or payload.get("text") or ""
        return f"[observation:{status}] {message.strip()}"
    if payload_type == "ErrorEvent":
        return f"[agent-error] {payload.get('error', 'Unknown error')}"
    return f"[agent:{payload_type}] {json.dumps(payload, ensure_ascii=False)}"


def extract_text_result(event_type: str, payload: dict) -> Optional[str]:
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
    req = Request(
        f"{server_url.rstrip('/')}/agent/conversations/{conversation_id}/messages",
        data=json.dumps({"text": task, "cwd": str(Path(cwd).resolve())}).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
        method="POST",
    )

    latest_text_result: Optional[str] = None
    error_result: Optional[str] = None
    exit_code = 0

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
                        json.dumps({"event": event_type, "payload": payload}, ensure_ascii=False)
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
    if explicit_conversation_id:
        return save_state(cwd, explicit_conversation_id, server_url, state_filename)

    if not new_session:
        saved = load_state(cwd, state_filename)
        if saved and saved.server_url.rstrip("/") == server_url.rstrip("/"):
            return save_state(cwd, saved.conversation_id, server_url, state_filename)

    return save_state(cwd, create_conversation(server_url, cwd), server_url, state_filename)


def add_shared_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--server", default=DEFAULT_SERVER_URL, help=f"OpenBrowser server URL (default: {DEFAULT_SERVER_URL})")
    parser.add_argument("--cwd", default=".", help="Workspace directory whose session state should be reused.")
    parser.add_argument("--state-file", default=DEFAULT_STATE_FILE, help=f"Session state filename stored under --cwd (default: {DEFAULT_STATE_FILE})")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Self-contained bridge from OpenClaw into OpenBrowser."
    )
    add_shared_options(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Send a prompt to OpenBrowser.")
    add_shared_options(run_parser)
    run_parser.add_argument("task", help="Prompt to send to OpenBrowser.")
    run_parser.add_argument("--conversation-id", help="Force a specific conversation ID.")
    run_parser.add_argument("--new-session", action="store_true", help="Create a fresh conversation before sending the prompt.")
    run_parser.add_argument("--jsonl", action="store_true", help="Emit raw SSE events as JSON lines.")
    run_parser.add_argument("--stream", action="store_true", help="Stream intermediate events instead of only the final text result.")

    check_parser = subparsers.add_parser("check", help="Check OpenBrowser readiness.")
    add_shared_options(check_parser)
    status_parser = subparsers.add_parser("status", help="Show the saved conversation state.")
    add_shared_options(status_parser)
    reset_parser = subparsers.add_parser("reset", help="Delete the saved conversation state.")
    add_shared_options(reset_parser)
    return parser


def handle_check(server_url: str) -> int:
    try:
        data = check_server(server_url)
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"[error] unable to reach OpenBrowser: {exc}", file=sys.stderr)
        return 1

    health_ok = data.get("health", {}).get("status") == "healthy"
    api = data.get("api", {})
    llm = data.get("llm", {}).get("config", {})
    ready = bool(health_ok and api.get("websocket_connected") and llm.get("has_api_key"))
    print(
        json.dumps(
            {
                "ready": ready,
                "server_healthy": health_ok,
                "extension_connected": api.get("websocket_connected", False),
                "extension_connections": api.get("websocket_connections", 0),
                "llm_model": llm.get("model"),
                "llm_has_api_key": llm.get("has_api_key", False),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if ready else 1


def handle_status(cwd: str, state_filename: str) -> int:
    state = load_state(cwd, state_filename)
    if not state:
        print(json.dumps({"saved_session": False}, indent=2))
        return 1
    print(json.dumps({"saved_session": True, **asdict(state)}, indent=2, ensure_ascii=False))
    return 0


def handle_reset(cwd: str, state_filename: str) -> int:
    print(json.dumps({"deleted": clear_state(cwd, state_filename)}, indent=2))
    return 0


def handle_run(args: argparse.Namespace) -> int:
    cwd = str(Path(args.cwd).resolve())
    try:
        state = resolve_conversation_id(
            args.server,
            cwd,
            args.conversation_id,
            args.new_session,
            args.state_file,
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
