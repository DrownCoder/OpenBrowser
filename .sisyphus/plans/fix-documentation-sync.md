# Fix Documentation and Code for Match Recent Implementation

> **Quick Summary**: Update documentation to reflect Element ID hash format change, fix duplicate class definition bug, and add missing visual commands to server docs.
> 
> **Deliverables**:
> - Fix AGENTS.md Element ID Format section and command examples
> - Fix duplicate HighlightElementsCommand class in server/models/commands.py
> - Update server/AGENTS.md with missing visual interaction commands
> - Fix TypeScript interfaces missing tab_id field (optional)
> - Add JSDoc comments clarifying tab_id auto-resolution
> 
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 5 waves
> **Critical Path**: Fix Python bug → Update core docs → Update server docs → Final verification

---

## Context

### Original Request
Review recent commits (1 week) and identify documentation discrepancies with code implementation, then fix them.

### Interview Summary
**Key Discussions**:
- Analyzed 49 commits from 2026-02-24 to 2026-03-03
- Major feature: Visual Interaction System (element-based, replacing coordinate-based)
- Critical change: Element IDs changed from `click-N` to 6-char hash (commit 69c6798)
- Dialog handling: Accurate, no changes needed

**Research Findings**:
- **Element System**: Migrated to pure 6-char hash format (FNV-1a + base36)
- **Code Bug**: Duplicate `HighlightElementsCommand` class definition (runtime error)
- **Documentation Gap**: Server AGENTS.md missing 7 new visual commands
- **Interface Mismatch**: TypeScript missing `tab_id` field

### Metis Review
**Identified Gaps** (addressed):
1. ✅ **Runtime Bug Priority**: Fix duplicate class before documentation updates
2. ✅ **Documentation Sync**: All AGENTS.md files need consistent Element ID format
3. ✅ **API Completeness**: Add missing commands to server/AGENTS.md

4. ✅ **Type Safety**: Fix TypeScript interfaces

---

## Work Objectives

### Core Objective
Update all documentation files to accurately reflect the current Element ID hash format implementation and fix the duplicate class definition runtime bug.

### Concrete Deliverables
- Fixed `AGENTS.md` with correct Element ID examples
- Fixed `server/models/commands.py` duplicate class definition
- Updated `server/AGENTS.md` with visual interaction commands
- Fixed `extension/src/types.ts` with tab_id field
- All tests passing after changes

### Definition of Done
- [ ] All Element ID examples use 6-char hash format (e.g., "a3f2b1")
- [ ] `server/models/commands.py` has only one `HighlightElementsCommand` class
- [ ] `server/AGENTS.md` includes all visual interaction commands
- [ ] TypeScript interfaces include optional `tab_id` field
- [ ] `pytest tests/integration/test_element_operations.py` passes
- [ ] `cd extension && npm run typecheck` shows no errors

### Must Have
- Correct Element ID format documentation (pure 6-char hash)
- Fixed duplicate class definition (only `element_type`, not `element_types`)
- All visual interaction commands documented in server/AGENTS.md
- TypeScript interfaces match Python models
- All tests pass

### Must NOT Have (Guardrails)
- NO changes to dialog handling documentation (already accurate)
- NO changes to element detection logic
- NO changes to collision detection algorithm
- NO breaking changes to Python or TypeScript code behavior
- NO removal of existing tests

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest for Python, bun test for TypeScript)
- **Automated tests**: TDD (fix first, verify tests still pass)
- **Framework**: pytest + bun test
- **TDD**: Each Python fix will be verified by running tests first

### QA Policy
Every task includes agent-executed QA scenarios with Playwright, tmux, or curl, and Bash as appropriate.

Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — fix critical runtime bug):
├── Task 1: Fix duplicate HighlightElementsCommand class [quick]
└── Task 2: Run Python tests to verify fix [quick]

Wave 2 (After Wave 1 — update core documentation):
├── Task 3: Update AGENTS.md Element ID Format section [quick]
├── Task 4: Update AGENTS.md command examples [quick]
└── Task 5: Update extension/src/types.ts with tab_id field [quick]

