# Draft: Visual-First Browser Interaction Refactor

**Created**: 2026-02-28
**Status**: Requirements Gathering

---

## User's Original Request

Transform OpenBrowser from **JavaScript-code-driven** to **visual-first** browser interaction:
- AI "sees" page with highlighted interactive elements
- AI operates by **element ID** (e.g., "click object 1"), not coordinates or selectors
- Operations should match real user behavior exactly
- No compatibility concerns (early project)

---

## Key Design Decisions (From User)

### New Action Types
| Type | Parameters | Purpose |
|------|------------|---------|
| `tab` | (existing) | Tab management |
| `highlight_elements` | `element_types`, `limit`, `offset` | Show highlighted elements with IDs |
| `keyboard_input` | `element_id`, `text` | Type into input field |
| `mouse_move` | `element_id` | Hover over element |
| `mouse_click` | `element_id` | Click element |
| `javascript_execute` | (existing, weakened) | Fallback for edge cases |
| ~~`view`~~ | (removed) | Replaced - all ops return screenshots |

### Key Design Principles
1. **All operations return screenshots** with optional element highlights
2. **Element IDs are visual** - displayed on screenshot overlay
3. **Smart element ranking** - prioritize by visibility, size, z-index
4. **Pagination support** - return elements in batches (e.g., 50 at a time)
5. **Real user behavior** - clicks/inputs match actual user actions

---

## Current Implementation Analysis

### What EXISTS (Reusable)

| Component | File | Status | Notes |
|-----------|------|--------|-------|
| Element extraction + bbox | `grounded-elements.ts` | **REUSE** | Has selector generation, bbox |
| Accessibility tree extraction | `accessibility.ts` | **REUSE** | Semantic elements + bounds |
| Screenshot capture (CDP) | `screenshot.ts` | **MODIFY** | Add overlay drawing |
| Dialog handling | `dialog.ts` | **KEEP** | Works for click+dialog scenarios |
| JS execution with dialog race | `javascript.ts` | **KEEP** | Can be used for element-based click |
| Debugger session management | `debugger-manager.ts` | **KEEP** | CDP lifecycle |
| Command routing | `background/index.ts` | **MODIFY** | Add new command handlers |
| Server command models | `models/commands.py` | **MODIFY** | Add new command types |
| OpenBrowserTool | `open_browser_tool.py` | **MODIFY** | Restructure action/observation |

### What to REMOVE/DEPRECATE

| Component | File | Reason |
|-----------|------|--------|
| Preset coordinate system (1280x720) | `computer.ts` | Replaced by element ID |
| `presetToActualCoords()` | `computer.ts` | No coordinate conversion needed |
| `performClick(x, y)` | `computer.ts` | Replaced by element-based click |
| `performMouseMove(x, y)` | `computer.ts` | Replaced by element-based hover |
| Mouse position tracking | `computer.ts` | Not needed for element-based |

---

## Technical Gaps (Need Building)

### 1. Element Highlighting System
**What's missing:**
- Drawing element bounding boxes on screenshots
- Numbered element ID labels (1, 2, 3...)
- Color coding by element type (clickable/scrollable/input/hoverable)
- Smart element ranking algorithm

**Implementation approach:**
- Use OffscreenCanvas (already available in screenshot.ts)
- Draw after screenshot capture, before return
- Store element ID → selector mapping for later click operations

### 2. Element Ranking Algorithm
**Proposed scoring:**
```
score = (area / maxArea) × 0.25
      + (viewportCenterDistance) × 0.25
      + (isInteractive) × 0.30
      + (zIndex / maxZIndex) × 0.20
```

**Element types to detect:**
- **Clickable**: button, a, [role="button"], input[type="submit"]
- **Input**: input, textarea, [contenteditable="true"]
- **Scrollable**: elements with overflow:scroll/auto and scrollable content
- **Hoverable**: elements with :hover CSS or mouse event handlers

### 3. Element ID Assignment & Tracking
**Two approaches:**

**Option A: Inject data attribute**
```javascript
// Inject data-ob-id into DOM
element.setAttribute('data-ob-id', '42');
// Later: click by finding element
document.querySelector('[data-ob-id="42"]').click();
```
- Pro: Stable reference
- Con: Modifies DOM, might trigger mutation observers

**Option B: Selector-based lookup**
```javascript
// Store selector + index mapping
const element = document.querySelectorAll(selector)[index];
```
- Pro: No DOM modification
- Con: Selector might become stale

**Recommended: Option A** - More reliable for dynamic pages

---

## Server-Side Changes

### New Command Models (`server/models/commands.py`)

