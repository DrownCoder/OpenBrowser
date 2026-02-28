# Visual Interaction Refactor - Work Plan

## TL;DR

> **Quick Summary**: 将OpenBrowser从基于JavaScript代码的浏览器操作重构为基于视觉高亮元素的纯视觉方案。AI通过视觉识别页面元素，基于element_id执行click/hover/scroll/keyboard_input操作。
> 
> **Deliverables**: 
> - 新的视觉高亮系统（在截图上绘制带编号的方框）
> - 基于element_id的操作命令（click, hover, scroll, keyboard_input）
> - 智能元素筛选与排序算法
> - TDD测试框架
> - 删除废弃的坐标系操作代码

> **Estimated Effort**: Large
> **Parallel Execution**: YES - 5 waves
> **Critical Path**: Test Framework → Element Detection → Visual Highlight → Operations → Integration

---

## Context

### Original Request
用户希望从**基于JavaScript代码的浏览器操作**转向**基于视觉高亮元素的纯视觉方案**。核心问题是JS代码/DOM结构不总是反映视觉页面（例如button在下层，文字在上层）。

### Interview Summary
**Key Discussions**:
- **滚动操作**: Element滚动 - 基于高亮元素滚动特定容器
- **Hover命令**: 保留独立hover命令，与click分离
- **Element ID格式**: 类型前缀如`click-1`, `scroll-1`, `input-1`
- **测试策略**: TDD (Test-Driven Development)

**Research Findings**:
- **可复用**: screenshot.ts (CDP截图), dialog.ts (对话框处理), javascript.ts (JS执行), tab-manager.ts, debugger-manager.ts
- **需删除**: computer.ts (817行坐标系操作)
- **需扩展**: grounded-elements.ts (元素提取), content/index.ts (视觉overlay)
- **需新增**: 智能排序算法、截图高亮绘制

### Metis Review
**Identified Gaps** (addressed):
- **高亮交互模式**: 每次操作前需要调用highlight_elements，高亮信息随截图返回
- **排序算法**: MVP使用简单启发式规则（viewport可见性 > 尺寸 > z-index）
- **性能**: 只高亮可见区域元素，使用Canvas硬件加速

**Guardrails Applied**:
- 保留`javascript_execute`作为向后兼容的fallback方案
- 使用现有`grounded-elements.ts`的bbox数据作为视觉定位基础
- 添加高亮超时机制（默认5秒），防止页面被永久遮挡

---

## Work Objectives

### Core Objective
重构OpenBrowser为纯视觉交互方案，让AI基于视觉识别页面元素，通过element_id执行操作，而不是通过JavaScript代码查找DOM元素。

### Concrete Deliverables
1. **测试框架**: Python (pytest) + TypeScript (bun test)
2. **命令模型**: server/models/commands.py 新增5种Command
3. **元素识别**: extension/src/commands/interactive-elements.ts
4. **视觉高亮**: extension/src/commands/visual-highlight.ts
5. **操作命令**: extension/src/commands/element-actions.ts
6. **Agent工具**: server/agent/tools/open_browser_tool.py 更新
7. **代码清理**: 删除computer.ts坐标系操作

### Definition of Done
- [ ] `bun test` 和 `pytest` 全部通过
- [ ] highlight_elements返回带高亮标记的截图
- [ ] click/hover/scroll/keyboard_input基于element_id执行
- [ ] 工具description反映新设计
- [ ] 无坐标相关代码残留

### Must Have
- 视觉高亮系统在截图上绘制方框+element_id
- 基于element_id的click, hover, scroll, keyboard_input
- 翻页返回高亮元素（limit/offset参数）
- 类型前缀element_id格式

### Must NOT Have (Guardrails)
- 坐标系鼠标操作（删除computer.ts）
- 固定坐标映射（1280x720）
- view操作类型（删除）
- 过度复杂的高亮样式系统
- 机器学习排序算法（MVP用简单启发式规则）

---

## Verification Strategy (MANDATORY)

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: NO
- **Automated tests**: TDD
- **Framework**: Python (pytest) + TypeScript (bun test)
- **TDD**: Each task follows RED → GREEN → REFACTOR

### QA Policy
Every task includes agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Extension TypeScript**: Use `bun test` — Unit tests for element detection, sorting, highlighting
- **Server Python**: Use `pytest` — Unit tests for command models, processor routing
- **Integration**: Use `curl` — API endpoint verification
- **E2E**: Use Playwright — Full workflow with real browser

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — Foundation):
├── Task 1: Test framework setup (pytest + bun test) [quick]
├── Task 2: Command models in server/models/commands.py [quick]
├── Task 3: Type definitions in extension/src/types.ts [quick]
└── Task 4: Delete computer.ts coordinate operations [quick]

Wave 2 (After Wave 1 — Extension Core):
├── Task 5: Interactive element detection [deep]
├── Task 6: Element sorting algorithm [deep]
├── Task 7: Visual highlight drawing on screenshot [deep]
└── Task 8: Element cache manager [quick]

Wave 3 (After Wave 2 — Operations):
├── Task 9: click command implementation [unspecified-high]
├── Task 10: hover command implementation [quick]
├── Task 11: scroll command implementation [quick]
├── Task 12: keyboard_input command implementation [quick]
└── Task 13: Dialog integration with new commands [unspecified-high]

Wave 4 (After Wave 3 — Server Integration):
├── Task 14: CommandProcessor routing for new commands [quick]
├── Task 15: OpenBrowserAction model update [quick]
├── Task 16: OpenBrowserObservation model update [quick]
├── Task 17: Tool description rewrite [writing]
└── Task 18: Delete view action type [quick]

Wave 5 (After Wave 4 — Integration & Cleanup):
├── Task 19: End-to-end integration test [deep]
├── Task 20: Performance optimization [unspecified-high]
└── Task 21: Final code cleanup [quick]

Wave FINAL (After ALL tasks — independent review):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA with Playwright (unspecified-high)
└── Task F4: Scope fidelity check (deep)

