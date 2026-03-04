# Plan: Track New Tab Creation in Observations

## TL;DR

> **Quick Summary**: Detect when `click_element` or `javascript_execute` triggers new tab creation and include this info in observations returned to the agent.
> 
> **Deliverables**:
> - Extension tracks new tabs created during JS execution
> - Server parses and includes in observation
> - Agent sees "New Tabs Created" section in observation
>
> **Estimated Effort**: Small (~1-2 hours)
> **Parallel Execution**: Limited - mostly sequential due to type dependencies
> **Critical Path**: Types → Extension → Server

---

## Context

### Original Request
User requested that `click_element` or `javascript_execute` commands should track when new tabs are created and include this information in the observation, so the agent is aware of this event. Must handle multiple tabs created together.

### Interview Summary
**Key Discussions**:
- Detection method: Short time window (~500ms after operation completes)
- Tab info format: Full details (Tab ID, URL, title)
- Scope: Only `click_element` and `javascript_execute` (exclude hover, scroll, keyboard_input)
- Verification: Manual QA only (no unit tests)

**Research Findings**:
- `tab-manager.ts` already has `onCreated` listener (lines 725-777) that auto-adds tabs to management
- Dialog tracking pattern exists and can be followed exactly
- `element-actions.ts` calls `executeJavaScript()` internally, so tracking only needs to be in one place

### Metis Review
**Identified Gaps** (addressed):
- Race condition: Tab created but not yet associated with conversation → Use `getManagedTabsOnly()` after delay
- False positives: Other extensions could create tabs → Only track tabs with `openerTabId` match
- Data consistency: URL may be blank during loading → Include with `loading: true` flag

---

## Work Objectives

### Core Objective
Track new tab creation during `click_element` and `javascript_execute` operations and include this information in the observation returned to the agent.

### Concrete Deliverables
- `extension/src/types.ts`: Add `new_tabs_created` field to result interfaces
- `extension/src/commands/javascript.ts`: Track tabs before/after JS execution
- `server/agent/tools/open_browser_tool.py`: Parse and include in observation
- Agent sees "## New Tabs Created" section in observation text

### Definition of Done
- [ ] `click_element` that opens new tab returns `new_tabs_created` with tab info
- [ ] `javascript_execute` with `window.open()` returns `new_tabs_created`
- [ ] Multiple tabs created at once all included in array
- [ ] No new tabs returns `new_tabs_created: []` or field omitted

### Must Have
- Tab ID, URL, and title for each new tab
- Support for multiple tabs created together
- Works for both `click_element` and `javascript_execute`

### Must NOT Have (Guardrails)
- DO NOT add tracking to `hover_element`, `scroll_element`, `keyboard_input`
- DO NOT create new tab management system (use existing `tab-manager.ts`)
- DO NOT include full Chrome tab objects (limit to ID, URL, title, loading)
- DO NOT add database persistence for tab creation history

---

## Verification Strategy (MANDATORY)

### Test Decision
- **Infrastructure exists**: N/A (no unit tests requested)
- **Automated tests**: None
- **Agent-Executed QA**: ALWAYS (mandatory for all tasks)

### QA Policy
Every task will include Agent-Executed QA Scenarios with ultra-detailed steps.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation - type definitions):
├── Task 1: Add new_tabs_created to TypeScript types [quick]
└── Task 2: Add new_tabs_created to Python types [quick]

Wave 2 (Extension implementation):
├── Task 3: Implement tab tracking in javascript.ts [quick]
└── Task 4: Propagate through element-actions.ts [quick]

Wave 3 (Server implementation):
├── Task 5: Parse new_tabs_created in open_browser_tool.py [quick]
└── Task 6: Add observation text formatting [quick]

Wave 4 (Verification):
├── Task 7: Manual QA - click_element opens new tab [quick]
├── Task 8: Manual QA - javascript_execute with window.open [quick]
└── Task 9: Manual QA - multiple tabs created [quick]