```python
class HighlightElementsCommand(BaseCommand):
    type: Literal["highlight_elements"] = "highlight_elements"
    element_types: List[str] = Field(
        default=["clickable", "input", "scrollable", "hoverable"],
        description="Types of elements to highlight"
    )
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)

class ElementClickCommand(BaseCommand):
    type: Literal["element_click"] = "element_click"
    element_id: int = Field(description="Element ID from highlight")
    
class ElementHoverCommand(BaseCommand):
    type: Literal["element_hover"] = "element_hover"
    element_id: int = Field(description="Element ID from highlight")

class ElementInputCommand(BaseCommand):
    type: Literal["element_input"] = "element_input"
    element_id: int = Field(description="Element ID from highlight")
    text: str = Field(description="Text to input")
```

### OpenBrowserAction Restructure

```python
class OpenBrowserAction(Action):
    type: str = Field(description="Type: 'tab', 'highlight_elements', 'element_click', 'element_hover', 'element_input', 'javascript_execute'")
    
    # Tab operations (existing)
    action: Optional[str] = None
    url: Optional[str] = None
    tab_id: Optional[int] = None
    
    # Highlight operations (new)
    element_types: Optional[List[str]] = None
    limit: Optional[int] = 50
    offset: Optional[int] = 0
    
    # Element operations (new)
    element_id: Optional[int] = None
    text: Optional[str] = None
    
    # JavaScript (existing, weakened)
    script: Optional[str] = None
    
    # Dialog handling (existing)
    dialog_action: Optional[str] = None
    prompt_text: Optional[str] = None
```

---

## Extension-Side Changes

### New Command Handlers (`extension/src/background/index.ts`)

```typescript
case 'highlight_elements': {
  // 1. Get elements by type
  // 2. Rank elements
  // 3. Capture screenshot
  // 4. Draw overlays with element IDs
  // 5. Store element_id → selector mapping
  // 6. Return screenshot + element list
}

case 'element_click': {
  // 1. Look up selector by element_id
  // 2. Execute click via JS or CDP
  // 3. Handle potential dialog
  // 4. Return screenshot
}

case 'element_hover': {
  // 1. Look up selector by element_id
  // 2. Dispatch mouseMoved via CDP at element center
  // 3. Return screenshot
}

case 'element_input': {
  // 1. Look up selector by element_id
  // 2. Focus element
  // 3. Dispatch key events via CDP
  // 4. Return screenshot
}
```

---

## User Decisions (CONFIRMED)

| Question | Decision |
|----------|----------|
| mouse_move vs mouse_click | **Keep both separate** - explicit hover for tooltips, click for actions |
| Element ID persistence | **Auto-invalidate on change** - detect DOM mutations/nav, force refresh |
| Scroll action | **Yes - element_scroll** - dedicated action for scrollable containers |
| Test strategy | **TDD** - write tests first for each task |

---

## ~~Open Questions for User~~ (RESOLVED)

### 1. Element ID Persistence
- Should element IDs persist across page navigations?
- How to handle dynamic content (elements appearing/disappearing)?
- Invalidate all IDs on page change, or attempt to track?

### 2. Mouse Operations
- **Question from user**: "mouse_move and mouse_click might be redundant"
- **My assessment**: 
  - `mouse_move` (hover) is useful for triggering hover effects, tooltips
  - `mouse_click` is the primary interaction
  - Could combine into `mouse_click` with optional `hover_first` parameter?

### 3. Scrollable Element Handling
- Should scrollable elements have dedicated `element_scroll` action?
- Or treat scroll as a property of any element?
- How to identify scroll direction/amount?

### 4. Error Handling
- What happens when AI tries to click element_id that no longer exists?
- Auto-refresh highlights and tell AI to re-select?

---

## Implementation Phases (Tentative)

### Phase 1: Core Infrastructure
1. Add new command models
2. Implement element extraction + ranking
3. Implement screenshot overlay drawing
4. Store element_id → selector mapping

### Phase 2: Element Operations
1. Implement `element_click` with dialog handling
2. Implement `element_input` with CDP key events
3. Implement `element_hover` with CDP mouse moved

### Phase 3: Cleanup
1. Remove coordinate-based mouse operations
2. Remove preset coordinate system
3. Update tool description
4. Remove/deprecate `view` action

### Phase 4: Polish
1. Add pagination for large element sets
2. Add element type filtering
3. Optimize screenshot + overlay composition
4. Add error recovery for stale element IDs

---

## Files to Modify

| File | Changes |
|------|---------|
| `server/models/commands.py` | Add new command types |
| `server/agent/tools/open_browser_tool.py` | Restructure Action/Observation |
| `server/core/processor.py` | Add command handlers |
| `extension/src/background/index.ts` | Add command routing |
| `extension/src/commands/screenshot.ts` | Add overlay drawing |
| `extension/src/commands/grounded-elements.ts` | Add ranking, IDs |
| `extension/src/commands/computer.ts` | Remove/DEPRECATE |

---

## Research References

- **Magnitude** (3,966 stars): Vision-first AI browser agent
- **CDP Input.dispatchMouseEvent**: For realistic mouse simulation
- **Element visibility scoring**: Size × viewport × interactivity × z-index
- **Canvas overlay patterns**: OffscreenCanvas for service worker context
