# Extension Module (Chrome MV3)

**Stack:** TypeScript 5.8+ | Vite | Chrome Extension MV3 | CDP

## OVERVIEW

Chrome extension providing browser control via Chrome DevTools Protocol. Handles JavaScript execution, screenshot capture, and tab management with session isolation via tab groups.

## COMPLEXITY HOTSPOTS (>500 lines)

| File | Lines | Purpose |
|------|-------|---------|
| `src/commands/tab-manager.ts` | 1010 | Tab lifecycle, multi-session, tab groups |
| `src/commands/computer.ts` | 817 | Computer/browser automation actions |
| `src/background/index.ts` | 746 | Command queue, CDP flow orchestration |
| `src/commands/screenshot.ts` | 605 | CDP capture, image processing pipeline |
| `src/workers/worker-manager.ts` | 635 | Web worker lifecycle, image resizing |
| `src/helpers/browser-helpers.ts` | 542 | DOM utilities, wait helpers |

## WHERE TO LOOK

| Task | File | Key Exports |
|------|------|-------------|
| Background entry | `src/background/index.ts` | `handleCommand()`, `CommandQueueManager` |
| Tab management | `src/commands/tab-manager.ts` | `tabManager`, `TabSessionManager` |
| Computer actions | `src/commands/computer.ts` | Coordinate translation, CDP actions |
| JavaScript exec | `src/commands/javascript.ts` | `executeJavaScript()` |
| Screenshot | `src/commands/screenshot.ts` | `captureScreenshot()` (CDP, not captureVisibleTab) |
| CDP commands | `src/commands/cdp-commander.ts` | `CDPCommander` |
| Debugger | `src/commands/debugger-manager.ts` | `debuggerSessionManager` |
| Types | `src/types.ts` | `Command`, `CommandResponse` |
| WebSocket client | `src/websocket/client.ts` | `wsClient` |
| Worker manager | `src/workers/worker-manager.ts` | Image processing fallback |

## STRUCTURE

```
extension/
├── src/
│   ├── background/      # Service worker entry (746 lines)
│   ├── commands/        # Browser command handlers (6 files)
│   ├── content/         # Content script (visual feedback)
│   ├── helpers/         # Browser utilities (542 lines)
│   ├── websocket/       # Server communication
│   ├── workers/         # Web workers (image processing)
│   └── types.ts         # TypeScript interfaces
├── manifest.json        # MV3 manifest
├── vite.config.ts       # Build config (multi-entry)
└── dist/                # Built extension
```

## BUILD

```bash
npm install
npm run build        # Production
npm run dev          # Watch mode
npm run typecheck    # Type check only
```

## CONVENTIONS

- **Strict mode:** TypeScript strict enabled
- **Path alias:** `@/*` maps to `src/*`
- **ES modules:** Native ES modules, no bundler runtime
- **CDP via debugger API:** Uses `chrome.debugger` for CDP commands

## COMMAND HANDLING

1. WebSocket receives command from server
2. `CommandQueueManager` enqueues with cooldown
3. `handleCommand()` routes to appropriate handler
4. Response sent back via WebSocket

## ANTI-PATTERNS

- **NEVER return DOM nodes** - Serialize to JSON first
- **NEVER skip conversation_id** - Required for isolation
- **NEVER use `.click()` directly on React** - Use full event sequence
- **NEVER skip tab management** - Always `ensureTabManaged()` before CDP
- **NEVER use captureVisibleTab** - DEPRECATED, use CDP screenshot
- Debugger sessions auto-detach on tab close

## KEY CLASSES

| Class | Location | Role |
|-------|----------|------|
| `CommandQueueManager` | background/index.ts:35 | Serializes command execution |
| `WatchdogTimer` | background/index.ts:254 | Detects main thread freezes |
| `TabManager` | commands/tab-manager.ts | Session-to-tab mapping |
| `DebuggerSessionManager` | commands/debugger-manager.ts | CDP session lifecycle |

## UNIQUE PATTERNS

### Click by Visible Text
```javascript
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

### 2-Strike Rule
If operation fails twice:
1. Try full event sequence (pointerdown → mousedown → click)
2. Inspect DOM structure
3. Consider direct URL navigation