Wave 3 (After Wave 2 — update server documentation):
├── Task 6: Update server/AGENTS.md COMMAND TYPES table [quick]
├── Task 7: Add visual interaction commands to server/AGENTS.md [quick]

Wave 4 (After Wave 3 — final verification):
├── Task 8: Run TypeScript type checking [quick]
├── Task 9: Run Python tests again [quick]
├── Task 10: Run TypeScript tests [quick]
└── Task 11: Verify Element ID examples in all docs [quick]

Critical Path: Task 1 → Task 2 → Tasks 3-7 → Tasks 8-11
Parallel Speedup: ~60% faster than sequential
Max Concurrent: 3 (Waves 2 & 3)
```

### Dependency Matrix
- **1**: — 2
- **2**: 1 — 3-7
- **3-5**: — 8-11
- **6-7**: — 8-11

### Agent Dispatch Summary
- **Wave 1**: 2 tasks (1 quick, 1 quick)
- **Wave 2**: 3 tasks (all quick)
- **Wave 3**: 2 tasks (all quick)
- **Wave 4**: 4 tasks (all quick)

---

## TODOs

- [ ] 1. Fix duplicate HighlightElementsCommand class in server/models/commands.py

  **What to do**:
  - Remove lines 247-261 (second duplicate definition with `element_types`)
  - Keep only first definition with `element_type: Optional[str]`
  - Verify no other code references the removed `element_types` field
  
  **Must NOT do**:
  - Do NOT change the element detection or highlighting logic
  - Do NOT modify the first class definition (lines 230-246)
  
  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple file edit, remove duplicate lines
  - **Skills**: []
  
  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (with Task 2)
  - **Blocks**: Task 2 (tests need correct class)
  - **Blocked By**: None (can start immediately)
  
  **References**:
  - **Pattern References**: `server/models/commands.py:230-246` - First HighlightElementsCommand definition (keep this)
  - **Pattern References**: `server/models/commands.py:247-261` - Second duplicate definition (remove this)
  - **API References**: `extension/src/types.ts:115-120` - TypeScript interface expects `element_type` (singular)
  
  **Acceptance Criteria**:
  - [ ] Duplicate lines 247-261 removed
  - [ ] File has only one `HighlightElementsCommand` class
  - [ ] Class uses `element_type: Optional[str]` field
  - [ ] No references to `element_types` field anywhere
  
  **QA Scenarios**:
  ```
  Scenario: Python class is unique
    Tool: Bash (Python import)
    Preconditions: File modified, Python environment available
    Steps:
      1. Run: python -c "from server.models.commands import HighlightElementsCommand; print(HighlightElementsCommand.__fields__)"
      2. Assert output shows `element_type` field, not `element_types`
    Expected Result: Import succeeds, shows only singular element_type field
    Evidence: .sisyphus/evidence/task-1-python-import.txt
  ```
  
  **Commit**: YES (individual)
  - Message: `fix(server): remove duplicate HighlightElementsCommand definition`
  - Files: `server/models/commands.py`
  - Pre-commit: `cd server && python -c "from server.models.commands import HighlightElementsCommand"`

---

- [ ] 2. Run Python tests to verify fix

  **What to do**:
  - Run pytest to ensure tests still pass
  - Specifically run `tests/integration/test_element_operations.py`
  - Check for any failures related to element_type field
  
  **Must NOT do**:
  - Do NOT modify test files
  - Do NOT skip any failing tests
  
  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Test execution and verification
  - **Skills**: []
  
  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (with Task 1)
  - **Blocks**: Task 3-7 (documentation updates)
  - **Blocked By**: Task 1 (needs fixed class)
  
  **References**:
  - **Test References**: `tests/integration/test_element_operations.py` - Validates element highlighting
  - **Test References**: `pytest.ini` - Test configuration
  
  **Acceptance Criteria**:
  - [ ] `pytest tests/integration/test_element_operations.py` passes
  - [ ] No errors related to missing `element_types` field
  - [ ] All assertions pass
  
  **QA Scenarios**:
  ```
  Scenario: Element operations tests pass
    Tool: Bash (pytest)
    Preconditions: Task 1 completed, Python class fixed
    Steps:
      1. Run: pytest tests/integration/test_element_operations.py -v
      2. Assert all tests pass (0 failures)
      3. Check output shows hash format examples like "a3f2b1"
    Expected Result: All tests pass, output shows 6-char hash IDs
    Failure Indicators: Any test failures, assertions about "click-N" format
    Evidence: .sisyphus/evidence/task-2-pytest-pass.txt
  ```
  
  **Commit**: NO (part of verification)

---

- [ ] 3. Update AGENTS.md Element ID Format section

  **What to do**:
  - Replace lines 148-153 in AGENTS.md
  - Change Element ID Format description from prefix-number to pure 6-char hash
  - Update examples from `click-N` to hash like "a3f2b1"
  - Add explanation of hash algorithm (FNV-1a + base36)
  
  **Must NOT do**:
  - Do NOT change collision detection or pagination logic documentation
  - Do NOT remove the Visual Interaction Workflow section
  
  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Documentation update
  - **Skills**: []
  
  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 4, 5)
  - **Blocks**: Tasks 8-11 (verification)
  - **Blocked By**: Task 2 (tests pass)
  
  **References**:
  - **Pattern References**: `extension/src/commands/hash-utils.ts:84-99` - Hash generation implementation
  - **Pattern References**: `AGENTS.md:148-153` - Current (outdated) Element ID section
  - **API References**: `extension/src/types.ts:37` - InteractiveElement type with id comment
  
  **Acceptance Criteria**:
  - [ ] Section describes pure 6-character hash format
  - [ ] Examples use hash format (e.g., "a3f2b1", "9z8x7c")
  - [ ] Mentions FNV-1a hash algorithm
  - [ ] Explains hash is deterministic based on CSS selector
  
  **QA Scenarios**:
  ```
  Scenario: Element ID section is accurate
    Tool: Bash (grep)
    Preconditions: File modified
    Steps:
      1. Run: grep -n "click-N\|scroll-N\|input-N\|hover-N" AGENTS.md
      2. Assert: No matches (old format removed)
      3. Run: grep -n "6-char hash\|FNV-1a\|base36" AGENTS.md
      4. Assert: Matches found (new format documented)
    Expected Result: Old format examples removed, new hash format documented
    Evidence: .sisyphus/evidence/task-3-grep-format.txt
  ```
  
  **Commit**: YES (individual)
  - Message: `docs: update Element ID Format to pure 6-char hash`
  - Files: `AGENTS.md`
  - Pre-commit: `grep -E "click-N|scroll-N|input-N|hover-N" AGENTS.md` (expect no matches)

---

- [ ] 4. Update AGENTS.md command examples

  **What to do**:
  - Update command table in Visual Interaction Workflow section
  - Change all examples from `click-3`, `hover-1`, etc. to hash examples
  - Update examples in lines 125, 159-162
  - Replace `"click-3"` with `"a3f2b1"`, `"hover-1"` with `"9z8x7c"`, etc.
  
  **Must NOT do**:
  - Do NOT change command descriptions or purposes
  - Do NOT change the Commands table structure
  
  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Documentation update
  - **Skills**: []
  
  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 3, 5)
  - **Blocks**: Tasks 8-11 (verification)
  - **Blocked By**: Task 2 (tests pass)
  
  **References**:
  - **Pattern References**: `AGENTS.md:125` - Workflow example with old ID format
  - **Pattern References**: `AGENTS.md:156-162` - Commands table with old examples
  - **API References**: `extension/src/commands/hash-utils.ts` - Hash format implementation
  
  **Acceptance Criteria**:
  - [ ] All command examples use 6-char hash format
  - [ ] No examples use `click-N`, `scroll-N`, etc.
  - [ ] Examples are realistic (use actual hash characters)
  
  **QA Scenarios**:
  ```
  Scenario: Command examples use correct format
    Tool: Bash (grep)
    Preconditions: File modified
    Steps:
      1. Run: grep -n "element_id.*click\|element_id.*scroll\|element_id.*input\|element_id.*hover" AGENTS.md
      2. Assert: No matches (old format removed)
      3. Run: grep -n 'element_id.*"[a-z0-9]{6}"' AGENTS.md
      4. Assert: Matches found (new format present)
    Expected Result: All element_id examples use 6-char hash
    Evidence: .sisyphus/evidence/task-4-command-examples.txt
  ```
  
  **Commit**: NO (group with Task 3)

---

- [ ] 5. Update extension/src/types.ts with tab_id field

  **What to do**:
  - Add optional `tab_id?: number` field to TypeScript interfaces:
    - ClickElementCommand
    - HoverElementCommand
    - ScrollElementCommand
    - KeyboardInputCommand
  - Add JSDoc comment explaining tab_id auto-resolution
  - Clarify that tab_id is optional in TS but required in Python
  
  **Must NOT do**:
  - Do NOT make tab_id required in TypeScript (keep optional)
  - Do NOT change Python models (tab_id stays required)
  - Do NOT modify extension handlers (they already work correctly)
  
  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: TypeScript interface update
  - **Skills**: []
  
  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 2 (with Tasks 3, 4)
  - **Blocks**: Task 10 (TypeScript tests)
  - **Blocked By**: Task 2 (tests pass)
  
  **References**:
  - **API References**: `server/models/commands.py:263-304` - Python command models with tab_id field
  - **API References**: `extension/src/types.ts:115-143` - Current TypeScript interfaces (missing tab_id)
  - **Pattern References**: `extension/src/background/index.ts` - Extension handlers that auto-resolve tab_id
  
  **Acceptance Criteria**:
  - [ ] TypeScript interfaces include `tab_id?: number` field
  - [ ] JSDoc comment explains tab_id is optional and auto-resolved
  - [ ] No TypeScript errors when compiling
  
  **QA Scenarios**:
  ```
  Scenario: TypeScript interfaces compile without errors
    Tool: Bash (npm)
    Preconditions: File modified, TypeScript project
    Steps:
      1. Run: cd extension && npm run typecheck
      2. Assert: No TypeScript errors
      3. Check that tab_id field is present in compiled output
    Expected Result: npm run typecheck succeeds with 0 errors
    Failure Indicators: TypeScript compilation errors, missing tab_id field
    Evidence: .sisyphus/evidence/task-5-typescript-compile.txt
  ```
  
  **Commit**: YES (individual)
  - Message: `fix(extension): add optional tab_id field to TypeScript interfaces`
  - Files: `extension/src/types.ts`
  - Pre-commit: `cd extension && npm run typecheck`

---

- [ ] 6. Update server/AGENTS.md COMMAND TYPES table

  **What to do**:
  - Add 7 new visual interaction commands to COMMAND TYPES table
  - Commands to add:
    - highlight_elements
    - click_element
    - hover_element
    - scroll_element
    - keyboard_input
    - get_element_html
    - highlight_single_element
  - Add model class and handler for each
  
  **Must NOT do**:
  - Do NOT remove existing command entries
  - Do NOT change the table structure
  - Do NOT modify Python code (only documentation)
  
  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Documentation update
  - **Skills**: []
  
  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Task 7)
  - **Blocks**: Task 9 (Python tests)
  - **Blocked By**: Task 2 (tests pass)
  
  **References**:
  - **API References**: `server/models/commands.py:204-328` - All visual interaction command models
  - **Pattern References**: `server/AGENTS.md:62-71` - Current COMMAND TYPES table
  - **Pattern References**: `AGENTS.md:156-162` - Root AGENTS.md commands table (for reference)
  
  **Acceptance Criteria**:
  - [ ] COMMAND TYPES table includes all 7 visual interaction commands
  - [ ] Each command has correct model class name
  - [ ] Each command has correct handler description
  
  **QA Scenarios**:
  ```
  Scenario: All visual commands documented
    Tool: Bash (grep)
    Preconditions: File modified
    Steps:
      1. Run: grep -n "highlight_elements\|click_element\|hover_element\|scroll_element\|keyboard_input\|get_element_html\|highlight_single_element" server/AGENTS.md
      2. Assert: All 7 commands found in output
      3. Verify each has model class and handler listed
    Expected Result: All 7 commands present in COMMAND TYPES table
    Evidence: .sisyphus/evidence/task-6-command-table.txt
  ```
  
  **Commit**: NO (group with Task 7)

---

- [ ] 7. Add visual interaction commands details to server/AGENTS.md

  **What to do**:
  - Add new section after DIALOG HANDLING: "VISUAL INTERACTION COMMANDS"
  - Document all 7 commands with:
    - Purpose
    - Parameters
    - Usage examples
    - Notes about tab_id auto-resolution
  - Add cross-reference to root AGENTS.md Visual Interaction Workflow
  
  **Must NOT do**:
  - Do NOT duplicate information from root AGENTS.md
  - Do NOT change existing sections
  - Do NOT modify Python implementation
  
  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Documentation addition
  - **Skills**: []
  
  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 3 (with Task 6)
  - **Blocks**: Task 9 (Python tests)
  - **Blocked By**: Task 2 (tests pass)
  
  **References**:
  - **Pattern References**: `AGENTS.md:117-163` - Root AGENTS.md visual interaction documentation
  - **API References**: `server/models/commands.py:230-328` - Python command models with parameters
  - **API References**: `server/core/processor.py` - Command routing logic
  
  **Acceptance Criteria**:
  - [ ] New section "VISUAL INTERACTION COMMANDS" exists
  - [ ] All 7 commands documented with parameters
  - [ ] Usage examples use hash format IDs
  - [ ] Note about tab_id auto-resolution included
  
  **QA Scenarios**:
  ```
  Scenario: Visual interaction section exists and complete
    Tool: Bash (grep)
    Preconditions: File modified
    Steps:
      1. Run: grep -n "## VISUAL INTERACTION COMMANDS" server/AGENTS.md
      2. Assert: Section found
      3. Run: grep -c "tab_id" server/AGENTS.md | wc -l
      4. Assert: At least 7 lines mention tab_id (one per command)
    Expected Result: Section exists with all 7 commands documented
    Evidence: .sisyphus/evidence/task-7-visual-section.txt
  ```
  
  **Commit**: YES (individual)
  - Message: `docs(server): add visual interaction commands documentation`
  - Files: `server/AGENTS.md`
  - Pre-commit: `grep -c "highlight_elements" server/AGENTS.md` (expect match)

---

- [ ] 8. Run TypeScript type checking

  **What to do**:
  - Run `npm run typecheck` in extension directory
  - Verify no TypeScript errors
  - Check that tab_id field compiles correctly
  
  **Must NOT do**:
  - Do NOT modify TypeScript code unless errors found
  - Do NOT skip type checking step
  
  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Verification task
  - **Skills**: []
  
  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 9, 10, 11)
  - **Blocks**: None (final verification)
  - **Blocked By**: Tasks 3-7 (all implementation complete)
  
  **References**:
  - **Test References**: `extension/package.json` - npm scripts configuration
  - **Test References**: `extension/tsconfig.json` - TypeScript configuration
  - **API References**: `extension/src/types.ts` - Modified TypeScript interfaces
  
  **Acceptance Criteria**:
  - [ ] `npm run typecheck` succeeds with exit code 0
  - [ ] No TypeScript compilation errors
  - [ ] Output shows tab_id field is valid
  
  **QA Scenarios**:
  ```
  Scenario: TypeScript compilation succeeds
    Tool: Bash (npm)
    Preconditions: All implementation tasks complete
    Steps:
      1. Run: cd extension && npm run typecheck
      2. Assert: Exit code is 0
      3. Check output for "error" keyword (should be absent)
    Expected Result: Command succeeds, no errors
    Failure Indicators: Non-zero exit code, TypeScript errors in output
    Evidence: .sisyphus/evidence/task-8-typescript-check.txt
  ```
  
  **Commit**: NO (verification only)

---

- [ ] 9. Run Python tests again

  **What to do**:
  - Run pytest to verify all changes
  - Ensure integration tests still pass
  - Check that element_type field works correctly
  
  **Must NOT do**:
  - Do NOT modify test files
  - Do NOT skip failing tests
  
  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Test execution
  - **Skills**: []
  
  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 8, 10, 11)
  - **Blocks**: None (final verification)
  - **Blocked By**: Tasks 1-7 (all implementation complete)
  
  **References**:
  - **Test References**: `pytest.ini` - Test configuration
  - **Test References**: `tests/integration/test_element_operations.py` - Element operation tests
  - **Test References**: `server/tests/e2e/test_visual_interaction.py` - E2E tests
  
  **Acceptance Criteria**:
  - [ ] `pytest` succeeds with 0 failures
  - [ ] Integration tests pass
  - [ ] No errors related to element_type field
  
  **QA Scenarios**:
  ```
  Scenario: All Python tests pass
    Tool: Bash (pytest)
    Preconditions: All changes complete
    Steps:
      1. Run: pytest -v
      2. Assert: All tests pass (0 failures)
      3. Check output shows hash format in test assertions
    Expected Result: All tests pass, hash format validated
    Failure Indicators: Test failures, assertions about old format
    Evidence: .sisyphus/evidence/task-9-pytest-all.txt
  ```
  
  **Commit**: NO (verification only)

---

- [ ] 10. Run TypeScript tests

  **What to do**:
  - Run `bun test` in extension directory
  - Verify hash utility tests pass
  - Check element ID generation tests
  
  **Must NOT do**:
  - Do NOT modify test files
  - Do NOT skip failing tests
  
  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Test execution
  - **Skills**: []
  
  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 8, 9, 11)
  - **Blocks**: None (final verification)
  - **Blocked By**: Tasks 3-7 (all implementation complete)
  
  **References**:
  - **Test References**: `extension/package.json` - npm scripts with bun test
  - **Test References**: `extension/src/commands/__tests__/hash-utils.test.ts` - Hash utility unit tests
  - **Test References**: `extension/src/commands/__tests__/element-cache.test.ts` - Element cache tests
  
  **Acceptance Criteria**:
  - [ ] `bun test` succeeds
  - [ ] Hash utility tests pass
  - [ ] Element cache tests pass
  
  **QA Scenarios**:
  ```
  Scenario: TypeScript unit tests pass
    Tool: Bash (bun)
    Preconditions: All changes complete
    Steps:
      1. Run: cd extension && bun test
      2. Assert: All tests pass
      3. Check hash utility test output shows 6-char format
    Expected Result: All tests pass, hash format validated
    Failure Indicators: Test failures, hash format assertions fail
    Evidence: .sisyphus/evidence/task-10-bun-test.txt
  ```
  
  **Commit**: NO (verification only)

---

- [ ] 11. Verify Element ID examples in all docs

  **What to do**:
  - Search all documentation files for old element ID format
  - Verify no examples use `click-N`, `scroll-N`, etc.
  - Verify all examples use 6-char hash format
  - Check consistency across AGENTS.md files
  
  **Must NOT do**:
  - Do NOT create new documentation
  - Do NOT change implementation
  
  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Documentation verification
  - **Skills**: []
  
  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 4 (with Tasks 8, 9, 10)
  - **Blocks**: None (final verification)
  - **Blocked By**: Tasks 3-7 (all implementation complete)
  
  **References**:
  - **API References**: All AGENTS.md files
  - **API References**: README.md
  - **Pattern References**: `extension/src/commands/hash-utils.ts` - Hash format definition
  
  **Acceptance Criteria**:
  - [ ] No old format examples found (`click-N`, `scroll-N`, etc.)
  - [ ] All element_id examples use 6-char hash
  - [ ] Consistent format across all documentation files
  
  **QA Scenarios**:
  ```
  Scenario: All documentation uses consistent Element ID format
    Tool: Bash (grep)
    Preconditions: All documentation updated
    Steps:
      1. Run: find . -name "AGENTS.md" -o README.md | xargs grep -l "click-[0-9]\|scroll-[0-9]\|input-[0-9]\|hover-[0-9]" {} \;
      2. Assert: Exit code is 1 (no matches found)
      3. Run: find . -name "AGENTS.md" -o README.md | xargs grep -l '[a-z0-9]\{6\}' {} \;
      4. Assert: Multiple matches found (hash format present)
    Expected Result: No old format, all docs use 6-char hash
    Failure Indicators: Old format found in any documentation file
    Evidence: .sisyphus/evidence/task-11-doc-consistency.txt
  ```
  
  **Commit**: NO (verification only)

---

## Final Verification Wave

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read all modified files. Verify:
  - Python: Only one HighlightElementsCommand class
  - AGENTS.md: Element ID format is pure 6-char hash
  - server/AGENTS.md: All 7 visual commands documented
  - extension/src/types.ts: tab_id field present
  Output: `Class Definition [CORRECT] | Element IDs [CORRECT] | Commands [7/7] | TypeScript [VALID] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Test Results Review** — `unspecified-high`
  Run all test suites. Check:
  - Python tests: All pass
  - TypeScript tests: All pass
  - No test failures related to element_type or element_id changes
  Output: `Python [N pass/N fail] | TypeScript [N pass/N fail] | VERDICT`

