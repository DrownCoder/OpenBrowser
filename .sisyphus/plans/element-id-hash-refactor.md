# Element ID Hash Refactor

## TL;DR

> **Quick Summary**: Refactor element identification from sequential numbering (`clickable-1`) to CSS-path-based 6-char hash IDs (`a3f2b1`). Change cache structure to be tab-scoped (`{conversation_id}:{tab_id}:{element_id}`). Extend screenshot returns to all tab operations (except list) and JavaScript execution.
> 
> **Deliverables**:
> - Modified element ID generation (pure hash, no prefix)
> - Tab-scoped element cache with strict validation
> - Screenshot returns for tab operations and JavaScript execution
> - Updated API models with tab_id parameters
> 
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 4 waves
> **Critical Path**: Task 1 → Task 4 → Task 6 → Task 8 → Task 10

---

## Context

### Original Request
Refactor element identification system:
1. Change element ID from `option-n` format to CSS-path-based hash (6 chars, no prefix)
2. Change cache structure from `[conversation_id, elements]` to `{conversation_id}:{tab_id}:{element_id}`
3. Add screenshot returns for tab operations and JavaScript execution
4. Element operations require tab_id parameter with validation

### Interview Summary

**Key Discussions**:
- Element ID format: Pure 6-char hash from CSS path (e.g., `a3f2b1`), collision resolved with salt rehash
- Cache key format: `{conversation_id}:{tab_id}:{element_id}` (3-part composite key)
- Tab operations screenshot: All except `list` return screenshot
- Tab ID validation: Strict - return error if tab_id doesn't match cached element's tab_id
- Backward compatibility: Not needed - direct breaking change

**Technical Decisions**:
- Hash algorithm: FNV-1a (already implemented in `hash-utils.ts`)
- Cache invalidation: TTL remains 2 minutes
- Collision resolution: Increment salt until unique hash found

### Metis Review

**Identified Gaps** (addressed):
- **Hash collision edge case**: Added fallback with `Date.now()` salt
- **Tab scope isolation**: Strict validation prevents cross-tab contamination
- **Breaking change notice**: All existing element IDs will change

**Risk Assessment**:
- Risk 1: Hash collision (extremely rare with 6-char base36)
  - Mitigation: Fallback to timestamp-based salt
- Risk 2: Screenshot performance impact on frequent tab operations
  - Mitigation: Acceptable tradeoff for visual feedback
- Risk 3: Existing AI scripts with hardcoded element IDs will break
  - Mitigation: Breaking change acknowledged by user

---

## Work Objectives

### Core Objective
Refactor element identification to use stable, collision-resistant hash IDs while maintaining all existing visual interaction behavior.

### Concrete Deliverables
1. Element ID generation using 6-char hash (no prefix)
2. Tab-scoped element cache with composite key
3. Screenshot returns for tab operations and JavaScript execution
4. API parameter updates for element operations

### Definition of Done
- [ ] All element IDs are 6-char hash format
- [ ] Cache keys include tab_id component
- [ ] Tab operations (except list) return screenshot
- [ ] JavaScript execution returns screenshot
- [ ] Element operations validate tab_id match
- [ ] All existing tests pass
- [ ] TypeScript compilation succeeds

### Must Have
- Element ID: 6-char base36 hash from CSS path
- Cache key: `{conversation_id}:{tab_id}:{element_id}`
- Collision resolution: Salt increment until unique
- tab_id parameter on all element operations
- Screenshot on tab init/open/close/switch/refresh
- Screenshot on JavaScript execution

### Must NOT Have (Guardrails)
- Element ID prefixes (no `click-`, `input-`, etc.)
- Cross-tab element operations (strict tab_id validation)
- Screenshot on tab list operation
- Backward compatibility code for old element ID format
- Changes to element detection/sorting logic

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: YES (bun test in extension)
- **Automated tests**: YES (TDD - tests written first)
- **Framework**: bun test
- **If TDD**: Each task follows RED (failing test) → GREEN (minimal impl) → REFACTOR

