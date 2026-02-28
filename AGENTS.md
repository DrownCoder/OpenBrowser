# OpenBrowser Project Knowledge Base

**Generated:** 2026-02-27
**Commit:** 8836b0b (main)
**Stack:** Python 3.12+ (FastAPI) + TypeScript (Chrome Extension MV3)

## OVERVIEW

Visual AI assistant powered by Qwen3.5-Plus for browser automation with visual feedback. Single-model closed loop: code generation → visual verification → browser control → terminal execution.

## STRUCTURE

```
OpenBrowser/
├── server/           # FastAPI backend + agent logic + WebSocket
├── extension/        # Chrome extension (MV3) for browser control
├── cli/              # Command-line tool (chrome-cli)
├── frontend/         # Static web UI (HTML)
└── reference/        # External SDK references (read-only)
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Agent orchestration | `server/agent/manager.py` | Conversation lifecycle, LLM config |
| Browser commands | `server/core/processor.py` | Command routing, multi-session |
| Dialog handling | `server/models/commands.py` | HandleDialogCommand, DialogAction |
| REST API routes | `server/api/routes/` | FastAPI endpoints |
| WebSocket handling | `server/websocket/manager.py` | Extension communication |
| Command models | `server/models/commands.py` | Pydantic command/response types |
| Extension entry | `extension/src/background/index.ts` | Command handler, dialog processing |
| Dialog manager | `extension/src/commands/dialog.ts` | CDP dialog events, cascading |
| JavaScript execution | `extension/src/commands/javascript.ts` | CDP Runtime.evaluate, dialog race |
| Screenshot capture | `extension/src/commands/screenshot.ts` | CDP Page.captureScreenshot |
| Tab management | `extension/src/commands/tab-manager.ts` | Session isolation, tab groups |
| CLI implementation | `cli/main.py` | Interactive mode, shortcuts |
## ARCHITECTURE

```
┌─────────────────────────────────────────┐
│     Qwen3.5-Plus (Multimodal LLM)       │
└────────────────────┬────────────────────┘
                     │
┌────────────────────▼────────────────────┐
│   OpenBrowser Agent Server (FastAPI)    │
│   - REST API (port 8765)                │
│   - WebSocket (port 8766)               │
│   - OpenHands SDK integration           │
│   - handle_dialog action                │
└────────────────────┬────────────────────┘
                     │
┌────────────────────▼────────────────────┐
│   Chrome Extension (CDP)                │
│   - JavaScript execution (with race)    │
│   - Dialog detection & handling         │
│   - Screenshots (1280x720)              │
│   - Tab management with groups          │
└─────────────────────────────────────────┘
```

## DIALOG HANDLING

When JavaScript triggers a dialog (alert/confirm/prompt), the browser pauses.
OpenBrowser uses Promise.race to detect dialogs gracefully.

### Flow
```
1. javascript_execute runs
2. Promise.race([
     jsExecution,    // Runtime.evaluate
     dialogEvent,    // Page.javascriptDialogOpening
     timeout         // User timeout
   ])
3. If dialog opens:
   - Alert → Auto-accept
   - Confirm/Prompt → Return dialog info
4. AI calls handle_dialog(accept/dismiss)
5. Extension handles, checks cascade
```

### Dialog Types
| Type | Needs Decision | AI Action |
|------|----------------|----------|
| alert | No | Auto-accepted |
| confirm | Yes | handle_dialog(accept/dismiss) |
| prompt | Yes | handle_dialog(accept, text) |
| beforeunload | Yes | handle_dialog(accept/dismiss) |

### Cascading Dialogs
Dialog → Dialog → Dialog chain supported. After handling one dialog,
the system checks for new dialogs within 150ms.

## CONVENTIONS

### Python (server/)
- **Line length:** 88 (black/ruff)
- **Target:** Python 3.12
- **Strict typing:** `disallow_untyped_defs = true` in mypy
- **Imports:** isort via ruff

### TypeScript (extension/)
- **Target:** ES2022
- **Module:** ESNext with bundler resolution
- **Strict mode:** enabled
- **Path alias:** `@/*` → `src/*`
- **Build:** Vite with multi-entry (background, content, workers)

## ANTI-PATTERNS (THIS PROJECT)

- **NEVER use pixel-based mouse/keyboard simulation** - All operations via JavaScript execution
- **NEVER skip conversation_id** - Required for multi-session isolation
- **NEVER return DOM nodes from JavaScript** - Must be JSON-serializable
- **NEVER use `.click()` for React/Vue** - Dispatch full event sequence instead
- **NEVER suppress type errors** - `as any`, `@ts-ignore` forbidden
- **NEVER ignore dialog_opened** - AI must handle dialogs before continuing
## VISUAL INTERACTION WORKFLOW

OpenBrowser uses a visual-first approach where the AI sees elements before interacting:

### Workflow
```
1. highlight_elements → Returns list of interactive elements with IDs
2. screenshot → AI sees numbered overlays on elements
3. click_element(id="click-3") → Interact with specific element
```

### Element ID Format
Elements are identified by type-prefix + number:
- `click-N` - Clickable elements (buttons, links)
- `scroll-N` - Scrollable elements
- `input-N` - Input fields
- `hover-N` - Hoverable elements

### Commands
| Command | Purpose | Example |
|---------|---------|--------|
| `highlight_elements` | Highlight & list interactive elements | `{element_types: ["clickable"], limit: 10}` |
| `click_element` | Click by element ID | `{element_id: "click-3"}` |
| `hover_element` | Hover by element ID | `{element_id: "hover-1"}` |
| `scroll_element` | Scroll by element ID | `{element_id: "scroll-2", direction: "down"}` |
| `keyboard_input` | Type into element | `{element_id: "input-1", text: "hello"}` |

## UNIQUE PATTERNS

### JavaScript-First Automation (Fallback)
For complex interactions not covered by visual commands:
```javascript
// Click by visible text (universal pattern)
(() => {
    const text = 'YOUR_TEXT';
    const leaf = Array.from(document.querySelectorAll('*'))
        .find(el => el.children.length === 0 && el.textContent.includes(text));
    if (!leaf) return 'not found';
    const target = leaf.closest('a, button, [role="button"]') || leaf;
    target.click();
    return 'clicked: ' + target.tagName;
})()
```

### Multi-Session Tab Isolation
- `tab init <url>` creates managed session with tab group
- `conversation_id` ties all commands to session
- Tab groups provide visual isolation ("OpenBrowser" group)

### 2-Strike Rule
If operation fails twice:
1. Try full event sequence (pointerdown → mousedown → click)
2. Inspect DOM structure
3. Consider direct URL navigation

## COMMANDS

```bash
# Start server
uv run local-chrome-server serve

# Build extension
cd extension && npm run build

# CLI interactive mode
uv run chrome-cli interactive

# CLI tab management
uv run chrome-cli tabs init https://example.com
uv run chrome-cli tabs list
uv run chrome-cli javascript execute "document.title"
```

## NOTES

- **Git dependencies:** `openhands-sdk` and `openhands-tools` from git subdirectories
- **CDP required:** Extension uses Chrome DevTools Protocol for screenshots/JS execution
- **Preset coordinates:** Screenshots at 1280x720, mouse in 0-1280/0-720 coordinate system
- **Config storage:** LLM config in `~/.openbrowser/llm_config.json`
