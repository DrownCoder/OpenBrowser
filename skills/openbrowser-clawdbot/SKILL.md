---
name: openbrowser-clawdbot
description: Use this skill when the user wants Clawdbot/OpenClaw to control the local OpenBrowser panel through natural-language conversation. Reuses a persistent OpenBrowser conversation so multi-turn browser tasks can continue in the same session.
---

# OpenBrowser Clawdbot Bridge

Use this skill when Clawdbot/OpenClaw should drive the existing OpenBrowser panel instead of calling the browser directly.

## What this skill does

- Reuses the existing OpenBrowser agent, panel, and Chrome extension
- Persists one OpenBrowser `conversation_id` per workspace
- Lets Clawdbot continue a browser task across multiple chat turns

## Prerequisites

Run this before the first browser task:

```bash
uv run openbrowser-clawdbot check --cwd .
```

The bridge is ready only when:

- `server_healthy` is `true`
- `extension_connected` is `true`
- `llm_has_api_key` is `true`

If not ready, start and configure OpenBrowser first.

## Main command

Send a prompt into the existing OpenBrowser panel session:

```bash
uv run openbrowser-clawdbot run "Open LinkedIn Jobs and search for staff backend engineer roles in San Francisco" --cwd .
```

Important behavior:

- The first run creates a fresh OpenBrowser conversation and stores it in `.openbrowser_clawdbot_session.json`
- Later runs reuse that same conversation automatically
- Add `--new-session` when the task should start over from a clean browser conversation

## Useful commands

Check the saved conversation:

```bash
uv run openbrowser-clawdbot status --cwd .
```

Reset the saved conversation:

```bash
uv run openbrowser-clawdbot reset --cwd .
```

Get raw events as JSONL:

```bash
uv run openbrowser-clawdbot run "Summarize the visible page" --cwd . --jsonl
```

## How to use it well

- Keep prompts action-oriented and specific
- Reuse the same session for follow-up prompts like "open the second result", "extract salary", or "continue from where you stopped"
- Start a new session when switching to a different browsing task or website account

## Example follow-up flow

```bash
uv run openbrowser-clawdbot run "Open Indeed and search for machine learning engineer jobs in New York" --cwd .
uv run openbrowser-clawdbot run "Filter to remote-friendly roles and summarize the top 10" --cwd .
uv run openbrowser-clawdbot run "Save the results into jobs.md in the workspace" --cwd .
```