### QA Policy
Every task MUST include agent-executed QA scenarios with Playwright.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — Foundation):
├── Task 1: Update hash-utils.ts for pure hash IDs [quick]
├── Task 2: Update InteractiveElement type documentation [quick]
└── Task 3: Add unit tests for hash generation [quick]

Wave 2 (After Wave 1 — Core logic):
├── Task 4: Refactor element-cache.ts for tab-scoped cache [unspecified-high]
├── Task 5: Update interactive-elements.ts for hash ID generation [unspecified-high]
└── Task 6: Add unit tests for cache structure [quick]

Wave 3 (After Wave 2 — API changes):
├── Task 7: Update element-actions.ts with tab_id validation [unspecified-high]
├── Task 8: Update server command models with tab_id [quick]
├── Task 9: Update background/index.ts command handlers [unspecified-high]
└── Task 10: Add integration tests for element operations [quick]

Wave 4 (After Wave 3 — Screenshot extension):
├── Task 11: Add screenshot returns to tab operations [quick]
├── Task 12: Add screenshot returns to JavaScript execution [quick]
├── Task 13: Update open_browser_tool.py action/observation models [unspecified-high]
├── Task 14: End-to-end integration tests [deep]

Wave FINAL (After ALL tasks — verification):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high + playwright)
└── Task F4: Scope fidelity check (deep)

Critical Path: Task 1 → Task 4 → Task 5 → Task 7 → Task 11/12 → Task 14
Parallel Speedup: ~60% faster than sequential
Max Concurrent: 3 (Waves 1 & 2)
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|-----------|--------|
| 1 | - | 4, 5 |
| 2 | - | 7, 8, 9 |
| 3 | 1 | 14 |
| 4 | 1 | 7 |
| 5 | 4 | 7, 10 |
| 6 | 4 | 10 |
| 7 | 4, 5 | 8, 9 |
| 8 | - | 9, 13 |
| 9 | 7, 8 | 10 |
| 10 | 5, 7 | 14 |
| 11 | 7 | 13, 14 |
| 12 | 7 | 13, 14 |
| 13 | 7, 8, 11, 12 | 14 |
| 14 | 1-13 | F1-F4 |

### Agent Dispatch Summary

- **Wave 1**: 3 tasks → T1-T3: `quick`
- **Wave 2**: 3 tasks → T4-T5: `unspecified-high`, T6: `quick`
- **Wave 3**: 4 tasks → T7: `unspecified-high`, T8-T10: `quick`-`unspecified-high`
- **Wave 4**: 4 tasks → T11-T12: `quick`, T13: `unspecified-high`, T14: `deep`
- **Wave FINAL**: 4 tasks → F1: `oracle`, F2-F4: `unspecified-high`/`deep`

---

## TODOs

- [x] 1. Update hash-utils.ts for pure hash IDs

  **What to do**:
  - Modify `generateElementId()` to return pure hash (remove type prefix)
  - Keep `generateShortHash()` and `generateUniqueHash()` unchanged
  - Update function signature: `generateElementId(type, cssPath, existingHashes)` → returns `{id: string, hash: string}` where `id` is just the hash

  **Must NOT do**:
  - Add prefixes to hash output (`click-`, `input-`, etc.)
  - Change existing hash algorithm (FNV-1a)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple function modification, no complex logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3)
  - **Blocks**: Tasks 4, 5
  - **Blocked By**: None (can start immediately)

  **References**:
  - `extension/src/commands/hash-utils.ts:91-99` - Current `generateElementId()` with prefix
  - `extension/src/commands/hash-utils.ts:18-42` - `generateShortHash()` implementation

  **Acceptance Criteria**:
  - [ ] `generateElementId('click', 'div#content > p', new Set())` returns `{id: 'a3f2b1', hash: 'a3f2b1'}` (no prefix)
  - [ ] Hash is always exactly 6 characters
  - [ ] Hash uses only base36 characters (0-9, a-z)

  **QA Scenarios**:
  ```
  Scenario: Pure hash generation without prefix
    Tool: Bash (bun test)
    Preconditions: Extension source available
    Steps:
      1. cd extension && bun test src/commands/__tests__/hash-utils.test.ts
      2. Assert `generateElementId()` returns hash without prefix
      3. Assert hash length is exactly 6 characters
    Expected Result: All tests pass
    Failure Indicators: Any test fails
    Evidence: .sisyphus/evidence/task-1-hash-generation.log
  ```

  **Commit**: NO (groups with Wave 1)