Critical Path: Task 1 → Task 3 → Task 5 → Task 7
```

### Dependency Matrix

| Task | Depends On | Blocks |
|------|------------|--------|
| 1 | — | 2, 3, 4 |
| 2 | — | 5, 6 |
| 3 | 1 | 4, 5 |
| 4 | 1, 3 | 5 |
| 5 | 2, 3, 4 | 6, 7, 8, 9 |
| 6 | 2, 5 | 7, 8, 9 |
| 7 | 5, 6 | — |
| 8 | 5, 6 | — |
| 9 | 5, 6 | — |

### Agent Dispatch Summary
- **Wave 1**: 2 tasks → `quick` (type definitions)
- **Wave 2**: 2 tasks → `quick` (extension logic)
- **Wave 3**: 2 tasks → `quick` (server logic)
- **Wave 4**: 3 tasks → `quick` (manual QA)

---

## TODOs

- [ ] 1. Add `new_tabs_created` Field to TypeScript Types

  **What to do**:
  - Add `new_tabs_created` field to `CommandResponse` interface in `extension/src/types.ts`
  - Add `new_tabs_created` field to `JavaScriptResult` interface in `extension/src/commands/javascript.ts`
  - Add `new_tabs_created` field to `ElementActionResult` interface in `extension/src/types.ts`
  - Type definition: `new_tabs_created?: Array<{tabId: number, url: string, title?: string, loading?: boolean}>`

  **Must NOT do**:
  - DO NOT add to other command interfaces (hover, scroll, keyboard)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple type definition additions
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Task 2 (Python types)
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 3, 4

  **References**:
  - `extension/src/types.ts:195-211` - `CommandResponse` interface with dialog fields pattern
  - `extension/src/commands/javascript.ts:63-79` - `JavaScriptResult` interface structure
  - `extension/src/types.ts:253-263` - `ElementActionResult` interface

  **Acceptance Criteria**:
  - [ ] TypeScript compiles without errors
  - [ ] All three interfaces have `new_tabs_created` field with correct type

  **QA Scenarios**:
  ```
  Scenario: Type definition compiles
    Tool: Bash
    Steps:
      1. cd extension && npm run typecheck
    Expected Result: No TypeScript errors
    Evidence: .sisyphus/evidence/task-01-typescript-compile.txt
  ```

  **Commit**: YES
  - Message: `feat(extension): add new_tabs_created field to result types`
  - Files: `extension/src/types.ts`, `extension/src/commands/javascript.ts`

---

- [ ] 2. Add `new_tabs_created` Field to Python Types

  **What to do**:
  - Add `new_tabs_created` field to `OpenBrowserObservation` class in `server/agent/tools/open_browser_tool.py`
  - Type: `Optional[List[Dict[str, Any]]]` with fields: tabId, url, title, loading
  - Default: `None`

  **Must NOT do**:
  - DO NOT add to other observation types

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple Pydantic field addition
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Task 1 (TypeScript types)
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 5, 6

  **References**:
  - `server/agent/tools/open_browser_tool.py:66-112` - `OpenBrowserObservation` class with dialog fields pattern

  **Acceptance Criteria**:
  - [ ] Python type checks pass (mypy)
  - [ ] Field accessible on observation object

  **QA Scenarios**:
  ```
  Scenario: Python types validate
    Tool: Bash
    Steps:
      1. cd server && uv run mypy server/agent/tools/open_browser_tool.py
    Expected Result: No mypy errors
    Evidence: .sisyphus/evidence/task-02-python-types.txt
  ```

  **Commit**: YES
  - Message: `feat(server): add new_tabs_created field to OpenBrowserObservation`
  - Files: `server/agent/tools/open_browser_tool.py`

---

- [ ] 3. Implement Tab Tracking in `javascript.ts`

  **What to do**:
  - In `executeJavaScript()` function, before executing JS:
    1. Get current managed tabs via `tabManager.getManagedTabsOnly(conversationId)`
    2. Store tab IDs in a Set
  - After JS execution completes (in success path):
    1. Wait 500ms for `onCreated` listener to process
    2. Get updated managed tabs
    3. Compare to find new tab IDs
    4. Build `new_tabs_created` array with `{tabId, url, title, loading}`
  - Include `new_tabs_created` in return value

  **Must NOT do**:
  - DO NOT modify tab creation logic in `tab-manager.ts`
  - DO NOT add tracking for commands other than JS execution

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Following existing dialog pattern
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: NO - depends on Task 1
  - **Parallel Group**: Wave 2 (after Task 1)
  - **Blocks**: Tasks 4, 5

  **References**:
  - `extension/src/commands/javascript.ts:93-393` - `executeJavaScript()` function to modify
  - `extension/src/commands/tab-manager.ts:283-286` - `getManagedTabsOnly()` method
  - `extension/src/commands/javascript.ts:63-79` - Return type interface (already modified in Task 1)

  **Acceptance Criteria**:
  - [ ] Before JS: captures current managed tab IDs
  - [ ] After JS: waits 500ms then compares tabs
  - [ ] Returns `new_tabs_created` array (empty if none)
  - [ ] TypeScript compiles

  **QA Scenarios**:
  ```
  Scenario: JS with window.open creates tracked tab
    Tool: Bash + Extension
    Preconditions: Extension connected, tab initialized
    Steps:
      1. Initialize tab: chrome-cli tabs init https://example.com
      2. Execute JS: window.open('https://google.com', '_blank')
      3. Check response contains new_tabs_created with google.com tab
    Expected Result: new_tabs_created array contains {tabId, url: "https://google.com"}
    Evidence: .sisyphus/evidence/task-03-js-window-open.txt
  ```

  **Commit**: YES
  - Message: `feat(extension): track new tabs created during JS execution`
  - Files: `extension/src/commands/javascript.ts`

---

- [ ] 4. Propagate Tab Tracking Through `element-actions.ts`

  **What to do**:
  - In `performElementClick()`: Pass through `new_tabs_created` from JS result
  - In `performElementHover()`: NO CHANGE (not in scope)
  - In `performElementScroll()`: NO CHANGE (not in scope)
  - In `performKeyboardInput()`: NO CHANGE (not in scope)
  - Update `ClickResult` interface (already done in Task 1)

  **Must NOT do**:
  - DO NOT add tab tracking to hover, scroll, or keyboard input

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple pass-through of existing field
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: NO - depends on Tasks 1, 3
  - **Parallel Group**: Wave 2 (with Task 3)
  - **Blocks**: Task 5

  **References**:
  - `extension/src/commands/element-actions.ts:52-263` - `performElementClick()` function
  - `extension/src/commands/element-actions.ts:166-176` - JS execution and result handling

  **Acceptance Criteria**:
  - [ ] `performElementClick()` returns `new_tabs_created` from JS result
  - [ ] TypeScript compiles

  **QA Scenarios**:
  ```
  Scenario: Click that opens new tab returns new_tabs_created
    Tool: Bash + Extension
    Preconditions: Extension connected, element with target="_blank" highlighted
    Steps:
      1. highlight_elements() to get element ID
      2. click_element() on link with target="_blank"
      3. Check response contains new_tabs_created
    Expected Result: new_tabs_created array with new tab info
    Evidence: .sisyphus/evidence/task-04-click-new-tab.txt
  ```

  **Commit**: YES
  - Message: `feat(extension): pass new_tabs_created through element click`
  - Files: `extension/src/commands/element-actions.ts`

---

- [ ] 5. Parse `new_tabs_created` in `open_browser_tool.py`

  **What to do**:
  - In `_execute_action_sync()` method:
    - For `click_element`: Extract `new_tabs_created` from result_dict
    - For `javascript_execute`: Extract `new_tabs_created` from result_dict
  - Pass to `OpenBrowserObservation` constructor

  **Must NOT do**:
  - DO NOT add parsing for other action types

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple field extraction, following dialog pattern
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: NO - depends on Tasks 2, 3, 4
  - **Parallel Group**: Wave 3
  - **Blocks**: Tasks 6, 7, 8, 9

  **References**:
  - `server/agent/tools/open_browser_tool.py:777-833` - Result extraction and observation creation
  - `server/agent/tools/open_browser_tool.py:785-803` - Dialog extraction pattern to follow

  **Acceptance Criteria**:
  - [ ] `javascript_execute` result parsed for `new_tabs_created`
  - [ ] `confirm_click_element` result parsed for `new_tabs_created`
  - [ ] Field passed to observation

  **QA Scenarios**:
  ```
  Scenario: Server parses new_tabs_created from extension
    Tool: Bash (curl)
    Preconditions: Server running, extension connected
    Steps:
      1. curl POST /command with javascript_execute that opens tab
      2. Check response contains new_tabs_created
    Expected Result: Response includes new_tabs_created array
    Evidence: .sisyphus/evidence/task-05-server-parse.txt
  ```

  **Commit**: YES
  - Message: `feat(server): parse new_tabs_created from extension responses`
  - Files: `server/agent/tools/open_browser_tool.py`

---

- [ ] 6. Add "New Tabs Created" Section to Observation Text

  **What to do**:
  - In `OpenBrowserObservation.to_llm_content()` method:
    - Add "## New Tabs Created" section after dialog section
    - Format: Tab ID, URL, Title for each tab
    - Include loading indicator if applicable
  - Also update `visualize` property if needed

  **Must NOT do**:
  - DO NOT include full Chrome tab objects
  - DO NOT add complex formatting

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple text formatting
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: NO - depends on Tasks 2, 5
  - **Parallel Group**: Wave 3 (with Task 5)
  - **Blocks**: Tasks 7, 8, 9

  **References**:
  - `server/agent/tools/open_browser_tool.py:113-320` - `to_llm_content()` method
  - `server/agent/tools/open_browser_tool.py:220-240` - Dialog section pattern to follow

  **Acceptance Criteria**:
  - [ ] "## New Tabs Created" section appears when tabs created
  - [ ] Section shows Tab ID, URL, Title for each
  - [ ] Section omitted when no new tabs

  **QA Scenarios**:
  ```
  Scenario: Observation text includes new tabs section
    Tool: Bash (curl)
    Steps:
      1. Execute action that creates new tab
      2. Get observation text via API
      3. Verify "## New Tabs Created" section present
    Expected Result: Text contains section with tab details
    Evidence: .sisyphus/evidence/task-06-observation-text.txt
  ```

  **Commit**: YES
  - Message: `feat(server): add new tabs section to observation text`
  - Files: `server/agent/tools/open_browser_tool.py`

---

- [ ] 7. Manual QA - `click_element` Opens New Tab

  **What to do**:
  - Start server and connect extension
  - Initialize tab with page containing `target="_blank"` link
  - Use `highlight_elements` to get element ID
  - Execute `click_element` on the link
  - Verify observation contains `new_tabs_created` with correct tab info

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Manual testing
  - **Skills**: `playwright` (for automated browser verification)

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 8, 9
  - **Parallel Group**: Wave 4
  - **Blocks**: None

  **References**:
  - `server/agent/tools/open_browser_tool.py` - Full implementation

  **QA Scenarios**:
  ```
  Scenario: Click element with target="_blank" creates tracked tab
    Tool: interactive_bash (tmux) + Bash (curl)
    Preconditions: Server running on port 8765, extension connected
    Steps:
      1. curl -X POST http://127.0.0.1:8765/command -d '{"type":"tab","action":"init","url":"https://example.com","conversation_id":"qa-test-1"}'
      2. curl -X POST http://127.0.0.1:8765/command -d '{"type":"highlight_elements","element_type":"clickable","conversation_id":"qa-test-1"}'
      3. Find element ID for link with target="_blank"
      4. curl -X POST http://127.0.0.1:8765/command -d '{"type":"click_element","element_id":"<found-id>","conversation_id":"qa-test-1"}'
      5. Check response: jq '.data.new_tabs_created'
    Expected Result: Array with at least one tab containing tabId, url
    Failure Indicators: Empty array, null, or field missing
    Evidence: .sisyphus/evidence/task-07-qa-click-blank.txt
  ```

  **Commit**: NO (verification only)

---

- [ ] 8. Manual QA - `javascript_execute` with `window.open`

  **What to do**:
  - Start server and connect extension
  - Initialize tab
  - Execute `javascript_execute` with `window.open('https://google.com', '_blank')`
  - Verify observation contains `new_tabs_created` with Google tab

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Manual testing
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 7, 9
  - **Parallel Group**: Wave 4
  - **Blocks**: None

  **References**:
  - `server/agent/tools/open_browser_tool.py` - Full implementation

  **QA Scenarios**:
  ```
  Scenario: JavaScript window.open creates tracked tab
    Tool: Bash (curl)
    Preconditions: Server running on port 8765, extension connected
    Steps:
      1. curl -X POST http://127.0.0.1:8765/command -d '{"type":"tab","action":"init","url":"https://example.com","conversation_id":"qa-test-2"}'
      2. curl -X POST http://127.0.0.1:8765/command -d '{"type":"javascript_execute","script":"window.open(\"https://google.com\", \"_blank\")","conversation_id":"qa-test-2"}'
      3. Check response: jq '.data.new_tabs_created'
    Expected Result: Array with tab containing url: "https://google.com"
    Failure Indicators: Empty array, null, or URL not google.com
    Evidence: .sisyphus/evidence/task-08-qa-js-open.txt
  ```

  **Commit**: NO (verification only)

---

- [ ] 9. Manual QA - Multiple Tabs Created

  **What to do**:
  - Start server and connect extension
  - Initialize tab
  - Execute JS that opens multiple tabs (e.g., multiple `window.open` calls)
  - Verify observation contains all new tabs

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Manual testing
  - **Skills**: None required

  **Parallelization**:
  - **Can Run In Parallel**: YES - with Tasks 7, 8
  - **Parallel Group**: Wave 4
  - **Blocks**: None

  **References**:
  - `server/agent/tools/open_browser_tool.py` - Full implementation

  **QA Scenarios**:
  ```
  Scenario: Multiple window.open calls create tracked tabs
    Tool: Bash (curl)
    Preconditions: Server running on port 8765, extension connected
    Steps:
      1. curl -X POST http://127.0.0.1:8765/command -d '{"type":"tab","action":"init","url":"https://example.com","conversation_id":"qa-test-3"}'
      2. curl -X POST http://127.0.0.1:8765/command -d '{"type":"javascript_execute","script":"window.open(\"https://google.com\"); window.open(\"https://github.com\");","conversation_id":"qa-test-3"}'
      3. Check response: jq '.data.new_tabs_created | length'
    Expected Result: Array with 2+ tabs
    Failure Indicators: Less than 2 tabs, or missing URLs
    Evidence: .sisyphus/evidence/task-09-qa-multiple-tabs.txt
  ```

  **Commit**: NO (verification only)

---

## Commit Strategy

- **Task 1-2**: `feat(types): add new_tabs_created field to result types`
- **Task 3**: `feat(extension): track new tabs created during JS execution`
- **Task 4**: `feat(extension): pass new_tabs_created through element click`
- **Task 5**: `feat(server): parse new_tabs_created from extension responses`
- **Task 6**: `feat(server): add new tabs section to observation text`

---

## Success Criteria

### Verification Commands
```bash
# 1. TypeScript compiles
cd extension && npm run typecheck

# 2. Python types check
cd server && uv run mypy server/agent/tools/open_browser_tool.py

# 3. Click opens new tab
curl -X POST http://127.0.0.1:8765/command -d '{"type":"javascript_execute","script":"window.open(\"https://example.com\")","conversation_id":"test"}' | jq '.data.new_tabs_created'

# Expected: Array with tab info
```

### Final Checklist
- [ ] TypeScript types compile without errors
- [ ] Python types pass mypy
- [ ] `click_element` on `target="_blank"` link returns `new_tabs_created`
- [ ] `javascript_execute` with `window.open()` returns `new_tabs_created`
- [ ] Multiple tabs all included in `new_tabs_created` array
- [ ] No new tabs returns empty array or field omitted
- [ ] Agent sees "## New Tabs Created" section in observation text