Critical Path: T1 → T5 → T7 → T9 → T14 → T19 → F1-F4
Parallel Speedup: ~60% faster than sequential
Max Concurrent: 4 (Waves 1 & 3)
```

### Dependency Matrix

- **1-4**: — (no dependencies, can start immediately)
- **5**: 1, 3
- **6**: 5
- **7**: 5, 6
- **8**: 5
- **9-12**: 7, 8
- **13**: 9
- **14**: 2, 9
- **15-17**: 2, 14
- **18**: 15
- **19**: 14, 18
- **20**: 19
- **21**: 19, 20
- **F1-F4**: 21

### Agent Dispatch Summary

- **Wave 1**: **4** — All `quick`
- **Wave 2**: **4** — T5-T6 → `deep`, T7 → `deep`, T8 → `quick`
- **Wave 3**: **5** — T9, T13 → `unspecified-high`, T10-T12 → `quick`
- **Wave 4**: **5** — T14-T16, T18 → `quick`, T17 → `writing`
- **Wave 5**: **3** — T19 → `deep`, T20 → `unspecified-high`, T21 → `quick`
- **FINAL**: **4** — F1 → `oracle`, F2-F3 → `unspecified-high`, F4 → `deep`

---

- [x] 1. **Test Framework Setup**

  **What to do**:
  - Create `pytest.ini` configuration for Python tests
  - Create `tests/` directory structure in server/
  - Add test dependencies to pyproject.toml (pytest, pytest-asyncio)
  - Create `extension/tests/` directory for TypeScript tests
  - Add test script to extension/package.json
  - Create example test file to verify setup

  **Must NOT do**:
  - Don't add complex test fixtures yet
  - Don't mock external services

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple configuration task, no complex logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4)
  - **Blocks**: Task 5 (element detection needs tests)
  - **Blocked By**: None

  **References**:
  - `pyproject.toml` - Python project configuration
  - `extension/package.json` - TypeScript project configuration
  - `extension/vite.config.ts` - Build configuration

  **Acceptance Criteria**:
  - [ ] `pytest --collect-only` shows test collection works
  - [ ] `bun test` runs (even if no tests exist yet)
  - [ ] Test directories exist: `server/tests/`, `extension/tests/`

  **QA Scenarios**:
  ```
  Scenario: pytest configuration works
    Tool: Bash
    Steps:
      1. cd /Users/yangxiao/git/OpenBrowser && pytest --collect-only
    Expected Result: No errors, shows test collection
    Evidence: .sisyphus/evidence/task-01-pytest-collect.txt

  Scenario: bun test runs
    Tool: Bash
    Steps:
      1. cd /Users/yangxiao/git/OpenBrowser/extension && bun test
    Expected Result: Runs (may show 0 tests)
    Evidence: .sisyphus/evidence/task-01-bun-test.txt
  ```

  **Commit**: YES
  - Message: `test: add pytest and bun test framework configuration`
  - Files: `pyproject.toml`, `pytest.ini`, `extension/package.json`

- [x] 2. **Command Models in server/models/commands.py**

  **What to do**:
  - Add `HighlightElementsCommand` with fields: element_types, limit, offset
  - Add `ClickElementCommand` with field: element_id
  - Add `HoverElementCommand` with field: element_id
  - Add `ScrollElementCommand` with fields: element_id, direction
  - Add `KeyboardInputCommand` with fields: element_id, text
  - Update `Command` Union type to include new commands
  - Update `parse_command()` to handle new types

  **Must NOT do**:
  - Don't remove existing commands (mouse, keyboard legacy)
  - Don't change REST API routes yet

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Straightforward Pydantic model definitions
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4)
  - **Blocks**: Task 14 (processor routing)
  - **Blocked By**: None

  **References**:
  - `server/models/commands.py:1-200` - Existing command patterns
  - `server/models/commands.py:BaseCommand` - Base class to extend

  **Acceptance Criteria**:
  - [ ] All 5 new command classes defined
  - [ ] `Command` Union includes new types
  - [ ] `parse_command("highlight_elements", {...})` works

  **QA Scenarios**:
  ```
  Scenario: parse highlight_elements command
    Tool: Bash (python -c)
    Steps:
      1. python -c "from server.models.commands import parse_command; cmd = parse_command({'type': 'highlight_elements', 'element_types': ['clickable'], 'limit': 10}); assert cmd.type == 'highlight_elements'"
    Expected Result: No assertion error
    Evidence: .sisyphus/evidence/task-02-parse-highlight.txt
  ```

  **Commit**: YES
  - Message: `feat(server): add visual interaction command models`
  - Files: `server/models/commands.py`

- [x] 3. **Type Definitions in extension/src/types.ts**

  **What to do**:
  - Add `InteractiveElement` interface: id, type, bbox, selector, tagName, text
  - Add `ElementType` enum: 'clickable', 'scrollable', 'inputable', 'hoverable'
  - Add `HighlightOptions` interface: elementTypes, limit, offset
  - Add `ElementAction` type for operation responses

  **Must NOT do**:
  - Don't change existing types
  - Don't add UI-specific types

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: TypeScript interface definitions
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4)
  - **Blocks**: Task 5 (element detection)
  - **Blocked By**: None

  **References**:
  - `extension/src/types.ts` - Existing type patterns

  **Acceptance Criteria**:
  - [ ] `InteractiveElement` interface defined
  - [ ] `ElementType` enum defined
  - [ ] TypeScript compiles without errors

  **QA Scenarios**:
  ```
  Scenario: TypeScript compiles
    Tool: Bash
    Steps:
      1. cd /Users/yangxiao/git/OpenBrowser/extension && npm run typecheck
    Expected Result: No TypeScript errors
    Evidence: .sisyphus/evidence/task-03-typecheck.txt
  ```

  **Commit**: YES
  - Message: `feat(extension): add visual interaction type definitions`
  - Files: `extension/src/types.ts`

- [x] 4. **Delete computer.ts Coordinate Operations**

  **What to do**:
  - Delete or comment out `performClick()` function (lines 192-295)
  - Delete or comment out `performMouseMove()` function (lines 301-397)
  - Delete or comment out `performScroll()` function (lines 667-774)
  - Delete `PRESET_WIDTH`, `PRESET_HEIGHT` constants
  - Delete `presetToActualCoords()` function
  - Delete `mousePositions` Map
  - Keep `CdpCommander` and utility functions
  - Update exports in `commands/index.ts`

  **Must NOT do**:
  - Don't delete the entire file - keep dialog and CDP utilities
  - Don't break existing imports

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Code deletion, straightforward
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3)
  - **Blocks**: None (cleanup task)
  - **Blocked By**: None

  **References**:
  - `extension/src/commands/computer.ts:51-774` - Code to remove
  - `extension/src/background/index.ts` - Import statements to update

  **Acceptance Criteria**:
  - [ ] No `PRESET_WIDTH` or `PRESET_HEIGHT` references
  - [ ] No `presetToActualCoords` references
  - [ ] TypeScript compiles without errors
  - [ ] Extension builds successfully

  **QA Scenarios**:
  ```
  Scenario: No coordinate code remains
    Tool: Bash (grep)
    Steps:
      1. grep -r "PRESET_WIDTH\|presetToActualCoords\|performClick.*tabId.*x.*y" extension/src/
    Expected Result: Empty output (no matches)
    Evidence: .sisyphus/evidence/task-04-no-coords.txt

  Scenario: Extension builds
    Tool: Bash
    Steps:
      1. cd /Users/yangxiao/git/OpenBrowser/extension && npm run build
    Expected Result: Build succeeds
    Evidence: .sisyphus/evidence/task-04-build.txt
  ```

  **Commit**: YES
  - Message: `refactor(extension): remove coordinate-based mouse operations`
  - Files: `extension/src/commands/computer.ts`

- [x] 5. **Interactive Element Detection**

  **What to do**:
  - Create `extension/src/commands/interactive-elements.ts`
  - Implement `detectInteractiveElements()` function
  - Detect clickable elements: `a`, `button`, `[role="button"]`, `[onclick]`, `[ng-click]`, `[@click]`
  - Detect scrollable elements: check `overflow: auto/scroll`, `element.scrollHeight > element.clientHeight`
  - Detect inputable elements: `input`, `textarea`, `[contenteditable="true"]`
  - Detect hoverable elements: elements with `:hover` CSS or `mouseenter` listeners
  - Calculate bounding box for each element using `getBoundingClientRect()`
  - Filter out hidden elements (`display: none`, `visibility: hidden`, `opacity: 0`)
  - Filter out off-screen elements
  - Return list of `InteractiveElement` objects with element_id generated

  **Must NOT do**:
  - Don't use complex ML-based detection
  - Don't detect elements inside `iframe` yet
  - Don't include `shadow DOM` elements yet

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex algorithm requiring careful DOM analysis
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO (foundation for Wave 2)
  - **Parallel Group**: Wave 2 (blocks Tasks 6, 7, 8)
  - **Blocks**: Tasks 6, 7, 8
  - **Blocked By**: Tasks 1, 3 (test framework, types)

  **References**:
  - `extension/src/commands/grounded-elements.ts:63-101` - Existing element detection patterns
  - `extension/src/helpers/browser-helpers.ts:67-86` - waitForClickable logic
  - `extension/src/types.ts:InteractiveElement` - Type definition from Task 3

  **Acceptance Criteria**:
  - [ ] `detectInteractiveElements()` returns array of `InteractiveElement`
  - [ ] Element IDs follow format `{type}-{index}` (e.g., `click-1`, `scroll-1`)
  - [ ] Hidden elements are filtered out
  - [ ] Unit tests pass: `bun test tests/interactive-elements.test.ts`

  **QA Scenarios**:
  ```
  Scenario: Detect elements on simple page
    Tool: Bash (curl + jq)
    Steps:
      1. Start server and extension
      2. Open test page with 3 buttons
      3. Call detectInteractiveElements
      4. Verify 3 clickable elements returned
    Expected Result: 3 elements with type="clickable"
    Evidence: .sisyphus/evidence/task-05-detect-simple.txt

  Scenario: Filter hidden elements
    Tool: Bash (curl + jq)
    Steps:
      1. Open page with 2 visible + 1 hidden button
      2. Call detectInteractiveElements
    Expected Result: Only 2 elements returned
    Evidence: .sisyphus/evidence/task-05-filter-hidden.txt
  ```

  **Commit**: YES
  - Message: `feat(extension): add interactive element detection`
  - Files: `extension/src/commands/interactive-elements.ts`
  - Pre-commit: `bun test tests/interactive-elements.test.ts`

- [x] 6. **Element Sorting Algorithm**

  **What to do**:
  - Create `sortInteractiveElements(elements: InteractiveElement[]): InteractiveElement[]`
  - Implement simple heuristic scoring:
    1. **Viewport visibility** (40%): Elements fully in viewport score higher
    2. **Size** (30%): Larger elements score higher (easier to click)
    3. **Z-index** (20%): Higher z-index elements score higher
    4. **Position** (10%): Top-left elements score slightly higher (reading order)
  - Sort by composite score descending
  - Ensure deterministic ordering (tie-breaker by DOM order)

  **Must NOT do**:
  - Don't use ML-based sorting
  - Don't access external APIs
  - Don't create complex scoring matrices

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Algorithm design requiring careful tuning
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (after Task 5)
  - **Blocks**: Task 7 (visual highlight needs sorted elements)
  - **Blocked By**: Task 5 (element detection)

  **References**:
  - `extension/src/commands/interactive-elements.ts:detectInteractiveElements` - Input data source

  **Acceptance Criteria**:
  - [ ] `sortInteractiveElements()` returns sorted array
  - [ ] Viewport elements appear before off-screen elements
  - [ ] Larger elements appear before smaller elements (same visibility)
  - [ ] Unit tests pass: `bun test tests/element-sorting.test.ts`

  **QA Scenarios**:
  ```
  Scenario: Viewport elements prioritized
    Tool: Bash (curl + jq)
    Steps:
      1. Open page with viewport button + off-screen button
      2. Get sorted elements
    Expected Result: Viewport button has lower index (appears first)
    Evidence: .sisyphus/evidence/task-06-viewport-priority.txt

  Scenario: Deterministic ordering
    Tool: Bash (curl + jq)
    Steps:
      1. Call sorting twice on same page
    Expected Result: Same order both times
    Evidence: .sisyphus/evidence/task-06-deterministic.txt
  ```

  **Commit**: YES
  - Message: `feat(extension): add element sorting algorithm`
  - Files: `extension/src/commands/interactive-elements.ts`
  - Pre-commit: `bun test tests/element-sorting.test.ts`

- [x] 7. **Visual Highlight Drawing on Screenshot**

  **What to do**:
  - Create `extension/src/commands/visual-highlight.ts`
  - Implement `drawHighlights(screenshotData: string, elements: InteractiveElement[], options): Promise<string>`
  - Use Canvas/OffscreenCanvas to draw on screenshot
  - Draw bounding box for each element (different colors by type):
    - Clickable: Blue `#0066FF`
    - Scrollable: Green `#00CC66`
    - Inputable: Orange `#FF9900`
    - Hoverable: Purple `#9966FF`
  - Draw element_id label inside/near the box (white text on colored background)
  - Support pagination: only draw elements in range `[offset, offset+limit]`
  - Return base64 PNG with highlights

  **Must NOT do**:
  - Don't modify the actual page DOM
  - Don't use CSS overlays
  - Don't draw more than 50 elements at once

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Canvas manipulation and visual rendering
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (after Tasks 5, 6)
  - **Blocks**: Task 9 (operations need visual feedback)
  - **Blocked By**: Tasks 5, 6 (element detection and sorting)

  **References**:
  - `extension/src/commands/screenshot.ts:60-96` - Existing Canvas handling
  - `extension/src/workers/image-processor.worker.ts:81-119` - OffscreenCanvas patterns
  - `extension/src/types.ts:InteractiveElement` - Element data structure

  **Acceptance Criteria**:
  - [ ] `drawHighlights()` returns base64 PNG
  - [ ] Bounding boxes drawn correctly
  - [ ] Element IDs visible on image
  - [ ] Different colors for different element types
  - [ ] Unit tests pass: `bun test tests/visual-highlight.test.ts`

  **QA Scenarios**:
  ```
  Scenario: Highlight draws bounding boxes
    Tool: Playwright (skill: playwright)
    Steps:
      1. Open test page with known button at position (100, 100)
      2. Call highlight_elements with type="clickable"
      3. Verify returned image has blue box at button position
    Expected Result: Blue box visible in screenshot
    Evidence: .sisyphus/evidence/task-07-highlight-boxes.png

  Scenario: Pagination works
    Tool: Bash (curl + jq)
    Steps:
      1. Page with 10 buttons
      2. Call highlight_elements with limit=5, offset=0
      3. Verify only 5 boxes drawn
    Expected Result: 5 boxes in image
    Evidence: .sisyphus/evidence/task-07-pagination.png
  ```

  **Commit**: YES
  - Message: `feat(extension): add visual highlight drawing on screenshot`
  - Files: `extension/src/commands/visual-highlight.ts`
  - Pre-commit: `bun test tests/visual-highlight.test.ts`