- [x] 2. Update InteractiveElement type documentation

  **What to do**:
  - Update `InteractiveElement.id` JSDoc comment in `types.ts`
  - Change from `// Element ID like "click-1", "scroll-1"` to `// Element ID: 6-char hash from CSS path (e.g., "a3f2b1")`

  **Must NOT do**:
  - Change any runtime type definitions
  - Modify other type properties

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Documentation update only
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3)
  - **Blocked By**: None

  **References**:
  - `extension/src/types.ts:216` - InteractiveElement.id field definition

  **Acceptance Criteria**:
  - [ ] JSDoc updated to reflect new ID format
  - [ ] No other type changes made

  **QA Scenarios**:
  ```
  Scenario: Type documentation verification
    Tool: Bash (grep)
    Preconditions: types.ts modified
    Steps:
      1. grep -n '6-char hash' extension/src/types.ts
    Expected Result: Pattern found with correct description
    Evidence: .sisyphus/evidence/task-2-doc-update.txt
  ```

  **Commit**: NO (groups with Wave 1)

- [x] 3. Add unit tests for hash generation

  **What to do**:
  - Create `extension/src/commands/__tests__/hash-utils.test.ts`
  - Test cases:
    1. Hash is exactly 6 characters
    2. Hash uses only base36 characters
    3. Same CSS path generates same hash (deterministic)
    4. Different CSS paths generate different hashes
    5. Collision resolution works (same hash + salt increment)
    6. Fallback to timestamp salt when max attempts exceeded

  **Must NOT do**:
  - Test implementation details (only test public API)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple unit test creation
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2)
  - **Blocked By**: Task 1 (needs updated implementation)

  **References**:
  - `extension/src/commands/hash-utils.ts` - Functions to test

  **Acceptance Criteria**:
  - [ ] All 6 test cases implemented
  - [ ] `bun test` passes all tests

  **QA Scenarios**:
  ```
  Scenario: Unit tests execute successfully
    Tool: Bash (bun test)
    Preconditions: Test file created
    Steps:
      1. cd extension && bun test src/commands/__tests__/hash-utils.test.ts
    Expected Result: All tests pass, 0 failures
    Evidence: .sisyphus/evidence/task-3-hash-tests.log
  ```

  **Commit**: NO (groups with Wave 1)

- [x] 4. Refactor element-cache.ts for tab-scoped cache

  **What to do**:
  - Change cache key from `conversationId` to `{conversationId}:{tabId}:{elementId}`
  - Update interface:
    ```typescript
    interface CacheEntry {
      element: InteractiveElement;
      tabId: number;
      timestamp: number;
    }
    ```
  - Update methods:
    - `storeElements(conversationId, tabId, elements)`: Store with composite key
    - `getElementById(conversationId, tabId, elementId)`: Lookup with composite key
    - `invalidate(conversationId, tabId?)`: Invalidate by conversation or specific tab
  - Keep TTL at 120000ms (2 minutes)

  **Must NOT do**:
  - Remove conversation_id from cache key (must be 3-part composite)
  - Change TTL duration

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Core data structure change affecting all element operations
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (sequential after Task 1)
  - **Blocks**: Task 7 (element actions need new cache API)
  - **Blocked By**: Task 1 (hash generation)

  **References**:
  - `extension/src/commands/element-cache.ts:8-11` - Current CacheEntry interface
  - `extension/src/commands/element-cache.ts:23-42` - Current storeElements implementation
  - `extension/src/commands/element-cache.ts:70-77` - Current getElementById implementation

  **Acceptance Criteria**:
  - [ ] Cache key format is `{conversationId}:{tabId}:{elementId}`
  - [ ] `getElementById()` validates tab_id match
  - [ ] `getElementById()` returns undefined if tab_id mismatch
  - [ ] TTL remains 120000ms

  **QA Scenarios**:
  ```
  Scenario: Tab-scoped cache lookup
    Tool: Bash (bun test)
    Preconditions: Cache refactored
    Steps:
      1. Store element with conversationId='c1', tabId=100, elementId='a1b2c3'
      2. Lookup with matching tab_id → returns element
      3. Lookup with different tab_id → returns undefined
    Expected Result: Correct tab-scoped behavior
    Evidence: .sisyphus/evidence/task-4-cache-scope.test.log
  ```

  **Commit**: NO (groups with Wave 2)

