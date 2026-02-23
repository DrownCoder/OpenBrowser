# Implementation Notes

This document contains technical implementation details, design decisions, and historical notes for the Local Chrome Server project.

## Table of Contents

- [Screenshot Resize Cover Mode (February 2026)](#screenshot-resize-cover-mode-february-2026)
- [Frontend Responsive Layout Improvements (February 2026)](#frontend-responsive-layout-improvements-february-2026)
- [Isolation Improvements (February 2026)](#isolation-improvements-february-2026)
- [Tab Management and Screenshot Fixes (February 2026)](#tab-management-and-screenshot-fixes-february-2026)
- [Screenshot Isolation using CDP (March 2025)](#screenshot-isolation-using-cdp-march-2025)
- [Refresh Tab Functionality (February 2026)](#refresh-tab-functionality-february-2026)
- [Debugging Guide](#debugging-guide)

---

## Screenshot Resize Cover Mode (February 2026)

### Problem

Screenshots using "contain" mode resize created white borders when the original viewport aspect ratio differed from the preset 1280x720:

```
Original: 1440x900 (16:10)
→ Scale to 1280x720 (16:9) with contain mode
→ Result: 1152x720 centered, with 64px white borders on left/right
→ Problem: Lost image information, confusing for AI
```

### Solution: Cover Mode Resize

Changed `resizeImage()` from contain mode to cover mode:

1. **Cover mode scaling**: Use `Math.max(scaleX, scaleY)` instead of `Math.min()` to scale image to cover entire target
2. **Center crop**: Calculate crop offsets to center the image, cropping overflow
3. **Metadata tracking**: Record `cropOffsetX` and `cropOffsetY` in screenshot metadata

### Example

```
Original: 1440x900 (16:10)
→ Scale with cover mode: scale = max(1280/1440, 720/900) = 0.889
→ Scaled: 1280x800
→ Crop: 40px from top and bottom
→ Result: Perfect 1280x720, no white borders ✅
```

### Benefits

- **No white borders**: Full 1280x720 image area utilized
- **Better for AI**: No confusion from empty borders
- **Metadata preserved**: Crop offsets saved for potential coordinate mapping

### Files Modified

- `extension/src/commands/screenshot.ts`: Updated `resizeImage()` function
- Screenshot metadata now includes `cropOffsetX` and `cropOffsetY` fields

---

## Frontend Responsive Layout Improvements (February 2026)

### Problems

On smaller screens (< 1200px width), the frontend displayed incorrectly:

1. **ASCII art title too large**: OPENBROWSER ASCII art took up too much space
2. **Right panel hidden**: Live view panel pushed off screen or not visible
3. **No scrolling**: Vertical layout not scrollable

### Solution: Three-Tier Responsive Design

Added responsive breakpoints for different screen sizes:

1. **Large screens (>1200px)**: Default layout, ASCII art at 12px
2. **Medium screens (900-1200px)**: 
   - ASCII art scaled down to 10px
   - Side-by-side layout maintained
3. **Small screens (<900px)**:
   - ASCII art at 10px
   - Vertical stack layout (terminal on top, live view below)
   - Right panel min-width reduced from 350px to 280px
   - Added `overflow-y: auto` to container for scrolling
4. **Extra small screens (<600px)**:
   - ASCII art further reduced to 8px
   - Image viewer min-height adjusted to 200px

### Files Modified

- `frontend/index.html`: Added responsive CSS rules for ASCII title and layout

### Benefits

- **Small screen support**: Frontend usable on laptops and smaller displays
- **No horizontal scrolling**: Content fits within viewport width
- **Maintained readability**: ASCII art scales appropriately

---

## Isolation Improvements (February 2026)

### Problem

AI-managed tabs were interfering with user browsing:
1. AI operations (e.g., `reset_mouse`) activated managed tabs, stealing focus from user's active tab
2. When user switched back to their tab, AI commands could target the wrong tab (user's active tab)

### Solution: Background Automation Mode

Implemented background automation mode to prevent focus stealing:

1. **No tab activation**: Modified `activateTabForAutomation()` to prepare tabs without activating them
2. **Managed tab priority**: Updated `getCurrentTabId()` to prefer managed tabs over active tab
3. **Background tab creation**: Changed `initializeSession()`, `openManagedTab()`, and `openTab()` to create tabs as non-active (`active: false`)
4. **Visual mouse handling**: Visual mouse pointers remain in managed tabs but are hidden when user switches away

### Benefits

- AI operations run in background without disrupting user's browsing experience
- Commands reliably target managed tabs even when user switches tabs
- Tab group isolation is preserved while avoiding focus stealing

### Configuration

All changes are enabled by default. No configuration needed.

### Testing

Verify that `tabs init <url>` creates a tab in the background, and subsequent `reset_mouse` or `mouse_move` commands do not switch tabs.

---

## Tab Management and Screenshot Fixes (February 2026)

### Problems

1. **Screenshots captured user's active tab instead of managed AI tab**
2. **Tab tracking was inconsistent across commands**

### Root Causes

1. Server-side lacked current tab tracking - commands didn't specify which tab to target
2. TypeScript and Python command schemas were misaligned (missing fields)

### Solution: Unified Tab Management System

1. **BaseCommand with tab_id**: Added `tab_id` field to all commands in Python schema
2. **CommandProcessor tab tracking**: 
   - Maintains `_current_tab_id` state
   - Auto-fills `tab_id` when not specified
   - Updates current tab on `init`, `open`, `switch` actions
3. **Schema alignment**:
   - Added `managed_only` to `GetTabsCommand` (default: true)
4. **Prepared command flow**: All commands go through `_send_prepared_command()` which ensures proper `tab_id`

### Workflow

```
tabs init https://example.com  # Creates managed tab, sets as current
screenshot                      # Captures from current managed tab
javascript_execute             # Executes in current managed tab
tabs switch <tab_id>           # Changes current tab
screenshot                      # Now captures from new current tab
```

### Backward Compatibility

- Existing commands work without changes
- When no managed tabs exist, extension falls back to active tab
- `tab_id` field is optional in API calls

---

## Screenshot Isolation using CDP (March 2025)

### Problem

Screenshots captured user's visible tab instead of managed tab due to `chrome.tabs.captureVisibleTab` API limitation.

### Root Cause

The `captureVisibleTab` API captures the currently visible tab in the window, not the specified tab. This caused screenshots to show user's active tab instead of the managed AI tab.

### Solution: CDP-based Screenshot Capture

Implemented CDP-based screenshot capture with background tab support:

1. **CDP Screenshot Function**: Created `captureScreenshotWithCDP` function using Chrome DevTools Protocol (`Page.captureScreenshot`)
2. **Background Tab Support**: CDP can capture screenshots of tabs even when they're in the background (not visible)
3. **Viewport Accuracy**: Uses `Page.getLayoutMetrics` to get precise viewport dimensions
4. **Fallback Mechanism**: Falls back to legacy `captureVisibleTab` if CDP fails, with clear warning about potential tab mismatch
5. **Session Isolation**: Modified `getCurrentTabId()` to require managed tabs, preventing accidental control of user's active tab

### Technical Implementation

- Added imports for `CdpCommander` and `debuggerManager` in `screenshot.ts`
- CDP screenshot flow: attach debugger → enable Page domain → get layout metrics → capture screenshot → resize to preset coordinate system (1280×720)
- Preset coordinate system maintained for consistent mapping between screenshots and mouse positions
- Added metadata field `captureMethod` to distinguish between CDP and legacy captures

### Isolation Benefits

- Screenshots now reliably capture managed tabs even when user is browsing other tabs
- No visual disruption or tab switching during screenshot capture
- Managed tabs remain in background, preserving user browsing experience
- Clear error messages guide users to initialize sessions with `tabs init` when no managed tabs exist

### Testing

Verify that `tabs init <url>` followed by `screenshot` captures the managed tab even when user switches to another tab.

---

## Refresh Tab Functionality (February 2026)

### New Feature

Added `refresh` action to tab management commands.

### Implementation

- **Server**: Added `REFRESH` to `TabAction` enum
- **Extension**: Added `refreshTab` function using Chrome's `tabs.reload()` API
- **AI Tool**: Updated `open_browser_tool.py` to support `refresh` action
- **CLI**: Added `tabs refresh <tab_id>` command

### Usage

```bash
# Refresh a specific managed tab (background, no user disruption)
local-chrome-server execute tab refresh --tab_id 123
# Or via CLI
local-chrome-server tabs refresh 123

# AI Agent usage
{"type": "tab", "parameters": {"action": "refresh", "tab_id": 123}}
```

### Behavior

- Refreshes tab without activating it (maintains user browsing isolation)
- Requires `tab_id` parameter to specify which tab to refresh
- Works with managed tabs only (ensures tab is in OpenBrowser tab group)
- Updates tab activity status for tracking purposes

---

## Debugging Guide

### Common Issues and Solutions

#### 1. Extension Shows "Disconnected"

**Cause**: WebSocket connection failure

**Check**:
- Server is running: `local-chrome-server serve`
- WebSocket server started: Check logs for "WebSocket server started"

#### 2. WebSocket 403 Errors

**Cause**: WebSocket handshake failure or origin rejection

**Solution**:
- Ensure WebSocket server accepts all origins (configured in `server/websocket/manager.py`)
- Verify extension connects to correct URL: `ws://127.0.0.1:8766`

#### 3. Commands Not Executing

**Cause**: Extension not connected or CDP attachment failed

**Debug Steps**:
1. Check extension background page console
2. Verify WebSocket connection
3. Test simple command: `chrome-cli tabs list`

#### 4. SSE stream disconnects

**Solution**:
- Increase timeout in agent configuration
- Check for errors in server logs

#### 5. ObservationEvent missing in SSE stream

**Cause**: Tool execution blocking due to event loop competition between WebSocket and thread pools

**Symptoms**: SSE shows `ActionEvent` but no `ObservationEvent`, stream times out after 30s

**Debug**:
- Check server logs for "DEBUG: OpenBrowserTool.__call__" and "DEBUG: _execute_action"

**Workaround**: Use synchronous HTTP API calls instead of WebSocket for tool execution

**Check**: Ensure `QueueVisualizer.on_event()` is being called for all event types

### Debugging Best Practices

1. **Enable Debug Logging**:
   ```bash
   local-chrome-server serve --log-level DEBUG
   ```

2. **Check Extension Background Page**:
   - Open `chrome://extensions/`
   - Find "OpenBrowser"
   - Click "Details" → "Inspect views: background page"

3. **Verify Tool Registration** (for AI agent integration):
   - Ensure tool description is clear and complete
   - Check parameter schemas are correctly defined
   - Verify tool is set correctly in agent configuration

4. **Test Connectivity**:
   ```bash
   chrome-cli status
   curl http://127.0.0.1:8765/health
   ```

---

## Related Documentation

- [Architecture Overview](../architecture/overview.md) - System design and component architecture
- [Python Server Modules](../architecture/python-modules.md) - Detailed server module documentation
- [Chrome Extension Modules](../extension/modules.md) - Detailed extension module documentation
- [Troubleshooting Guide](../troubleshooting/common-issues.md) - Common issues and solutions