- [x] 8. **Element Cache Manager**

  **What to do**:
  - Create `extension/src/commands/element-cache.ts`
  - Implement `ElementCache` class:
    - `storeElements(conversationId: string, elements: InteractiveElement[]): void`
    - `getElements(conversationId: string): InteractiveElement[]`
    - `getElementById(conversationId: string, elementId: string): InteractiveElement | undefined`
    - `invalidate(conversationId: string): void`
  - Cache elements per conversation/session
  - Auto-invalidate after 30 seconds or on page navigation
  - Store element selector for re-finding if needed

  **Must NOT do**:
  - Don't persist cache across browser restarts
  - Don't cache more than 100 elements per session
  - Don't share cache between conversations

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple data structure implementation
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 7 in Wave 2)
  - **Parallel Group**: Wave 2
  - **Blocks**: Tasks 9-12 (operations need cache lookup)
  - **Blocked By**: Task 5 (needs element structure)

  **References**:
  - `extension/src/commands/interactive-elements.ts:InteractiveElement` - Data type
  - `extension/src/commands/tab-manager.ts` - Per-conversation patterns

  **Acceptance Criteria**:
  - [ ] `ElementCache` class implemented
  - [ ] `getElementById()` returns correct element
  - [ ] Cache invalidation works
  - [ ] Unit tests pass: `bun test tests/element-cache.test.ts`

  **QA Scenarios**:
  ```
  Scenario: Cache stores and retrieves elements
    Tool: Bash (bun test)
    Steps:
      1. Run unit test for cache store/get
    Expected Result: Test passes
    Evidence: .sisyphus/evidence/task-08-cache-store.txt

  Scenario: Auto-invalidation works
    Tool: Bash (bun test)
    Steps:
      1. Store elements
      2. Wait 31 seconds
      3. Try to retrieve
    Expected Result: Returns undefined (invalidated)
    Evidence: .sisyphus/evidence/task-08-cache-invalidate.txt
  ```

  **Commit**: YES
  - Message: `feat(extension): add element cache manager`
  - Files: `extension/src/commands/element-cache.ts`
  - Pre-commit: `bun test tests/element-cache.test.ts`