- [x] 5. Update interactive-elements.ts for hash ID generation

  **What to do**:
  - Modify `createElementInfo()` (line 478-500) to use hash instead of sequential index:
    ```typescript
    import { generateShortHash } from './hash-utils';
    // In createElementInfo():
    const hash = generateShortHash(element.selector);
    return {
      id: hash,  // Pure hash, no prefix
      ...
    };
    ```
  - Track existing hashes for collision detection within same highlight call
  - Pass `existingHashes` set to avoid collisions in single batch

  **Must NOT do**:
  - Add prefix to element ID
  - Change element detection logic (`isClickable`, `isScrollable`, etc.)
  - Change element sorting/scoring logic

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Core ID generation change affecting all visual interactions
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (after Task 4)
  - **Blocks**: Task 7 (element actions need hash IDs)
  - **Blocked By**: Task 4 (needs new cache API)

  **References**:
  - `extension/src/commands/interactive-elements.ts:478-500` - createElementInfo function
  - `extension/src/commands/interactive-elements.ts:516-537` - sortInteractiveElements (ID reassignment)
  - `extension/src/commands/hash-utils.ts:generateShortHash` - Hash function to use

  **Acceptance Criteria**:
  - [ ] Element IDs are pure 6-char hashes
  - [ ] Same selector always produces same hash
  - [ ] No collisions within single highlight_elements call

  **QA Scenarios**:
  ```
  Scenario: Hash-based element ID generation
    Tool: Bash (bun test)
    Preconditions: interactive-elements.ts updated
    Steps:
      1. Call detectInteractiveElements() on test DOM
      2. Assert all element.id values are 6-char hashes
      3. Assert no ID prefixes present
    Expected Result: All IDs are pure hashes
    Evidence: .sisyphus/evidence/task-5-hash-ids.test.log
  ```

  **Commit**: NO (groups with Wave 2)

- [x] 6. Add unit tests for tab-scoped cache structure

  **What to do**:
  - Create `extension/src/commands/__tests__/element-cache.test.ts`
  - Test cases:
    1. Store and retrieve with matching tab_id succeeds
    2. Retrieve with non-matching tab_id returns undefined
    3. TTL expiration works correctly
    4. Invalidate by conversation clears all tabs
    5. Invalidate by specific tab only clears that tab
    6. Cross-tab isolation (same element_id, different tab_id)

  **Must NOT do**:
  - Test implementation details

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Unit test creation
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (after Task 4)
  - **Blocked By**: Task 4 (needs refactored cache)

  **References**:
  - `extension/src/commands/element-cache.ts` - Cache implementation to test

  **Acceptance Criteria**:
  - [ ] All 6 test cases implemented
  - [ ] `bun test` passes all tests

  **QA Scenarios**:
  ```
  Scenario: Cache unit tests pass
    Tool: Bash (bun test)
    Preconditions: Test file created
    Steps:
      1. cd extension && bun test src/commands/__tests__/element-cache.test.ts
    Expected Result: All tests pass
    Evidence: .sisyphus/evidence/task-6-cache-tests.log
  ```

  **Commit**: NO (groups with Wave 2)

