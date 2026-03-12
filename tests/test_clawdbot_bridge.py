import json

from server.clawdbot_bridge import (
    extract_text_result,
    format_event,
    load_state,
    parse_sse_stream,
    save_state,
)


def test_save_and_load_state_round_trip(tmp_path):
    state = save_state(str(tmp_path), "conv-123", "http://127.0.0.1:8765")

    loaded = load_state(str(tmp_path))

    assert loaded is not None
    assert loaded.conversation_id == state.conversation_id
    assert loaded.cwd == state.cwd
    assert loaded.server_url == state.server_url


def test_parse_sse_stream_reads_multiple_events():
    lines = [
        "event: agent_event\n",
        'data: {"type":"MessageEvent","role":"assistant","text":"hello"}\n',
        "\n",
        "event: complete\n",
        'data: {"message":"done"}\n',
        "\n",
    ]

    events = list(parse_sse_stream(lines))

    assert events == [
        ("agent_event", {"type": "MessageEvent", "role": "assistant", "text": "hello"}),
        ("complete", {"message": "done"}),
    ]


def test_format_event_for_observation_event():
    payload = {
        "type": "ObservationEvent",
        "success": True,
        "message": "Captured screenshot",
    }

    assert format_event("agent_event", payload) == "[observation:ok] Captured screenshot"


def test_extract_text_result_prefers_assistant_messages():
    payload = {
        "type": "MessageEvent",
        "role": "assistant",
        "text": "Found 12 backend jobs and summarized the top 5.",
    }

    assert (
        extract_text_result("agent_event", payload)
        == "Found 12 backend jobs and summarized the top 5."
    )


def test_extract_text_result_reads_errors():
    assert extract_text_result("error", {"error": "server unavailable"}) == "server unavailable"