- [x] 9. **Click Command Implementation**

  **What to do**:
  - Create `performElementClick(conversationId: string, elementId: string)` in `extension/src/commands/element-actions.ts`
  - Look up element from cache by element_id
  - Execute JavaScript to click the element:
    - Use full event sequence: `pointerdown` → `mousedown` → `mouseup` → `click`
    - Support React/Vue synthetic events
  - Capture screenshot after click
  - Handle dialog events (reuse existing dialog manager)
  - Return result with screenshot and dialog info if any

  **Must NOT do**:
  - Don't use CDP `Input.dispatchMouseEvent` (violates design)
  - Don't assume element still exists (handle stale references)
  - Don't bypass dialog handling

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Complex implementation with edge cases
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (foundation for other operations)
  - **Blocks**: Task 13 (dialog integration)
  - **Blocked By**: Tasks 7, 8 (highlight and cache)

  **References**:
  - `extension/src/commands/javascript.ts:executeJavaScript()` - JS execution pattern
  - `extension/src/commands/dialog.ts:DialogManager` - Dialog handling
  - `extension/src/commands/element-cache.ts:getElementById()` - Cache lookup

  **Acceptance Criteria**:
  - [ ] `performElementClick()` clicks correct element
  - [ ] Full event sequence dispatched
  - [ ] Dialog events handled properly
  - [ ] Screenshot returned after click
  - [ ] Unit tests pass: `bun test tests/element-click.test.ts`

  **QA Scenarios**:
  ```
  Scenario: Click element triggers action
    Tool: Bash (curl + jq)
    Steps:
      1. Open page with button that shows alert
      2. highlight_elements to get element_id
      3. click element_id
      4. Verify dialog_opened is true
    Expected Result: dialog_opened = true
    Evidence: .sisyphus/evidence/task-09-click-dialog.txt

  Scenario: Click stale element fails gracefully
    Tool: Bash (curl + jq)
    Steps:
      1. highlight_elements
      2. Remove element via JS
      3. Try to click the now-stale element_id
    Expected Result: error message about stale element
    Evidence: .sisyphus/evidence/task-09-stale-element.txt
  ```

  **Commit**: YES
  - Message: `feat(extension): add element-based click command`
  - Files: `extension/src/commands/element-actions.ts`
  - Pre-commit: `bun test tests/element-click.test.ts`