- [ ] F3. **Documentation Consistency Check** — `unspecified-high`
  Read all AGENTS.md files. Verify:
  - Element ID format consistent (all use 6-char hash)
  - Command examples consistent
  - No references to old `click-N` format
  Output: `Root AGENTS.md [CONSISTENT] | Server AGENTS.md [CONSISTENT] | Extension AGENTS.md [N/A] | VERDICT`

- [ ] F4. **Cross-Reference Verification** — `deep`
  Check cross-references between docs:
  - server/AGENTS.md points to root AGENTS.md visual interaction section
  - README.md mentions visual interaction features
  - No broken links or outdated references
  Output: `Cross-Refs [VALID] | Broken Links [0] | VERDICT`

---

## Commit Strategy

- **Task 1**: `fix(server): remove duplicate HighlightElementsCommand definition` — server/models/commands.py
- **Task 2**: Test verification (no commit)
- **Task 3**: `docs: update Element ID Format to pure 6-char hash` — AGENTS.md
- **Task 5**: `fix(extension): add optional tab_id field to TypeScript interfaces` — extension/src/types.ts
- **Task 7**: `docs(server): add visual interaction commands documentation` — server/AGENTS.md
- Tasks 8-11: Verification only (no commits)

---

## Success Criteria

### Verification Commands
```bash
# Python tests pass
pytest -v
# Expected: All tests pass, hash format validated

# TypeScript compiles
cd extension && npm run typecheck
# Expected: No errors

# TypeScript tests pass
cd extension && bun test
# Expected: All tests pass

# No old format in docs
find . -name "AGENTS.md" -o README.md | xargs grep -l "click-[0-9]\|scroll-[0-9]\|input-[0-9]\|hover-[0-9]"
# Expected: Exit code 1 (no matches)
```

### Final Checklist
- [ ] Only one HighlightElementsCommand class in Python models
- [ ] All Element ID examples use 6-char hash format
- [ ] server/AGENTS.md includes all 7 visual interaction commands
- [ ] TypeScript interfaces include tab_id field
- [ ] All Python tests pass
- [ ] All TypeScript tests pass
- [ ] No documentation inconsistencies
