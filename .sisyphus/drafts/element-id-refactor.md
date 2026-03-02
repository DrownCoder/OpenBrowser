# Draft: Element ID & Cache Refactor

## Requirements (confirmed)

### 1. Element ID Generation Change
- **Current**: `type-n` format (e.g., `click-1`, `scroll-2`)
- **Problem**: Not unique across page changes / tab switches
- **New Design**: Pure hash from CSS path (max 6 chars)
  - No prefix (no `click-`, `input-`, etc.)
  - Collision handling: add salt and rehash if collides with existing non-expired element
  - Maintain existing TTL expiration (2 minutes)

### 2. Cache Structure Change
- **Current**: Single-level cache `[conversation_id, elements[]]`
- **New Design**: Two-level cache `[tab_id + element_id, element]`
  - `highlight_elements`: write cache with tab_id association
  - `click_element`, `hover_element`, `keyboard_input`, `scroll_element`: read cache, require tab_id input

### 3. Screenshot Return Extension
- **Current**: `highlight_elements` and element operations return screenshots
- **New**: All `tab` operations AND `javascript_execute` also return screenshots (without highlights)

## Technical Decisions

### Hash Algorithm
- File already exists: `extension/src/commands/hash-utils.ts`
- Uses FNV-1a hash → base36 encoding
- Current format: `{type}-{hash}` (e.g., `click-a3f2b1`)
- **Required change**: Remove prefix, return pure hash only

### Cache Structure
- File: `extension/src/commands/element-cache.ts`
- Current: `Map<conversationId, {elements, timestamp}>`
- New: Need to include `tab_id` in key

### Affected Files (Preliminary)

**Extension (TypeScript)**:
1. `extension/src/commands/hash-utils.ts` - Remove prefix generation
2. `extension/src/commands/element-cache.ts` - Add tab_id to cache key
3. `extension/src/commands/interactive-elements.ts` - Generate hash IDs
4. `extension/src/commands/element-actions.ts` - Add tab_id parameter
5. `extension/src/background/index.ts` - Update command handlers
6. `extension/src/types.ts` - Update InteractiveElement.id documentation

**Server (Python)**:
1. `server/models/commands.py` - Add tab_id to element commands
2. `server/agent/tools/open_browser_tool.py` - Update action/observation models

## Open Questions

1. **Tab operations screenshot**: Should tab `list` action return screenshot? (It doesn't change page state)
2. **Error handling**: What if tab_id doesn't match cached element's tab_id?
3. **Cache key format**: `{tab_id}:{element_id}` or `{conversation_id}:{tab_id}:{element_id}`?
4. **Backward compatibility**: Should we support old element ID format during transition?

## Scope Boundaries
- INCLUDE: Element ID generation, cache structure, screenshot return
- EXCLUDE: Other visual interaction improvements, accessibility changes
