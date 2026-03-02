# Element Hash ID & Tab-Scoped Cache Refactor

## TL;DR

> **Quick Summary**: Refactor element identification from sequential `click-1` format to pure hash-based IDs (`a3f2b1`) with tab-scoped caching for uniqueness across page changes. Extend screenshot returns to all tab and JavaScript operations.

> **Deliverables**:
> - Hash-only element IDs (max 6 chars, no type prefix)
> - Tab-scoped element cache with composite keys
> - Screenshots returned from all tab operations and JavaScript execution
> - Updated Python command models with tab_id parameter
> - Updated tool documentation

> **Estimated Effort**: Medium
> **Parallel Execution**: YES - 4 waves
> **Critical Path**: Task 1 → Task 2-5 → Task 6-9 → Task 10-14

---

## Context

### Original Request
User wants to refactor the element ID system:
1. Change from `option-n` / `click-1` format to pure hash-based IDs
2. Make cache tab-scoped instead of conversation-scoped
3. Return screenshots from all tab and JavaScript operations

### Interview Summary
**Key Discussions**:
- **Hash Format**: Pure hash (e.g., `a3f2b1`) without type prefix for simplicity
- **Cache Key**: Composite key `${tabId}:${elementHash}` for tab isolation
- **tab_id Default**: Use active tab if not specified (convenience)
- **Screenshot Return**: Add to tab operations (init/open/close/switch/refresh/list) and JavaScript execute

**Research Findings**:
- `hash-utils.ts` already has FNV-1a hash implementation with collision resolution
- Current cache uses `Map<conversationId, CacheEntry>` - needs tab-scoping
- Element actions already receive `tabId` parameter - just need cache update
- Screenshot capture function `captureScreenshot()` already exists

---

## Work Objectives

### Core Objective
Stable, unique element identification across page navigation and tab switches, plus visual feedback for all browser operations.

### Concrete Deliverables
- `extension/src/commands/hash-utils.ts` - Pure hash ID generation
- `extension/src/commands/element-cache.ts` - Tab-scoped cache structure
- `extension/src/commands/element-actions.ts` - Updated cache lookups
- `extension/src/background/index.ts` - Screenshot returns for tab/JS operations
- `server/models/commands.py` - tab_id fields for element commands
- `server/agent/tools/open_browser_tool.py` - Updated action and documentation

### Definition of Done
- [ ] Element IDs are pure 6-character hashes
- [ ] Cache uses tab-scoped composite keys
- [ ] All tab operations return screenshots
- [ ] JavaScript execution returns screenshots
- [ ] Python models have tab_id fields
- [ ] Tool documentation reflects new ID format
- [ ] `npm run typecheck` passes
- [ ] `npm run build` succeeds

### Must Have
- Hash-only element IDs (no type prefix)
- Tab-scoped cache with composite key
- Screenshot return for tab/JS operations
- tab_id parameter on element commands

### Must NOT Have (Guardrails)
- DO NOT break existing element operations
- DO NOT change TTL behavior (2 minutes)
- DO NOT add unnecessary abstractions
- DO NOT over-document trivial changes

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: NO (no unit tests found)
- **Automated tests**: None (Agent-Executed QA only)
- **Framework**: N/A
- **Agent-Executed QA**: ALWAYS (mandatory for all tasks)

### QA Policy
Every task includes agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Frontend/UI**: Use Playwright — Navigate, interact, assert DOM, screenshot
- **TUI/CLI**: Use interactive_bash (tmux) — Run command, validate output
- **API/Backend**: Use Bash (curl) — Send requests, assert response

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation - hash & cache):
├── Task 1: Modify hash-utils.ts for pure hash IDs [quick]
├── Task 2: Refactor element-cache.ts for tab-scoped cache [quick]
├── Task 3: Update element-actions.ts cache lookups [quick]
└── Task 4: Update types.ts comments [quick]

Wave 2 (Extension handlers):
├── Task 5: Update highlight_elements handler [quick]
├── Task 6: Add screenshot to tab operations [quick]
├── Task 7: Add screenshot to JavaScript execute [quick]
└── Task 8: Update element command handlers for tab_id [quick]

Wave 3 (Server side):
├── Task 9: Add tab_id to Python command models [quick]
├── Task 10: Update OpenBrowserAction with tab_id [quick]
├── Task 11: Pass tab_id to element commands [quick]
├── Task 12: Extract screenshots from tab/JS responses [quick]
└── Task 13: Update tool documentation [writing]

Wave 4 (Verification):
├── Task 14: Extension build & typecheck [quick]
└── Task 15: Integration QA [unspecified-high]

Critical Path: Task 1 → Task 2 → Task 3 → Task 5 → Task 9 → Task 14 → Task 15
Parallel Speedup: ~60% faster than sequential
Max Concurrent: 8 (Wave 1 & 2)
```

### Dependency Matrix
- **1-4**: — — 5-8
- **5**: 1, 2 — 14, 15
- **6-7**: — — 12, 14, 15
- **8**: 2, 3 — 14, 15
- **9**: — — 10, 11
- **10-12**: 9 — 14, 15
- **13**: — — 14
- **14**: 1-13 — 15
- **15**: 14 — —

### Agent Dispatch Summary
- **Wave 1**: 4 quick tasks
- **Wave 2**: 4 quick tasks
- **Wave 3**: 5 tasks (4 quick + 1 writing)
- **Wave 4**: 2 tasks (1 quick + 1 unspecified-high)

---

## TODOs

