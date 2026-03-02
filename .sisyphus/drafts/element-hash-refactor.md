# Draft: Element Hash ID & Tab-Scoped Cache Refactor

## Requirements (confirmed)

### 1. Element ID: Sequential → Hash-based (NO PREFIX)
- **Current**: `option-n` or `{type}-{hash}` format (e.g., `click-1`, `click-a3f2b1`)
- **Problem**: Not unique after page flip/tab switch
- **Target**: Pure hash (max 6 chars, NO type prefix)
  - Example: `a3f2b1` instead of `click-1`
  - Collision handling: Add salt and rehash if collision with existing non-expired element

### 2. Cache Structure: Global → Tab-Scoped
- **Current**: `Map<conversationId, { elements: [], timestamp }>`
- **Target**: `map<compositeKey, { element, timestamp }>` where compositeKey = `${tabId}:${elementHash}`
- **Write**: During `highlight_elements`
- **Read**: During `click_element`, `hover_element`, `keyboard_input`, `scroll_element`
- **TTL**: 2 minutes (unchanged)

### 3. Screenshot Return: Extend to All Operations
- **Current**: Only `highlight_elements` and element operations
- **Target**: ALL tab operations AND JavaScript operations also return screenshot
- **Note**: Screenshot should NOT have highlights for these operations

## Technical Decisions

### Hash Algorithm
- **Choice**: FNV-1a (already implemented in `hash-utils.ts`)
- **Output**: 6-character base36 string
- **Collision resolution**: Increment salt until unique hash found

### CSS Path Source
- **Source**: `element.selector` property from InteractiveElement

### Cache Key Format
```typescript
// Current:
Map<conversationId, CacheEntry>

// Target:
Map<string, CacheEntry>  // key = `${tabId}:${elementHash}`

interface CacheEntry {
  element: InteractiveElement;
  timestamp: number;
}
```

### Tab ID in Element Operations
- **Operations requiring tab_id**: `click_element`, `hover_element`, `keyboard_input`, `scroll_element`
- **If tab_id missing**: Return error

## Research Findings

### Existing Code (hash-utils.ts)
- Already has `generateShortHash()`, `generateUniqueHash()`, `generateElementId()`
- Currently generates IDs with type prefix: `${type}-${hash}`
- **Need to modify**: Remove type prefix from `generateElementId()`

### Current Element Cache (element-cache.ts)
- Uses `Map<conversationId, CacheEntry>` where CacheEntry = `{ elements: [], timestamp }`
- Methods: `storeElements()`, `getElements()`, `getElementById()`
- **Need to change to tab-scoped key structure

### Element Actions (element-actions.ts)
- All 4 operations call `elementCache.getElementById(conversationId, elementId)`
- Need to change to: `elementCache.getElementById(conversationId, elementId, tabId)`

## Files to Modify

### Extension (TypeScript)
1. `extension/src/commands/hash-utils.ts`
   - Remove type prefix from `generateElementId()`
   - Keep `generateShortHash()` and `generateUniqueHash()` unchanged

2. `extension/src/commands/element-cache.ts`
   - Change key from conversationId to compositeKey (`tabId:elementHash`)
   - Add tabId parameter to store/get methods
   - Update cleanup logic for new key format

3. `extension/src/commands/element-actions.ts`
   - Add tabId parameter to all 4 operations
   - Pass tabId to cache lookup

4. `extension/src/background/index.ts`
   - `highlight_elements`: Store elements with tab_id association
   - `click_element/hover_element/scroll_element/keyboard_input`: Validate tab_id
   - Tab operations + JavaScript: Add screenshot capture

5. `extension/src/types.ts`
   - Update `InteractiveElement.id` comment

### Server (Python)
1. `server/models/commands.py`
   - Add `tab_id` field to `ClickElementCommand`, `HoverElementCommand`, `ScrollElementCommand`, `KeyboardInputCommand`

2. `server/agent/tools/open_browser_tool.py`
   - Add `tab_id` to `OpenBrowserAction` fields
   - Pass `tab_id` to element command construction
   - Extract screenshots from tab/javascript operations
   - Update tool documentation

## Open Questions (NEED USER INPUT)