- [x] 10. **Hover Command Implementation**

  **What to do**:
  - Add `performElementHover(conversationId: string, elementId: string)` to `element-actions.ts`
  - Look up element from cache
  - Execute JavaScript to dispatch hover events:
    - `pointerenter` → `pointerover` → `mouseenter` → `mouseover`
  - Capture screenshot after hover (to show tooltips, dropdowns)
  - Return screenshot

  **Must NOT do**:
  - Don't use CDP mouse events
  - Don't move actual mouse cursor

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Similar pattern to click, simpler
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 11, 12)
  - **Blocks**: None
  - **Blocked By**: Tasks 7, 8

  **References**:
  - `extension/src/commands/element-actions.ts:performElementClick` - Similar pattern

  **Acceptance Criteria**:
  - [ ] `performElementHover()` dispatches hover events
  - [ ] Tooltip/dropdown appears after hover
  - [ ] Screenshot returned
  - [ ] Unit tests pass: `bun test tests/element-hover.test.ts`

  **QA Scenarios**:
  ```
  Scenario: Hover shows tooltip
    Tool: Playwright (skill: playwright)
    Steps:
      1. Open page with button that shows tooltip on hover
      2. highlight_elements
      3. hover on button element_id
      4. Verify tooltip visible in screenshot
    Expected Result: Tooltip appears in screenshot
    Evidence: .sisyphus/evidence/task-10-hover-tooltip.png
  ```

  **Commit**: YES
  - Message: `feat(extension): add element-based hover command`
  - Files: `extension/src/commands/element-actions.ts`
  - Pre-commit: `bun test tests/element-hover.test.ts`

- [x] 11. **Scroll Command Implementation**

  **What to do**:
  - Add `performElementScroll(conversationId: string, elementId: string, direction: 'up' | 'down' | 'left' | 'right')` to `element-actions.ts`
  - Look up element from cache
  - Execute JavaScript to scroll the element:
    - Use `element.scrollBy()` for direction
    - If element_id is `page-scroll-1`, scroll `document.scrollingElement`
  - Capture screenshot after scroll
  - Return screenshot

  **Must NOT do**:
  - Don't use CDP mouse wheel
  - Don't scroll by pixels - use reasonable scroll amount (100px or 50vh)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Straightforward JS execution
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 10, 12)
  - **Blocks**: None
  - **Blocked By**: Tasks 7, 8

  **References**:
  - `extension/src/commands/element-actions.ts` - Action patterns

  **Acceptance Criteria**:
  - [ ] `performElementScroll()` scrolls correct element
  - [ ] Page scroll works for document element
  - [ ] Screenshot returned
  - [ ] Unit tests pass: `bun test tests/element-scroll.test.ts`

  **QA Scenarios**:
  ```
  Scenario: Scroll container element
    Tool: Bash (curl + jq)
    Steps:
      1. Open page with scrollable div
      2. highlight_elements with type="scrollable"
      3. scroll element_id direction="down"
      4. Verify scroll position changed
    Expected Result: Scroll position > 0
    Evidence: .sisyphus/evidence/task-11-scroll-container.txt
  ```

  **Commit**: YES
  - Message: `feat(extension): add element-based scroll command`
  - Files: `extension/src/commands/element-actions.ts`
  - Pre-commit: `bun test tests/element-scroll.test.ts`