- [x] 7. Update element-actions.ts with tab_id validation

  **What to do**:
  - Add `tabId` parameter to all element action functions:
    - `performElementClick(conversationId, elementId, tabId, timeout)`
    - `performElementHover(conversationId, elementId, tabId, timeout)`
    - `performElementScroll(conversationId, elementId, direction, tabId, timeout)`
    - `performKeyboardInput(conversationId, elementId, text, tabId, timeout)`
  - Update cache lookup calls to include tabId:
    - `elementCache.getElementById(conversationId, tabId, elementId)`
  - Add validation: Return error if cached element's tabId doesn't match provided tabId
  - Error message: `Element ${elementId} was found in tab ${cachedTabId} but operation requested on tab ${tabId}`

  **Must NOT do**:
  - Allow cross-tab operations (strict validation required)
  - Change JavaScript execution logic (only add tab_id parameter)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: API signature changes affecting all callers
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (after Tasks 4, 5)
  - **Blocks**: Tasks 8, 9 (command handlers)
  - **Blocked By**: Task 4 (cache API), Task 5 (hash IDs)

  **References**:
  - `extension/src/commands/element-actions.ts:52-57` - performElementClick signature
  - `extension/src/commands/element-actions.ts:65-75` - Current cache lookup
  - `extension/src/commands/element-cache.ts:getElementById` - New cache API

  **Acceptance Criteria**:
  - [ ] All 4 functions have tabId parameter
  - [ ] Cache lookups include tabId
  - [ ] Mismatch returns error (not exception)

  **QA Scenarios**:
  ```
  Scenario: Tab ID validation rejects cross-tab operations
    Tool: Bash (bun test)
    Preconditions: element-actions.ts updated
    Steps:
      1. Store element in cache with tabId=100
      2. Call performElementClick with tabId=200
      3. Assert error message contains 'tab mismatch'
    Expected Result: Operation rejected with clear error
    Evidence: .sisyphus/evidence/task-7-tab-validation.test.log
  ```

  **Commit**: NO (groups with Wave 3)

- [x] 8. Update server command models with tab_id

  **What to do**:
  - Add `tab_id: int` field to element command models in `server/models/commands.py`:
    - `ClickElementCommand`
    - `HoverElementCommand`
    - `ScrollElementCommand`
    - `KeyboardInputCommand`
  - Add validation: `tab_id` is required for these commands

  **Must NOT do**:
  - Make tab_id optional (must be required)
  - Change other command fields

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple Pydantic model field addition
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (independent of extension changes)
  - **Blocks**: Task 9, Task 13
  - **Blocked By**: None

  **References**:
  - `server/models/commands.py:263-268` - ClickElementCommand
  - `server/models/commands.py:271-276` - HoverElementCommand
  - `server/models/commands.py:279-289` - ScrollElementCommand
  - `server/models/commands.py:291-299` - KeyboardInputCommand

  **Acceptance Criteria**:
  - [ ] All 4 commands have `tab_id: int` field
  - [ ] Validation requires tab_id

  **QA Scenarios**:
  ```
  Scenario: Command model validation requires tab_id
    Tool: Bash (python -c)
    Preconditions: Models updated
    Steps:
      1. python -c "from server.models.commands import ClickElementCommand; cmd = ClickElementCommand(element_id='test')"
    Expected Result: ValidationError raised (missing tab_id)
    Evidence: .sisyphus/evidence/task-8-model-validation.log
  ```

  **Commit**: NO (groups with Wave 3)

