# Server Module (FastAPI Backend)

**Stack:** Python 3.12+ | FastAPI | Pydantic | WebSocket | SQLite

## OVERVIEW

FastAPI backend handling REST API, WebSocket communication with Chrome extension, and AI agent orchestration via OpenHands SDK. Multi-session isolation with SQLite persistence.

## WHERE TO LOOK

| Task | File | Key Symbols |
|------|------|-------------|
| Server entry | `main.py` | `cli()`, `serve()` |
| FastAPI app | `api/main.py` | `app`, lifespan, routers |
| Agent manager | `agent/manager.py` | `OpenBrowserAgentManager` |
| Command processor | `core/processor.py` | `CommandProcessor`, `_execute_*` |
| Session state | `core/session_manager.py` | `SessionManager`, SQLite |
| WebSocket | `websocket/manager.py` | `ws_manager`, `send_command()` |
| LLM config | `core/llm_config.py` | `llm_config_manager` |
| Command models | `models/commands.py` | `Command`, `HandleDialogCommand`, `DialogAction` |
| Browser tool | `agent/tools/open_browser_tool.py` | `OpenBrowserTool`, `handle_dialog` |
## STRUCTURE

```
server/
├── main.py              # CLI entry (serve, check, execute)
├── api/
│   ├── main.py          # FastAPI app + lifespan
│   ├── sse.py           # SSE event streaming
│   └── routes/          # REST endpoints (health, commands, agent, config)
├── agent/
│   ├── manager.py       # OpenBrowserAgentManager singleton
│   ├── conversation.py  # ConversationState, message handling
│   └── tools/           # OpenHands tool integrations
├── core/
│   ├── processor.py     # Command routing, per-conversation tab tracking
│   ├── session_manager.py  # SQLite persistence (SessionMetadata)
│   ├── config.py        # Server config (ports, host)
│   └── llm_config.py    # LLM API settings storage
├── websocket/
│   └── manager.py       # Extension communication, command_id futures
└── models/
    └── commands.py      # Pydantic command types (MouseMove, Tab, etc.)
```

## KEY CLASSES

| Class | Location | Role |
|-------|----------|------|
| `OpenBrowserAgentManager` | `agent/manager.py` | Singleton; creates/manages conversations, LLM init, tool provisioning |
| `CommandProcessor` | `core/processor.py` | Routes commands to extension; tracks `current_tab_id` per conversation |
| `SessionManager` | `core/session_manager.py` | SQLite-backed session CRUD, history, events |
| `WebSocketManager` | `websocket/manager.py` | Extension connections, command/response correlation via futures |

## CONVENTIONS

- **Strict typing:** All functions must have type hints
- **Async:** All I/O operations are async
- **Singletons:** Global instances (`command_processor`, `ws_manager`, `agent_manager`)
- **Conversation ID:** Required for all browser commands (multi-session isolation)

## COMMAND TYPES

| Type | Model | Handler |
|------|-------|---------|
| `javascript_execute` | `JavascriptExecuteCommand` | Extension CDP |
| `screenshot` | `ScreenshotCommand` | Extension CDP |
| `tab` | `TabCommand` | Extension tab API |
| `get_tabs` | `GetTabsCommand` | Extension tab API |
| `highlight_single_element` | `HighlightSingleElementCommand` | Extension 2PC flow |
| `get_element_html` | `GetElementHtmlCommand` | Extension element cache |
| `keyboard_input` | `KeyboardInputCommand` | Extension element actions |
| `scroll_element` | `ScrollElementCommand` | Extension element actions |
| `hover_element` | `HoverElementCommand` | Extension element actions |
| `click_element` | `ClickElementCommand` | Extension element actions |
| `highlight_elements` | `HighlightElementsCommand` | Extension element detection |
| `highlight_single_element` | `HighlightSingleElementCommand` | Extension 2PC flow |
| `get_element_html` | `GetElementHtmlCommand` | Extension element cache |
| `keyboard_input` | `KeyboardInputCommand` | Extension element actions |
| `scroll_element` | `ScrollElementCommand` | Extension element actions |
| `hover_element` | `HoverElementCommand` | Extension element actions |
| `click_element` | `ClickElementCommand` | Extension element actions |
| `highlight_elements` | `HighlightElementsCommand` | Extension element detection |
| `handle_dialog` | `HandleDialogCommand` | Extension CDP |
| `get_accessibility_tree` | `GetAccessibilityTreeCommand` | Extension CDP |