- [x] 12. **Keyboard Input Command Implementation**

  **What to do**:
  - Add `performKeyboardInput(conversationId: string, elementId: string, text: string)` to `element-actions.ts`
  - Look up element from cache
  - Focus the element using JavaScript
  - Set value using multiple approaches:
    - Try `element.value = text` for input/textarea
    - Try `element.textContent = text` for contenteditable
    - Dispatch `input` and `change` events
  - For special keys like `{Enter}`, `{Tab}`, dispatch key events
  - Capture screenshot after input
  - Return screenshot

  **Must NOT do**:
  - Don't use CDP keyboard events
  - Don't type character by character (unless simulating typing)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Similar to existing patterns
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Tasks 10, 11)
  - **Blocks**: None
  - **Blocked By**: Tasks 7, 8

  **References**:
  - `extension/src/commands/element-actions.ts` - Action patterns

  **Acceptance Criteria**:
  - [ ] `performKeyboardInput()` sets value correctly
  - [ ] Works for input, textarea, contenteditable
  - [ ] Screenshot returned
  - [ ] Unit tests pass: `bun test tests/element-input.test.ts`

  **QA Scenarios**:
  ```
  Scenario: Input text into field
    Tool: Bash (curl + jq)
    Steps:
      1. Open page with text input
      2. highlight_elements with type="inputable"
      3. keyboard_input element_id="input-1" text="Hello World"
      4. Verify input value via javascript_execute
    Expected Result: input.value === "Hello World"
    Evidence: .sisyphus/evidence/task-12-input-text.txt
  ```

  **Commit**: YES
  - Message: `feat(extension): add element-based keyboard input command`
  - Files: `extension/src/commands/element-actions.ts`
  - Pre-commit: `bun test tests/element-input.test.ts`

- [x] 13. **Dialog Integration with New Commands**

  **What to do**:
  - Ensure click command integrates with existing `DialogManager`
  - Add dialog detection to element action handlers
  - Return `dialog_opened` and `dialog` info when click triggers dialog
  - Allow `handle_dialog` to work after element click
  - Test cascading dialogs

  **Must NOT do**:
  - Don't duplicate dialog handling logic
  - Don't change existing dialog behavior

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Integration work requiring careful testing
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3 (after Task 9)
  - **Blocks**: None
  - **Blocked By**: Task 9 (click command)

  **References**:
  - `extension/src/commands/dialog.ts:DialogManager` - Existing dialog logic
  - `extension/src/commands/javascript.ts` - Dialog race pattern

  **Acceptance Criteria**:
  - [ ] Click triggers dialog → `dialog_opened: true` in response
  - [ ] `handle_dialog` works after element click
  - [ ] Cascading dialogs handled
  - [ ] Integration tests pass: `bun test tests/dialog-integration.test.ts`

  **QA Scenarios**:
  ```
  Scenario: Click triggers confirm dialog
    Tool: Bash (curl + jq)
    Steps:
      1. Open page with button: onclick="confirm('Are you sure?')"
      2. highlight_elements
      3. click element_id
      4. Verify dialog_opened=true, dialog.type="confirm"
    Expected Result: Dialog info returned
    Evidence: .sisyphus/evidence/task-13-click-confirm.txt

  Scenario: Handle dialog after click
    Tool: Bash (curl + jq)
    Steps:
      1. Click triggers confirm
      2. handle_dialog action="accept"
      3. Verify dialog handled
    Expected Result: success=true
    Evidence: .sisyphus/evidence/task-13-handle-dialog.txt
  ```

  **Commit**: YES
  - Message: `feat(extension): integrate dialog handling with element actions`
  - Files: `extension/src/commands/element-actions.ts`
  - Pre-commit: `bun test tests/dialog-integration.test.ts`

- [x] 14. **CommandProcessor Routing for New Commands**

  **What to do**:
  - Update `server/core/processor.py:CommandProcessor.execute()`
  - Add routing for `highlight_elements` → call extension
  - Add routing for `click` → call extension
  - Add routing for `hover` → call extension
  - Add routing for `scroll` → call extension
  - Add routing for `keyboard_input` → call extension
  - Each handler sends command to WebSocket, waits for response

  **Must NOT do**:
  - Don't change existing command routing
  - Don't add REST endpoints (use existing /command)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple routing additions
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (foundation)
  - **Blocks**: Tasks 15-17
  - **Blocked By**: Tasks 2, 9 (command models, click implementation)

  **References**:
  - `server/core/processor.py:134-183` - Existing routing pattern
  - `server/models/commands.py` - New command types

  **Acceptance Criteria**:
  - [ ] All 5 new commands route to extension
  - [ ] Error handling for unknown commands
  - [ ] Unit tests pass: `pytest tests/test_processor.py`

  **QA Scenarios**:
  ```
  Scenario: highlight_elements routes correctly
    Tool: Bash (curl)
    Steps:
      1. Start server with extension connected
      2. POST /command with type="highlight_elements"
    Expected Result: 200 OK, extension receives command
    Evidence: .sisyphus/evidence/task-14-route-highlight.txt
  ```

  **Commit**: YES
  - Message: `feat(server): add routing for visual interaction commands`
  - Files: `server/core/processor.py`
  - Pre-commit: `pytest tests/test_processor.py`

- [x] 15. **OpenBrowserAction Model Update**

  **What to do**:
  - Update `server/agent/tools/open_browser_tool.py:OpenBrowserAction`
  - Add `type` options: `highlight_elements`, `click`, `hover`, `scroll`, `keyboard_input`
  - Add fields:
    - `element_types: Optional[List[str]]` for highlight
    - `element_id: Optional[str]` for click/hover/scroll/keyboard_input
    - `text: Optional[str]` for keyboard_input
    - `direction: Optional[str]` for scroll
    - `limit: Optional[int]` and `offset: Optional[int]` for highlight
  - Remove `view` from type Literal
  - Update field descriptions

  **Must NOT do**:
  - Don't remove existing fields (tab, javascript, handle_dialog)
  - Don't break backward compatibility

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pydantic model updates
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 16, 17)
  - **Blocks**: Task 18
  - **Blocked By**: Tasks 2, 14

  **References**:
  - `server/agent/tools/open_browser_tool.py:35-80` - Current Action model

  **Acceptance Criteria**:
  - [ ] New type options available
  - [ ] New fields defined with correct types
  - [ ] `view` removed from type Literal
  - [ ] Model validates correctly

  **QA Scenarios**:
  ```
  Scenario: Action validates new types
    Tool: Bash (python -c)
    Steps:
      1. Import OpenBrowserAction
      2. Create action with type="click", element_id="click-1"
    Expected Result: No validation error
    Evidence: .sisyphus/evidence/task-15-action-validate.txt
  ```

  **Commit**: YES
  - Message: `feat(server): update OpenBrowserAction for visual interaction`
  - Files: `server/agent/tools/open_browser_tool.py`
  - Pre-commit: `pytest tests/test_open_browser_tool.py`