- [x] 9. Update background/index.ts command handlers

  **What to do**:
  - Update element operation handlers to pass tab_id from command to element-actions:
    - `highlight_elements`: Store with current tab_id from `managedTab`
    - `click_element`: Extract `tab_id` from command, pass to `performElementClick()`
    - `hover_element`: Extract `tab_id` from command, pass to `performElementHover()`
    - `scroll_element`: Extract `tab_id` from command, pass to `performElementScroll()`
    - `keyboard_input`: Extract `tab_id` from command, pass to `performKeyboardInput()`
  - Update error handling for tab_id mismatch errors

  **Must NOT do**:
  - Change command routing logic
  - Modify other command handlers (tab, javascript, etc.)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Core command handler changes
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (after Tasks 7, 8)
  - **Blocks**: Task 10
  - **Blocked By**: Task 7 (element-actions), Task 8 (models)

  **References**:
  - `extension/src/background/index.ts` - Command handler routing
  - `extension/src/commands/element-actions.ts` - Action functions to call

  **Acceptance Criteria**:
  - [ ] All 5 element handlers pass tab_id correctly
  - [ ] `highlight_elements` stores elements with current tab_id
  - [ ] Error messages for tab_id mismatch are propagated

  **QA Scenarios**:
  ```
  Scenario: Command handlers pass tab_id
    Tool: Playwright (extension)
    Preconditions: Extension built with new handlers
    Steps:
      1. Send highlight_elements command
      2. Verify cache stores with tab_id
      3. Send click_element with different tab_id
      4. Verify error returned
    Expected Result: Tab ID correctly propagated and validated
    Evidence: .sisyphus/evidence/task-9-handler-integration.png
  ```

  **Commit**: NO (groups with Wave 3)

- [x] 10. Add integration tests for element operations

  **What to do**:
  - Create integration tests verifying end-to-end flow:
    1. `highlight_elements` returns hash IDs (no prefixes)
    2. `click_element` with matching tab_id succeeds
    3. `click_element` with mismatched tab_id fails with error
    4. `keyboard_input` validates tab_id
  - Test via HTTP API (server + extension)

  **Must NOT do**:
  - Test extension internals (only test public API)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Integration test creation
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (after Task 9)
  - **Blocked By**: Tasks 5, 7, 9

  **References**:
  - `server/api/routes/` - HTTP endpoints to test
  - Extension command handlers

  **Acceptance Criteria**:
  - [ ] All 4 test scenarios pass
  - [ ] Tests use real HTTP requests

  **QA Scenarios**:
  ```
  Scenario: Integration tests execute
    Tool: Bash (pytest)
    Preconditions: Server and extension running
    Steps:
      1. pytest tests/integration/test_element_operations.py
    Expected Result: All tests pass
    Evidence: .sisyphus/evidence/task-10-integration-tests.log
  ```

  **Commit**: NO (groups with Wave 3)

- [x] 11. Add screenshot returns to tab operations

  **What to do**:
  - In `server/agent/tools/open_browser_tool.py`, add screenshot capture after tab operations:
    - After `tab init`: capture screenshot
    - After `tab open`: capture screenshot
    - After `tab close`: capture screenshot (of remaining active tab)
    - After `tab switch`: capture screenshot
    - After `tab refresh`: capture screenshot
  - **NOT** for `tab list` (no page state change)
  - Use existing `captureScreenshot()` via command processor

  **Must NOT do**:
  - Add screenshot to `tab list` operation
  - Change tab operation logic

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Add screenshot capture calls to existing logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (after Task 7)
  - **Blocks**: Task 13, Task 14
  - **Blocked By**: Task 7 (element-actions pattern)

  **References**:
  - `server/agent/tools/open_browser_tool.py:382-426` - Tab operation handling
  - `extension/src/commands/screenshot.ts:captureScreenshot` - Screenshot function

  **Acceptance Criteria**:
  - [ ] `tab init` returns `screenshot_data_url`
  - [ ] `tab open` returns `screenshot_data_url`
  - [ ] `tab close` returns `screenshot_data_url`
  - [ ] `tab switch` returns `screenshot_data_url`
  - [ ] `tab refresh` returns `screenshot_data_url`
  - [ ] `tab list` does NOT return screenshot

  **QA Scenarios**:
  ```
  Scenario: Tab operations return screenshots
    Tool: Bash (curl + jq)
    Preconditions: Server running
    Steps:
      1. curl -X POST http://localhost:8765/command -d '{"type":"tab","action":"init","url":"https://example.com"}' | jq 'has("screenshot")'
      2. Assert response contains screenshot field
    Expected Result: All operations except list have screenshot
    Evidence: .sisyphus/evidence/task-11-tab-screenshots.log
  ```

  **Commit**: NO (groups with Wave 4)

