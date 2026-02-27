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
| Command models | `models/commands.py` | `Command`, `parse_command()` |
| Browser tool | `agent/tools/open_browser_tool.py` | `OpenBrowserTool` |

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

## NOTES

- WebSocket runs on port 8766, HTTP on 8765
- `conversation_id` links all commands to session context
- Agent uses OpenHands SDK with custom `OpenBrowserTool`
## ANTI-PATTERNS

- **NEVER skip conversation_id** - Required for multi-session isolation
- **NEVER suppress type errors** - `disallow_untyped_defs = true` enforced
- **NEVER access WebSocket directly** - Use `ws_manager` singleton
- **NEVER hardcode ports** - Use `config.port` / `config.websocket_port`
