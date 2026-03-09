---
name: open-browser
description: This skill should be used when the user asks to "automate browser", "control Chrome", "browse website with AI", "use OpenBrowser", "run browser automation", or mentions web scraping, form filling, UI testing, or any task requiring visual browser interaction. Delegates browser automation tasks to OpenBrowser Agent.
---

# OpenBrowser Skill

Delegate browser automation to OpenBrowser Agent for visual browser control.

## Quick Start

### 1. Check Prerequisites

```bash
python3 scripts/check_status.py
```

Expected output:
```
✅ Server: Running
✅ Extension: Connected (1 connection(s))
✅ LLM Config: dashscope/qwen3.5-plus
🎉 OpenBrowser is ready to use!
```

If not ready, see [Setup](#setup) below.

### 2. Submit Task

Use the task submission script:

```bash
# Submit task with real-time output
python3 scripts/send_task.py "Go to example.com and extract the title"

# For long-running tasks, run in background
python3 scripts/send_task.py "Scrape news from HN" --background --output task.log

# Check server status only
python3 scripts/send_task.py --check
```

### 3. Monitor Progress

For background tasks

```bash
# Monitor task output
tail -f task.log

# Check conversation status via API
curl http://localhost:8765/agent/conversations/{conversation_id}
```

## Setup

If OpenBrowser is not ready, follow these steps

### Step 1: Install and Start Server

```bash
cd /path/to/OpenBrowser
uv sync
uv run local-chrome-server serve
```

Server runs at http://127.0.0.1:8765

**Important:** Do NOT start the server yet. Use scripts/check_status.py first.

### Step 2: Configure LLM API Key (REQUIRED)

**Ask the user to configure the LLM API key:**

1. Go to https://dashscope.aliyun.com/ to get a DashScope API key
2. Open http://localhost:8765 in Chrome
3. Click the ⚙️ Settings button in the status bar
4. Fill in:
   - Model: `dashscope/qwen3.5-plus`
   - Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`
   - API Key: `YOUR_API_KEY`
5. Click Save

Verify configuration:
```bash
python3 scripts/check_status.py
# Should show: ✅ LLM Config: dashscope/qwen3.5-plus
```

**Note:** The LLM API key is stored in `~/.openbrowser/llm_config.json`.

### Step 3: Install Chrome Extension (REQUIRED)

**Ask the user to install the Chrome extension**

1. Build the extension:
   ```bash
   cd /path/to/OpenBrowser/extension
   npm install
   npm run build
   ```

2. Load in Chrome:
   - Open `chrome://extensions/`
   - Enable **Developer mode** (top-right toggle)
   - Click **Load unpacked**
   - Select the `extension/dist` folder
3. Verify extension appears and list

Verify extension is connected:
```bash
python3 scripts/check_status.py
# Should show: ✅ Extension: Connected
```

## Important Notes

- **Long-running tasks can take minutes** - Always run in background
- **Extension must stay loaded in Chrome** - Browser automation won't work if extension is disabled
- **Visual-based automation** - OpenBrowser sees pages via screenshots
- **Uses your browser session** - Leverages existing logins/cookies

## Troubleshooting

### Extension Not Connected (`websocket_connected: false`)

1. Verify extension is loaded in `chrome://extensions/`
2. Click the refresh icon on the extension
3. Check Chrome console for errors (F12 → Console tab)
4. Restart server

### API Key Not Configured (`has_api_key: false`)

1. Configure via web UI at http://localhost:8765
2. Check config file: `cat ~/.openbrowser/llm_config.json`

### Task Not Progressing

1. Check conversation status API
2. View browser window - may be waiting for dialogs
3. Check for dialog prompts (confirm/alert)
4. Restart with new conversation

## Additional Resources

### Reference Documentation
- `references/api_reference.md` - Complete REST API documentation

### Utility Scripts
- `scripts/check_status.py` - Verify OpenBrowser readiness
- `scripts/send_task.py` - Submit automation tasks

### Architecture
```
AI Assistant → REST API → OpenBrowser Agent → Chrome Extension
                                     ↓
                              Qwen3.5-Plus (Visual Understanding)
```

## Task Examples


