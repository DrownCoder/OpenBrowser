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
1. highlight_elements(page=1) → Returns collision-free elements with IDs
2. screenshot → AI sees numbered overlays on elements (no overlap)
3. click_element(id="click-3") → Interact with specific element
4. highlight_elements(page=2) → Get next batch of non-colliding elements
```

### Collision-Aware Pagination (Single-Type Design)
Elements are paginated to ensure **no visual overlap** in each screenshot:
- **One element type per call** for stable, predictable pagination
- Each page returns a maximal set of non-colliding elements
- Collision detection includes label area (26px above element)
- AI calls `page=1, page=2, page=3...` to see all elements of that type
- No offset/limit - pages are determined by collision geometry

```
# Highlight clickable elements (default)
highlight_elements()                  → Page 1 of clickable elements
highlight_elements(page=2)             → Page 2 of clickable elements

# Highlight other types (one at a time)
highlight_elements(element_type="inputable")   → Input fields
highlight_elements(element_type="scrollable")  → Scrollable areas
highlight_elements(element_type="hoverable")   → Hoverable elements
```

### Element ID Format
Elements are identified by a 6-character hash string:
- Format: `[a-z0-9]{6}` (e.g., "a3f2b1", "9z8x7c")
- Algorithm: FNV-1a hash of CSS selector, encoded in base36
- Deterministic: Same element always gets same ID across page reloads
- Example IDs: "a3f2b1", "k9m4p2", "7x3n1q"
| `hover_element` | Hover by element ID | `{element_id: "9z8x7c"}` |
| `scroll_element` | Scroll by element ID | `{element_id: "m5k2p8", direction: "down"}` |
| `keyboard_input` | Type into element | `{element_id: "j4n7q1", text: "hello"}` |
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
