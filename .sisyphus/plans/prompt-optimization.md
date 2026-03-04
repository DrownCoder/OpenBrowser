# Prompt Optimization for Browser-First Agent

## TL;DR

> **Quick Summary**: Transform OpenBrowser from a general coding agent into a browser operation specialist by restructuring system_prompt.j2 and enhancing tool descriptions. The agent will excel at visual browser automation while retaining HTML/CSS/JS writing and bash execution as supporting capabilities.
> 
> **Deliverables**:
> - Updated `system_prompt.j2` with browser-first identity and new behavioral sections
> - Enhanced `open_browser_tool.py` with scrolling strategy and hover clarification
> - Updated `pyproject.toml` with new SDK commit reference
> - QA validation of 4 browser automation scenarios
> 
> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 3 waves
> **Critical Path**: SDK prompts → Commit SDK → Update pyproject → QA tests

---

## Context

### Original Request
User wants to optimize OpenBrowser's prompts to focus on browser operation rather than general coding. The current system prompt positions the agent as a "general coding AI Agent" with browser automation as "special capabilities." This should be inverted: browser automation first, coding as support.

### Interview Summary
**Key Discussions**:
- **Primary Role**: Browser automation expert (specialize in navigating, interacting, extracting data from websites)
- **Coding to Retain**: HTML/CSS/JS writing, bash commands (secondary capabilities)
- **Key Patterns**: Visual-first interaction, two-stage verification (BLUE→ORANGE)
- **Behavioral Requirements**: 
  - Always scroll for more content before giving up
  - Casual when searching online, but CAREFUL about correct element targeting
  - Avoid ambiguity when multiple similar elements exist
- **Error Recovery**: Re-discover elements with highlight_elements on mismatch
- **Hover Usage**: For interactive elements only (reveal tooltips/dropdowns), NOT for disambiguation
- **Sections to Reduce**: PROBLEM_SOLVING_WORKFLOW (de-emphasize TDD)
- **Test Scenarios**: Click similar links, scroll hidden content, handle dialogs, form input

### Metis Review
**Identified Gaps** (addressed):
- **Token budget**: Keep prompt reasonable, don't bloat excessively
- **Infinite scroll**: No explicit limit - agent decides based on context
- **What to remove**: Reduce PROBLEM_SOLVING_WORKFLOW (testing focus), keep PULL_REQUESTS and SECURITY
- **Test scenarios**: Defined 4 specific browser tasks for validation

---

## Work Objectives

### Core Objective
Transform OpenBrowser's prompts to position it as a browser operation specialist that excels at visual-first browser automation, with coding capabilities as secondary support.

### Concrete Deliverables
- `reference/agent-sdk/openhands-sdk/openhands/sdk/agent/prompts/system_prompt.j2` - Restructured with browser-first identity
- `server/agent/tools/open_browser_tool.py` - Enhanced with scrolling strategy and hover clarification
- `pyproject.toml` - Updated SDK commit reference

### Definition of Done
- [ ] System prompt restructured with new browser-focused sections
- [ ] Tool description enhanced with behavioral guidance
- [ ] SDK changes committed and pushed
- [ ] pyproject.toml updated with new commit reference
- [ ] 4 QA test scenarios pass

### Must Have
- Browser-first ROLE section in system_prompt.j2
- New sections: BROWSER_OPERATION_PHILOSOPHY, VISUAL_INTERACTION_WORKFLOW, SCROLLING_STRATEGY, AMBIGUITY_RESOLUTION, ERROR_RECOVERY
- Scrolling strategy guidance in tool description
- Clear hover usage clarification