## DIALOG HANDLING

When JavaScript triggers a dialog (alert/confirm/prompt), the browser pauses.
OpenBrowser detects dialogs and handles them gracefully.

### Key Components
| Component | File | Role |
|-----------|------|------|
| `HandleDialogCommand` | models/commands.py | `action` (accept/dismiss), `prompt_text` |
| `OpenBrowserAction` | tools/open_browser_tool.py | `dialog_action`, `prompt_text` fields |
| `OpenBrowserObservation` | tools/open_browser_tool.py | `dialog_opened`, `dialog` fields |
| `CommandProcessor` | core/processor.py | Routes handle_dialog to extension |

### Dialog Types
| Type | Needs Decision | AI Action |
|------|----------------|----------|
| alert | No | Auto-accepted |
| confirm | Yes | Must call handle_dialog |
| prompt | Yes | Must call handle_dialog with text |
| beforeunload | Yes | Must call handle_dialog |

### Flow
1. `javascript_execute` triggers dialog
2. Extension returns `dialog_opened: true` with dialog info
3. AI sees "Dialog Opened" in observation
4. AI calls `handle_dialog` with `accept` or `dismiss`
5. Extension handles, checks for cascade, returns result

### Cascading Dialogs
After handling one dialog, another may open (e.g., confirm → alert).
The extension:
- Auto-accepts alerts
- Returns info for new confirm/prompt


## VISUAL INTERACTION COMMANDS

OpenBrowser uses a visual-first approach where elements are highlighted with numbered overlays before interaction.

### Key Commands
| Command | Purpose | Parameters |
|---------|---------|-----------|
| `highlight_elements` | Detect and highlight interactive elements | `element_type?: string`, `page?: number` |
| `click_element` | Click a highlighted element by ID | `element_id: string`, `tab_id: number` |
| `hover_element` | Hover over a highlighted element | `element_id: string`, `tab_id: number` |
| `scroll_element` | Scroll an element or the page | `element_id?: string`, `direction: string`, `tab_id: number` |
| `keyboard_input` | Type text into an element | `element_id: string`, `text: string`, `tab_id: number` |
| `get_element_html` | Get HTML of a cached element | `element_id: string`, `tab_id?: number` |
| `highlight_single_element` | Highlight single element for 2PC | `element_id: string`, `tab_id?: number` |

### Element Types
- `clickable` - Buttons, links, clickable elements
- `scrollable` - Scrollable containers
- `inputable` - Input fields, textareas
- `hoverable` - Hoverable elements

### tab_id Auto-Resolution
All visual interaction commands require `tab_id` in Python models, However, the TypeScript extension
can auto-resolve `tab_id` from the conversation context if not provided explicitly. This allows for cleaner
API usage in most cases where the active tab is implied.

For cross-reference, see root AGENTS.md "VISUAL INTERACTION WORKFLOW" section for complete workflow details.


## ACCESSIBILITY CONTEXT

The system provides a list of accessible interactive elements to help the AI agent
understand page structure and select elements.

### How It Works
1. After each `javascript_execute`, `tab init/open/switch`, the system fetches the accessibility tree
2. Returns list of interactive elements with selectors in `a11y_elements` field

### Key Components
| Component | File | Role |
|-----------|------|------|
| `GetAccessibilityTreeCommand` | models/commands.py | `max_elements` parameter |
| `a11y_elements` | tools/open_browser_tool.py | Observation field with elements list |
| `_get_a11y_elements_for_conversation()` | core/processor.py | Fetch accessibility tree |

### Elements Format
```python
[
    {"role": "button", "name": "Submit", "selector": "#submit-btn", "index": 0},
    {"role": "textbox", "name": "Email", "selector": "[name='email']", "index": 0},
    ...
]
```

## NOTES

- WebSocket runs on port 8766, HTTP on 8765
- `conversation_id` links all commands to session context
- Agent uses OpenHands SDK with custom `OpenBrowserTool`
- Dialogs block screenshot/JS until handled

## ANTI-PATTERNS

- **NEVER skip conversation_id** - Required for multi-session isolation
- **NEVER suppress type errors** - `disallow_untyped_defs = true` enforced
- **NEVER access WebSocket directly** - Use `ws_manager` singleton
- **NEVER hardcode ports** - Use `config.port` / `config.websocket_port`
- **NEVER ignore dialog_opened** - AI must handle dialogs before continuing
