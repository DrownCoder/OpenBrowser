---
name: openbrowser-clawdbot
description: Use this skill when the user wants Clawdbot/OpenClaw to control the local OpenBrowser panel through natural-language conversation. Reuses a persistent OpenBrowser conversation so multi-turn browser tasks can continue in the same session.
---

# OpenBrowser Clawdbot Bridge

Use this skill when Clawdbot/OpenClaw should drive the existing OpenBrowser panel instead of calling the browser directly.

This skill is self-contained. It does not import Python modules from the OpenBrowser repo, so it can be installed into OpenClaw as an independent skill package.

## What this skill does

- Reuses the existing OpenBrowser agent, panel, and Chrome extension
- Persists one OpenBrowser `conversation_id` per workspace
- Lets Clawdbot continue a browser task across multiple chat turns
- Runs OpenBrowser in the background and returns the final assistant answer as plain text by default

## Prerequisites

Run this before the first browser task:

```bash
python3 scripts/run_openbrowser_bridge.py check --cwd .
```

The bridge is ready only when:

- `server_healthy` is `true`
- `extension_connected` is `true`
- `llm_has_api_key` is `true`

If not ready, start and configure OpenBrowser first.

## Main command

Send a prompt into the existing OpenBrowser panel session:

```bash
python3 scripts/run_openbrowser_bridge.py run "Open LinkedIn Jobs and search for staff backend engineer roles in San Francisco" --cwd .
```

Important behavior:

- The first run creates a fresh OpenBrowser conversation and stores it in `.openbrowser_clawdbot_session.json`
- Later runs reuse that same conversation automatically
- Add `--new-session` when the task should start over from a clean browser conversation
- By default, `run` waits for the task to finish and prints only the final assistant text answer
- Use `--stream` only when debugging and you want the full step-by-step event stream

## Useful commands

Check the saved conversation:

```bash
python3 scripts/run_openbrowser_bridge.py status --cwd .
```

Reset the saved conversation:

```bash
python3 scripts/run_openbrowser_bridge.py reset --cwd .
```

Get raw events as JSONL:

```bash
python3 scripts/run_openbrowser_bridge.py run "Summarize the visible page" --cwd . --stream --jsonl
```

## How to use it well

- Keep prompts action-oriented and specific
- Reuse the same session for follow-up prompts like "open the second result", "extract salary", or "continue from where you stopped"
- Start a new session when switching to a different browsing task or website account
- In chat products like DingTalk, prefer the default `run` behavior so the user sees only the final text result

## Recommended OpenClaw behavior

When this skill is selected:

1. Convert the user's request into one `python3 scripts/run_openbrowser_bridge.py run "...task..." --cwd .` command
2. Wait for the command to finish in the background
3. Return the command stdout to the user as the final text answer
4. Do not use `--stream` unless the user explicitly asks for step-by-step debugging output

## Example follow-up flow

```bash
python3 scripts/run_openbrowser_bridge.py run "Open Indeed and search for machine learning engineer jobs in New York" --cwd .
python3 scripts/run_openbrowser_bridge.py run "Filter to remote-friendly roles and summarize the top 10" --cwd .
python3 scripts/run_openbrowser_bridge.py run "Save the results into jobs.md in the workspace" --cwd .
```