### Must NOT Have (Guardrails)
- NO removal of HTML/CSS/JS and bash capabilities (they're secondary, not deleted)
- NO changes to tool interfaces or command schemas
- NO adding new tools
- NO modifications to extension code
- NO changes to AGENTS.md files

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: NO (no automated tests for prompts)
- **Automated tests**: Agent QA testing (manual execution by agent)
- **Framework**: N/A - Agent executes browser scenarios

### QA Policy
Every task includes agent-executed QA scenarios. Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Browser QA**: Agent uses OpenBrowser tool to execute test scenarios
- **Evidence**: Screenshots and observation logs captured during testing

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — SDK prompt restructuring):
├── Task 1: Replace ROLE section with browser-first identity [quick]
├── Task 2: Add BROWSER_OPERATION_PHILOSOPHY section [quick]
├── Task 3: Add VISUAL_INTERACTION_WORKFLOW section [quick]
├── Task 4: Add SCROLLING_STRATEGY section [quick]
├── Task 5: Add AMBIGUITY_RESOLUTION section [quick]
├── Task 6: Add ERROR_RECOVERY section [quick]
└── Task 7: Reduce PROBLEM_SOLVING_WORKFLOW section [quick]

Wave 2 (After Wave 1 — Tool description enhancements, MAX PARALLEL with Wave 1):
├── Task 8: Add scrolling strategy to tool description [quick]
└── Task 9: Add hover usage clarification to tool description [quick]

Wave 3 (After Waves 1-2 — Commit and Integration):
├── Task 10: Commit and push SDK changes [quick]
└── Task 11: Update pyproject.toml SDK reference [quick]

Wave 4 (After Wave 3 — QA Verification):
├── Task 12: QA - Click specific link among similar [unspecified-high]
├── Task 13: QA - Scroll to find hidden content [unspecified-high]
├── Task 14: QA - Handle browser dialogs [unspecified-high]
└── Task 15: QA - Form input workflow [unspecified-high]

Critical Path: Task 1-7 → Task 10 → Task 11 → Task 12-15
Parallel Speedup: ~50% faster than sequential
Max Concurrent: 9 (Waves 1 & 2)
```

### Dependency Matrix

- **1-7**: — — 10, 1
- **8-9**: — — 10, 1
- **10**: 1-9 — 11, 1
- **11**: 10 — 12-15, 1
- **12-15**: 11 — —

### Agent Dispatch Summary

- **Wave 1**: **7** — All `quick` (text editing)
- **Wave 2**: **2** — All `quick` (text editing, can parallel with Wave 1)
- **Wave 3**: **2** — All `quick` (git operations)
- **Wave 4**: **4** — All `unspecified-high` (QA testing)

---

## TODOs

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE. Rejection → fix → re-run.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists. For each "Must NOT Have": search codebase for forbidden patterns. Check evidence files exist. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `tsc --noEmit` + linter + type checks. Review all changed files for issues.
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill if UI)
  Start from clean state. Execute EVERY QA scenario from EVERY task. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff. Verify 1:1 — everything in spec was built, nothing beyond spec. Check "Must NOT do" compliance.
  Output: `Tasks [N/N compliant] | VERDICT`

---

## Commit Strategy

- **SDK Changes**: `feat(sdk): optimize prompts for browser-first agent identity`
  - Files: `openhands-sdk/openhands/sdk/agent/prompts/system_prompt.j2`
  - Pre-commit: None (prompt file, no tests)

- **Tool Enhancements**: `feat(server): enhance browser tool descriptions`
  - Files: `server/agent/tools/open_browser_tool.py`
  - Pre-commit: None

- **SDK Reference**: `chore: update openhands-sdk commit reference`
  - Files: `pyproject.toml`
  - Pre-commit: `uv sync`

---

## Success Criteria

### Verification Commands
```bash
# Verify SDK changes are in place
cat reference/agent-sdk/openhands-sdk/openhands/sdk/agent/prompts/system_prompt.j2 | grep -A5 "ROLE"

# Verify tool description enhanced
grep -A10 "Scrolling Strategy" server/agent/tools/open_browser_tool.py

# Verify pyproject.toml updated
grep "openhands-sdk" pyproject.toml
```

### Final Checklist
- [ ] ROLE section replaced with browser-first identity
- [ ] All 5 new sections added to system_prompt.j2
- [ ] PROBLEM_SOLVING_WORKFLOW reduced
- [ ] Tool description has scrolling strategy
- [ ] Tool description has hover clarification
- [ ] SDK changes committed and pushed
- [ ] pyproject.toml references new commit
- [ ] 4 QA scenarios pass