- [x] 12. Add screenshot returns to JavaScript execution

  **What to do**:
  - In `server/agent/tools/open_browser_tool.py`, add screenshot capture after JavaScript execution:
    - After `javascript_execute` succeeds: capture screenshot
  - Exclude if dialog is open (screenshot may fail)
  - Use existing `captureScreenshot()` via command processor

  **Must NOT do**:
  - Capture screenshot when dialog is open
  - Change JavaScript execution logic

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Add screenshot capture calls
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (after Task 7)
  - **Blocks**: Task 13, Task 14
  - **Blocked By**: Task 7 (element-actions pattern)

  **References**:
  - `server/agent/tools/open_browser_tool.py:428-481` - JavaScript execution handling
  - `extension/src/commands/screenshot.ts:captureScreenshot` - Screenshot function

  **Acceptance Criteria**:
  - [ ] `javascript_execute` returns `screenshot_data_url` on success
  - [ ] No screenshot when `dialog_opened` is true

  **QA Scenarios**:
  ```
  Scenario: JavaScript execution returns screenshot
    Tool: Bash (curl + jq)
    Preconditions: Server running
    Steps:
      1. curl -X POST http://localhost:8765/command -d '{"type":"javascript_execute","script":"document.title"}' | jq 'has("screenshot")'
    Expected Result: Response contains screenshot field
    Evidence: .sisyphus/evidence/task-12-js-screenshots.log
  ```

  **Commit**: NO (groups with Wave 4)

- [x] 13. Update open_browser_tool.py action/observation models

  **What to do**:
  - Update `OpenBrowserAction` (line 36-63):
    - Change `element_id` documentation to reflect hash format
    - Ensure `tab_id` is marked as required for element operations
  - Update `_OPEN_BROWSER_DESCRIPTION` (line 773-972):
    - Update Element ID Format section (line 804-813) to show pure hash format
    - Remove all references to `click-`, `input-`, etc. prefixes
    - Update examples to use hash IDs
    - Add note about tab_id requirement for element operations

  **Must NOT do**:
  - Change field types (only documentation)
  - Update unrelated sections

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Documentation changes affecting AI agent behavior
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (after Tasks 11, 12)
  - **Blocks**: Task 14
  - **Blocked By**: Tasks 7, 8, 11, 12

  **References**:
  - `server/agent/tools/open_browser_tool.py:36-63` - OpenBrowserAction
  - `server/agent/tools/open_browser_tool.py:804-813` - Element ID Format section

  **Acceptance Criteria**:
  - [ ] Element ID documentation shows pure hash format
  - [ ] All examples use hash IDs
  - [ ] tab_id requirement documented
  - [ ] No prefix references remain

  **QA Scenarios**:
  ```
  Scenario: Documentation updated correctly
    Tool: Bash (grep)
    Preconditions: File updated
    Steps:
      1. grep -c 'click-1\|input-1\|scroll-1' server/agent/tools/open_browser_tool.py
    Expected Result: Count is 0 (no old prefixes)
    Evidence: .sisyphus/evidence/task-13-doc-check.txt
  ```

  **Commit**: NO (groups with Wave 4)