- [x] 16. **OpenBrowserObservation Model Update**

  **What to do**:
  - Update `server/agent/tools/open_browser_tool.py:OpenBrowserObservation`
  - Ensure all operations return `screenshot_data_url`
  - Add `highlighted_elements: Optional[List[Dict]]` for highlight response
  - Add `total_elements: Optional[int]` for pagination info
  - Update `to_llm_content` to include element list in text

  **Must NOT do**:
  - Don't remove existing fields
  - Don't change screenshot format

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pydantic model updates
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 15, 17)
  - **Blocks**: Task 18
  - **Blocked By**: Tasks 2, 14

  **References**:
  - `server/agent/tools/open_browser_tool.py:85-340` - Current Observation model

  **Acceptance Criteria**:
  - [ ] All operations return screenshot
  - [ ] highlight response includes element list
  - [ ] Pagination info included
  - [ ] `to_llm_content` shows elements

  **QA Scenarios**:
  ```
  Scenario: Observation includes highlighted elements
    Tool: Bash (python -c)
    Steps:
      1. Create Observation with highlighted_elements
      2. Check to_llm_content includes element text
    Expected Result: Element list in content
    Evidence: .sisyphus/evidence/task-16-observation-elements.txt
  ```

  **Commit**: YES
  - Message: `feat(server): update OpenBrowserObservation for visual interaction`
  - Files: `server/agent/tools/open_browser_tool.py`
  - Pre-commit: `pytest tests/test_open_browser_tool.py`

- [x] 17. **Tool Description Rewrite**

  **What to do**:
  - Rewrite `_OPEN_BROWSER_DESCRIPTION` in `open_browser_tool.py`
  - New design philosophy:
    1. **Visual First**: AI sees page, identifies target via highlight
    2. **Element-based**: Operations use element_id, not coordinates
    3. **JavaScript as Fallback**: Only when visual approach fails
  - Document new workflow:
    1. `highlight_elements` to see interactive elements
    2. Identify target by element_id from image
    3. Use `click`, `hover`, `scroll`, `keyboard_input`
    4. Use `handle_dialog` if dialog appears
    5. Use `javascript_execute` as fallback
  - Remove old accessibility element guidance
  - Add pagination guidance (limit, offset)

  **Must NOT do**:
  - Don't mention coordinates or mouse positions
  - Don't recommend JavaScript-first approach
  - Don't include view operation

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Documentation and prompt engineering
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 15, 16)
  - **Blocks**: None
  - **Blocked By**: Tasks 2, 14

  **References**:
  - `server/agent/tools/open_browser_tool.py:702-908` - Current description

  **Acceptance Criteria**:
  - [ ] Description explains visual-first approach
  - [ ] All new commands documented
  - [ ] No mention of coordinates
  - [ ] JavaScript as fallback emphasized

  **QA Scenarios**:
  ```
  Scenario: Description is complete
    Tool: Bash (grep)
    Steps:
      1. grep -c "highlight_elements\|click\|hover\|scroll\|keyboard_input" server/agent/tools/open_browser_tool.py
    Expected Result: Count >= 5 (all commands mentioned)
    Evidence: .sisyphus/evidence/task-17-description-complete.txt

  Scenario: No coordinate references
    Tool: Bash (grep)
    Steps:
      1. grep -i "coordinate\|pixel\|mouse.*position\|1280\|720" server/agent/tools/open_browser_tool.py
    Expected Result: Empty (no matches in description)
    Evidence: .sisyphus/evidence/task-17-no-coords.txt
  ```

  **Commit**: YES
  - Message: `docs(server): rewrite tool description for visual-first approach`
  - Files: `server/agent/tools/open_browser_tool.py`

- [x] 18. **Delete view Action Type**

  **What to do**:
  - Remove `view` handling from `OpenBrowserExecutor._execute_action_sync()`
  - Remove `_get_screenshot_sync()` if only used by view
  - Ensure all operations return screenshot (view no longer needed)
  - Update any code that checks for `view` type

  **Must NOT do**:
  - Don't break existing operations
  - Don't remove screenshot functionality

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Code removal
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (after Tasks 15, 16)
  - **Blocks**: Task 19
  - **Blocked By**: Task 15

  **References**:
  - `server/agent/tools/open_browser_tool.py:496-536` - view implementation

  **Acceptance Criteria**:
  - [ ] `view` type no longer accepted
  - [ ] All operations return screenshot
  - [ ] No references to `view` in action handling

  **QA Scenarios**:
  ```
  Scenario: view type rejected
    Tool: Bash (python -c)
    Steps:
      1. Try to create Action with type="view"
    Expected Result: Validation error
    Evidence: .sisyphus/evidence/task-18-view-rejected.txt

  Scenario: All operations return screenshot
    Tool: Bash (curl)
    Steps:
      1. Execute click command
      2. Check response has screenshot_data_url
    Expected Result: screenshot_data_url present
    Evidence: .sisyphus/evidence/task-18-screenshot-returned.txt
  ```

  **Commit**: YES
  - Message: `refactor(server): remove view action type`
  - Files: `server/agent/tools/open_browser_tool.py`
  - Pre-commit: `pytest tests/test_open_browser_tool.py`

---

## Wave 5: Integration & Cleanup

- [x] 19. **End-to-End Integration Test**

  **What to do**:
  - Create `tests/e2e/test_visual_interaction.py`
  - Test complete workflow:
    1. `tab init https://example.com`
    2. `highlight_elements type="clickable" limit=10`
    3. Verify screenshot has blue boxes
    4. `click element_id="click-1"`
    5. Verify click executed
  - Test pagination: `highlight_elements offset=10 limit=10`
  - Test all element types: clickable, scrollable, inputable, hoverable
  - Test dialog handling with click

  **Must NOT do**:
  - Don't test on production websites (use test fixtures)
  - Don't skip cleanup

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex integration testing
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 5
  - **Blocks**: Tasks 20, 21
  - **Blocked By**: Tasks 14, 18

  **References**:
  - `tests/` - Test directory structure

  **Acceptance Criteria**:
  - [ ] E2E test passes: `pytest tests/e2e/test_visual_interaction.py`
  - [ ] All 4 element types tested
  - [ ] Pagination tested
  - [ ] Dialog integration tested

  **QA Scenarios**:
  ```
  Scenario: Full workflow works
    Tool: Bash (pytest)
    Steps:
      1. pytest tests/e2e/test_visual_interaction.py -v
    Expected Result: All tests pass
    Evidence: .sisyphus/evidence/task-19-e2e-pass.txt
  ```

  **Commit**: YES
  - Message: `test: add e2e tests for visual interaction`
  - Files: `tests/e2e/test_visual_interaction.py`
  - Pre-commit: `pytest tests/e2e/`

- [ ] 20. **Performance Optimization**

  **What to do**:
  - Benchmark element detection on complex pages
  - Optimize if detection takes >500ms:
    - Use `requestIdleCallback` for detection
    - Cache detection results per page state
    - Skip hidden/off-screen elements early
  - Optimize highlight drawing:
    - Use Canvas hardware acceleration
    - Limit max elements to 50 per highlight
  - Profile and fix any memory leaks

  **Must NOT do**:
  - Don't over-optimize prematurely
  - Don't sacrifice correctness for speed

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Performance analysis and optimization
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 5 (after Task 19)
  - **Blocks**: Task 21
  - **Blocked By**: Task 19

  **References**:
  - Chrome DevTools Performance tab
  - `extension/src/commands/interactive-elements.ts` - Code to optimize

  **Acceptance Criteria**:
  - [ ] Element detection <500ms on typical pages
  - [ ] Highlight drawing <200ms
  - [ ] No memory leaks after 100 operations

  **QA Scenarios**:
  ```
  Scenario: Detection is fast
    Tool: Bash (curl with timing)
    Steps:
      1. Time highlight_elements call on complex page
    Expected Result: <500ms response time
    Evidence: .sisyphus/evidence/task-20-detection-speed.txt

  Scenario: No memory leaks
    Tool: Playwright
    Steps:
      1. Run 100 highlight + click operations
      2. Check memory usage
    Expected Result: Memory stable (not growing)
    Evidence: .sisyphus/evidence/task-20-memory.txt
  ```

  **Commit**: YES
  - Message: `perf(extension): optimize element detection and highlighting`
  - Files: `extension/src/commands/interactive-elements.ts`, `extension/src/commands/visual-highlight.ts`

- [ ] 21. **Final Code Cleanup**

  **What to do**:
  - Remove any remaining dead code
  - Remove unused imports
  - Add/update type annotations
  - Update AGENTS.md with new architecture
  - Remove deprecated function comments
  - Final lint and format pass

  **Must NOT do**:
  - Don't change working logic
  - Don't add new features

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Code cleanup
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 5 (last task)
  - **Blocks**: None (final task)
  - **Blocked By**: Tasks 19, 20

  **References**:
  - All modified files

  **Acceptance Criteria**:
  - [ ] `ruff check server/` passes
  - [ ] `npm run typecheck` passes in extension/
  - [ ] No unused imports
  - [ ] AGENTS.md updated

  **QA Scenarios**:
  ```
  Scenario: Lint passes
    Tool: Bash
    Steps:
      1. ruff check server/ && cd extension && npm run typecheck
    Expected Result: No errors
    Evidence: .sisyphus/evidence/task-21-lint-pass.txt
  ```

  **Commit**: YES
  - Message: `chore: final cleanup for visual interaction refactor`
  - Files: Multiple
  - Pre-commit: `pytest && bun test`

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE. Rejection → fix → re-run.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists. For each "Must NOT Have": search codebase for forbidden patterns. Check evidence files exist. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `pytest` + `bun test` + `ruff check` + `tsc --noEmit`. Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports.
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill)
  Start from clean state. Execute EVERY QA scenario from EVERY task. Test cross-task integration. Test edge cases: empty page, dynamic content, iframe. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff. Verify 1:1 — everything in spec was built, nothing beyond spec was built. Check "Must NOT do" compliance. Detect cross-task contamination.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Wave 1 Complete**: `refactor(test): add TDD framework for visual interaction`
- **Wave 2 Complete**: `feat(extension): add visual element detection and highlighting`
- **Wave 3 Complete**: `feat(extension): add element-based operations (click/hover/scroll/input)`
- **Wave 4 Complete**: `refactor(server): update agent tool for visual interaction`
- **Wave 5 Complete**: `refactor: complete visual interaction refactor`
- **Each commit**: Run `pytest && bun test` as pre-commit

---

## Success Criteria

### Verification Commands
```bash
# Run all tests
pytest && bun test

# Verify highlight command works
curl -X POST http://localhost:8765/command -H "Content-Type: application/json" -d '{
  "type": "highlight_elements",
  "conversation_id": "test",
  "element_types": ["clickable"],
  "limit": 10
}' | jq '.success'
# Expected: true

# Verify click command works
curl -X POST http://localhost:8765/command -H "Content-Type: application/json" -d '{
  "type": "click",
  "conversation_id": "test",
  "element_id": "click-1"
}' | jq '.success'
# Expected: true

# Verify no coordinate code remains
grep -r "PRESET_WIDTH\|presetToActualCoords\|performClick.*x.*y" extension/src/
# Expected: (empty - no matches)
```

### Final Checklist
- [ ] All "Must Have" present (visual highlight, element_id operations)
- [ ] All "Must NOT Have" absent (coordinate operations, view type)
- [ ] All tests pass (pytest + bun test)
- [ ] Tool description updated
- [ ] No breaking changes to tab/handle_dialog/javascript_execute