- [x] 14. End-to-end integration tests

  **What to do**:
  - Create comprehensive E2E tests covering:
    1. Full workflow: `highlight_elements` → `click_element` with hash ID and tab_id
    2. Tab switch → `highlight_elements` → element operation (tab_id validation)
    3. `javascript_execute` returns screenshot
    4. All tab operations (except list) return screenshots
    5. Hash collision resolution works correctly
  - Use Playwright for browser automation
  - Test against real Chrome extension

  **Must NOT do**:
  - Test internal implementation details

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Comprehensive E2E testing requiring full system integration
  - **Skills**: [`playwright`]
    - `playwright`: Browser automation for E2E testing

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (after all other tasks)
  - **Blocked By**: All tasks 1-13

  **References**:
  - All previous tasks
  - `extension/src/commands/` - All command modules
  - `server/agent/tools/open_browser_tool.py` - Tool interface

  **Acceptance Criteria**:
  - [ ] All 5 test scenarios pass
  - [ ] Tests use real browser + extension

  **QA Scenarios**:
  ```
  Scenario: E2E tests execute successfully
    Tool: Bash (bun test)
    Preconditions: Full system running
    Steps:
      1. cd extension && bun test tests/e2e/element-hash-refactor.test.ts
    Expected Result: All 5 scenarios pass
    Evidence: .sisyphus/evidence/task-14-e2e-tests.log
  ```

  **Commit**: YES
  - Message: `refactor(elements): change element IDs to pure hash format`,
  - Files: All modified files from Waves 1-4
  - Pre-commit: `bun test && npm run typecheck`

---

## Final Verification Wave (MANDATORY — after ALL implementation tasks)

> 4 review agents run in PARALLEL. ALL must APPROVE. Rejection → fix → re-run.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, curl endpoint, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `tsc --noEmit` + linter + `bun test`. Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names (data/result/item/temp).
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill if UI)
  Start from clean state. Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration (features working together, not isolation). Test edge cases: empty state, invalid input, rapid actions. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance. Detect cross-task contamination: Task N touching Task M's files. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Wave 1 (Tasks 1-3)**: `chore(hash): refactor element ID generation to pure hash format`
  - Files: `extension/src/commands/hash-utils.ts`, `extension/src/types.ts`, `extension/src/commands/__tests__/hash-utils.test.ts`
  - Pre-commit: `bun test`

- **Wave 2 (Tasks 4-6)**: `refactor(cache): change element cache to tab-scoped structure`
  - Files: `extension/src/commands/element-cache.ts`, `extension/src/commands/interactive-elements.ts`, `extension/src/commands/__tests__/element-cache.test.ts`
  - Pre-commit: `bun test`

- **Wave 3 (Tasks 7-10)**: `feat(api): add tab_id parameter to element operations`
  - Files: `extension/src/commands/element-actions.ts`, `server/models/commands.py`, `extension/src/background/index.ts`, `tests/integration/test_element_operations.py`
  - Pre-commit: `bun test && pytest`

- **Wave 4 (Tasks 11-14)**: `refactor(screenshot): add screenshot returns to tab and JS operations`
  - Files: `server/agent/tools/open_browser_tool.py`, `tests/e2e/element-hash-refactor.test.ts`
  - Pre-commit: `bun test && npm run typecheck`

---

## Success Criteria

### Verification Commands
```bash
# Element ID format verification
cd extension && bun test src/commands/__tests__/hash-utils.test.ts
# Expected: All tests pass, hash length = 6

# Cache structure verification
cd extension && bun test src/commands/__tests__/element-cache.test.ts
# Expected: All tests pass, tab-scoped lookups work

# Integration verification
pytest tests/integration/test_element_operations.py
# Expected: All tests pass, tab_id validation works

# E2E verification
cd extension && bun test tests/e2e/element-hash-refactor.test.ts
# Expected: All 5 scenarios pass

# Screenshot verification
curl -X POST http://localhost:8765/command -d '{"type":"tab","action":"init","url":"https://example.com"}' | jq 'has("screenshot")'
# Expected: true
```

### Final Checklist
- [ ] All element IDs are pure 6-char hashes (no prefixes)
- [ ] Cache keys include tab_id component
- [ ] Element operations validate tab_id
- [ ] Tab operations (except list) return screenshots
- [ ] JavaScript execution returns screenshots
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All E2E tests pass
- [ ] TypeScript compilation succeeds
- [ ] No old element ID prefixes in codebase
- [ ] Documentation updated to reflect new format
  - Message: `refactor(elements): change element IDs to pure hash format`,
  - Files: All modified files from Waves 1-4
  - Pre-commit: `bun test && npm run typecheck`




