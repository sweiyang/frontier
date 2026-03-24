# Frontier — Agent Teams & Phased Task List

> **Objective:** Close loose ends, harden the codebase, and refine UX.
> No new features. No CI/CD. No infra/ops work.

---

## Agent Teams

### Team 1 — Backend Hardening

**Focus:** Error handling, input validation, security loopholes, code consistency.

| Role | Agent Type | Scope |
|------|-----------|-------|
| Lead | `general-purpose` | Orchestrates fixes across backend modules, resolves cross-cutting concerns |
| Security Auditor | `Explore` → `general-purpose` | Identifies and patches SQL injection risks, auth bypass, credential exposure |
| Validator | `general-purpose` | Adds Pydantic validators, enum constraints, and input sanitization |

**Key files in scope:**

```
src/core/config.py              # Hardcoded app_env, weak default JWT secret
src/core/db/db.py               # f-string SQL in schema ops
src/core/db/db_chat.py          # f-string SQL in ALTER TABLE, conversation isolation
src/core/db/db_project.py       # Inconsistent session/rollback patterns
src/core/auth/auth.py           # LDAP connection leak, no pool cleanup
src/core/agent/base_connector.py        # No HTTPS enforcement for credentials
src/core/agent/connectors/*.py          # Timeout handling, error recovery
src/core/approval/approval_service.py   # Broad except blocks, transaction isolation
src/api/schema.py               # Duplicate validation fn, missing enums/constraints
src/api/routers/*.py            # Mixed error response formats (JSONResponse vs HTTPException)
src/api/services/chat_service.py        # Swallowed exceptions
```

---

### Team 2 — Frontend UX Refinement

**Focus:** Loading/error/empty states, alert() cleanup, form validation, styling consistency.

| Role | Agent Type | Scope |
|------|-----------|-------|
| Lead | `general-purpose` | Coordinates UX fixes across all Svelte components |
| UX Polisher | `general-purpose` | Replaces `alert()` calls with toast notifications, adds missing states |
| Style Auditor | `Explore` → `general-purpose` | Finds and replaces hardcoded colors/spacing with CSS variables |

**Key files in scope:**

```
src/frontend/src/lib/ChatArea.svelte          # alert() on upload errors, missing error recovery
src/frontend/src/lib/ProjectSettings.svelte   # Silent error suppression, missing form feedback
src/frontend/src/lib/AgentManager.svelte      # alert() for JSON errors, no field validation
src/frontend/src/lib/ChangeRequests.svelte    # alert() for approve/reject, no in-progress state
src/frontend/src/lib/SiteBuilder.svelte       # Hardcoded colors, incomplete save error handling
src/frontend/src/lib/SiteRenderer.svelte      # Bare catch {} blocks, no user feedback
src/frontend/src/lib/CreateProject.svelte     # Validation only on input, not on submit
src/frontend/src/lib/ComponentPreview.svelte  # No retry on failed table fetch
src/frontend/src/lib/Login.svelte             # Hardcoded rgba values, disabled "Forgot password"
src/frontend/src/lib/Sidebar.svelte           # Inline agent color styles
src/frontend/src/lib/DynamicPanel.svelte      # a11y suppression pragmas
```

---

### Team 3 — Accessibility & Semantics

**Focus:** ARIA attributes, keyboard navigation, semantic HTML, color contrast.

| Role | Agent Type | Scope |
|------|-----------|-------|
| Lead | `general-purpose` | Audits and fixes accessibility across all components |
| A11y Reviewer | `Explore` | Scans for missing aria-labels, role misuse, keyboard traps |

**Key files in scope:**

```
src/frontend/src/lib/SiteBuilder.svelte       # Canvas drag targets need roles/aria
src/frontend/src/lib/Sidebar.svelte           # Dropdown keyboard navigation missing
src/frontend/src/lib/ChangeRequests.svelte    # Modal aria-modal, Escape key handling
src/frontend/src/lib/Workbench.svelte         # div[role="button"] → <button>
src/frontend/src/lib/DynamicPanel.svelte      # a11y-click/a11y-no-static-element suppressed
src/frontend/src/lib/ProjectSettings.svelte   # Label-input associations missing
src/frontend/src/lib/AgentManager.svelte      # Dynamic field labels
```

---

### Team 4 — Test Coverage

**Focus:** Fill critical test gaps for existing code. No new features to test.

| Role | Agent Type | Scope |
|------|-----------|-------|
| Lead | `general-purpose` | Plans test strategy, writes integration-style tests |
| Backend Tester | `general-purpose` | Unit tests for untested core modules |
| Frontend Tester | `general-purpose` | Component and utility tests via Vitest |

**Current state (baseline):**

| Layer | Test Files | Source Files | Coverage Estimate |
|-------|-----------|-------------|-------------------|
| Backend | 7 files (546 LOC) | 33+ modules (~8k LOC) | ~7% |
| Frontend | 3 files (410 LOC) | 24 components + 7 utils | ~10% |

**Priority untested modules:**

```
# Backend — critical paths with zero tests
src/core/approval/approval_service.py    # 579 lines — approval workflow
src/core/agent/connectors/*.py           # All 3 connectors — streaming, auth, errors
src/api/routers/agents.py               # Agent CRUD endpoints
src/api/routers/approval.py             # Approval endpoints (293 lines)
src/api/services/chat_service.py        # Chat streaming service
src/core/db/db_chat.py                  # 430 lines — conversation/message ops

# Frontend — zero Svelte component tests exist
src/frontend/src/lib/ChatArea.svelte     # Core chat interface
src/frontend/src/lib/AgentManager.svelte # Agent config forms
src/frontend/src/lib/CreateProject.svelte # Project creation flow
src/frontend/src/lib/ActionExecutor.js   # Action execution logic
src/frontend/src/lib/favorites.js        # Favorites store
src/frontend/src/lib/theme.js            # Theme handling
```

---

### Team 5 — Dead Code & Consistency Cleanup

**Focus:** Remove dead code, fix duplicates, standardize patterns.

| Role | Agent Type | Scope |
|------|-----------|-------|
| Cleanup Agent | `general-purpose` | Removes dead code, fixes duplicates, standardizes patterns |

**Known items:**

```
src/api/schema.py                 # Duplicate _validate_project_name() (lines 46-75)
src/frontend/src/lib/ChatArea.svelte    # hasNotifiedCollapse never set to true
src/frontend/src/lib/ChatArea.svelte    # currentAgentColor assigned but unused
src/frontend/src/lib/Chat.svelte        # hasNotifiedCollapse dead state variable
src/api/routers/*.py              # Standardize error responses to HTTPException only
src/core/db/db_project.py         # Standardize session close/rollback patterns
```

---

## Phased Execution Plan

### Phase 1 — Critical Fixes (Security & Stability)

> **Goal:** Patch anything that could cause data loss, auth bypass, or silent failures.
> **Teams:** Backend Hardening (lead), Dead Code Cleanup (support)
> **Estimated tasks:** 12

| # | Task | File(s) | Team |
|---|------|---------|------|
| 1.1 | Fix hardcoded `app_env` — read from `APP_ENV` env var with fallback | `src/core/config.py:116-117` | Backend |
| 1.2 | Replace f-string SQL with parameterized queries in schema operations | `src/core/db/db.py:98,108,160` | Backend |
| 1.3 | Replace f-string SQL in ALTER TABLE migration | `src/core/db/db_chat.py:165` | Backend |
| 1.4 | Add HTTPS enforcement when agent auth credentials are present | `src/core/agent/base_connector.py:28-37` | Backend |
| 1.5 | Fix LDAP connection pool — add cleanup on error, TTL, and `finally` blocks | `src/core/auth/auth.py:36,48-49` | Backend |
| 1.6 | Replace broad `except Exception` blocks with specific exceptions + logging | `src/core/approval/approval_service.py` | Backend |
| 1.7 | Fix swallowed exception in usage event recording | `src/api/services/chat_service.py:131-132` | Backend |
| 1.8 | Add HTTP timeout defaults to HTTP connector | `src/core/agent/connectors/http_connector.py` | Backend |
| 1.9 | Remove duplicate `_validate_project_name()` definition | `src/api/schema.py:46-75` | Cleanup |
| 1.10 | Standardize DB session close/rollback to `try/finally` pattern | `src/core/db/db_project.py`, `approval_service.py` | Backend |
| 1.11 | Add transaction boundaries to approval check-and-apply flow | `src/core/approval/approval_service.py` | Backend |
| 1.12 | Warn on default JWT secret at startup (log.warning) | `src/core/config.py:161` | Backend |

---

### Phase 2 — Input Validation & API Consistency

> **Goal:** Tighten all inputs, standardize API error contracts.
> **Teams:** Backend Hardening (lead)
> **Estimated tasks:** 10

| # | Task | File(s) | Team |
|---|------|---------|------|
| 2.1 | Add URL format validator to agent endpoint fields | `src/api/schema.py` (AgentCreate, AgentUpdate) | Backend |
| 2.2 | Add `connection_type` enum constraint (`http`, `langgraph`, `openai`) | `src/api/schema.py:134` | Backend |
| 2.3 | Add max length constraint to `ChatRequest.message` | `src/api/schema.py:17` | Backend |
| 2.4 | Add base64 format + size validation to `FileAttachment.data` | `src/api/schema.py:8-12` | Backend |
| 2.5 | Add LDAP DN format validation to `ADGroupCreate.group_dn` | `src/api/schema.py:189-190` | Backend |
| 2.6 | Add `approval_type` enum constraint (`any`, `all`, `majority`) | `src/api/schema.py` | Backend |
| 2.7 | Standardize all error responses to `HTTPException` (remove `JSONResponse` errors) | `src/api/routers/projects.py`, all routers | Backend |
| 2.8 | Add project existence check before operations in chat router | `src/api/routers/chat.py:37` | Backend |
| 2.9 | Add null-safe `ctx.user` checks before accessing `user_id` | `src/api/routers/agents.py:56-57` | Backend |
| 2.10 | Add conversation ownership enforcement (user can only query own conversations) | `src/core/db/db_chat.py` | Backend |

---

### Phase 3 — UX Refinement & Error Feedback

> **Goal:** Replace all `alert()` calls, add loading/error/empty states, fix form validation.
> **Teams:** Frontend UX (lead)
> **Estimated tasks:** 14

| # | Task | File(s) | Team |
|---|------|---------|------|
| 3.1 | Create a reusable `<Toast>` notification component | New: `src/frontend/src/lib/Toast.svelte` | UX |
| 3.2 | Replace `alert()` in ChatArea with toast notifications | `ChatArea.svelte:162,169` | UX |
| 3.3 | Replace `alert()` in AgentManager with in-form error display | `AgentManager.svelte:184-192` | UX |
| 3.4 | Replace `alert()` in ChangeRequests with toast + in-progress button state | `ChangeRequests.svelte:86-90,109-113` | UX |
| 3.5 | Replace `alert()` in ProjectSettings with contextual error messages | `ProjectSettings.svelte` | UX |
| 3.6 | Add error recovery UI for failed message streams in ChatArea | `ChatArea.svelte:281` | UX |
| 3.7 | Replace bare `catch {}` blocks with error logging + user feedback | `SiteRenderer.svelte:104,139`, `Dashboard.svelte:48` | UX |
| 3.8 | Replace `.catch(() => ({}))` with proper error handling | `ProjectSettings.svelte:240` | UX |
| 3.9 | Add `accept` attribute to file input for allowed types | `ChatArea.svelte:100` | UX |
| 3.10 | Add HTML5 validation attributes to CreateProject form | `CreateProject.svelte:103` | UX |
| 3.11 | Add endpoint URL validation to AgentManager form | `AgentManager.svelte` | UX |
| 3.12 | Add confirmation dialog before removing approvers/members | `ProjectSettings.svelte` | UX |
| 3.13 | Add retry mechanism for failed table data fetches | `ComponentPreview.svelte:121-127` | UX |
| 3.14 | Add loading spinner for initial SiteBuilder site load | `SiteBuilder.svelte` | UX |

---

### Phase 4 — Styling Consistency & Accessibility

> **Goal:** Replace all hardcoded colors with CSS variables, fix semantic HTML and ARIA.
> **Teams:** Accessibility (lead), Frontend UX (support)
> **Estimated tasks:** 12

| # | Task | File(s) | Team |
|---|------|---------|------|
| 4.1 | Replace hardcoded hex colors in SiteBuilder with CSS variables | `SiteBuilder.svelte:266,1070` | A11y |
| 4.2 | Replace hardcoded `AGENT_COLORS` array with CSS variable references | `ChatArea.svelte:57` | A11y |
| 4.3 | Replace inline `rgba()` orb backgrounds with CSS variable + opacity | `Login.svelte:224-227,309` | A11y |
| 4.4 | Replace inline agent icon `background` with CSS class | `Sidebar.svelte:215` | A11y |
| 4.5 | Replace `div[role="button"]` with semantic `<button>` elements | `Workbench.svelte:149,97` | A11y |
| 4.6 | Add `aria-label`, `aria-expanded`, `aria-haspopup` to dropdowns | `Sidebar.svelte:93-98`, `ModelSelector.svelte` | A11y |
| 4.7 | Add `aria-modal`, `aria-label`, Escape key handler to modals | `ChangeRequests.svelte:252,256` | A11y |
| 4.8 | Add keyboard arrow-key navigation to search dropdown | `Sidebar.svelte:268-287` | A11y |
| 4.9 | Add drag-drop ARIA roles and live region announcements | `SiteBuilder.svelte` canvas | A11y |
| 4.10 | Fix label-input `for` associations on all form fields | `ProjectSettings.svelte`, `AgentManager.svelte` | A11y |
| 4.11 | Remove a11y suppression pragmas and fix underlying issues | `DynamicPanel.svelte:208-209` | A11y |
| 4.12 | Audit and fix color contrast on disabled/secondary states | All components with `opacity: 0.6` patterns | A11y |

---

### Phase 5 — Test Coverage & Dead Code Cleanup

> **Goal:** Bring test coverage to meaningful levels on critical paths. Remove dead code.
> **Teams:** Test Coverage (lead), Dead Code Cleanup (support)
> **Estimated tasks:** 14

| # | Task | File(s) | Team |
|---|------|---------|------|
| 5.1 | Remove `hasNotifiedCollapse` dead variable | `ChatArea.svelte:35`, `Chat.svelte:35` | Cleanup |
| 5.2 | Remove unused `currentAgentColor` assignment | `ChatArea.svelte:53` | Cleanup |
| 5.3 | Remove 29 fragile `pytest.skip()` guards — fix imports properly | `tests/*.py` | Tests |
| 5.4 | Write unit tests for approval_service (happy path + edge cases) | `tests/test_approval_service.py` | Tests |
| 5.5 | Write unit tests for all 3 agent connectors (stream, auth, error) | `tests/test_connectors.py` | Tests |
| 5.6 | Write unit tests for chat_service (stream success, failure, cleanup) | `tests/test_chat_service.py` | Tests |
| 5.7 | Write unit tests for version_service (create, rollback, list) | `tests/test_version_service.py` | Tests |
| 5.8 | Write API tests for agents router (CRUD, validation, auth) | `tests/test_api_agents.py` | Tests |
| 5.9 | Write API tests for approval router (create, approve, reject, self-approve) | `tests/test_api_approval.py` | Tests |
| 5.10 | Write API tests for chat router (send, stream, conversation isolation) | `tests/test_api_chat.py` | Tests |
| 5.11 | Write frontend tests for CreateProject form validation | `src/frontend/src/tests/create-project.test.js` | Tests |
| 5.12 | Write frontend tests for AgentManager form validation | `src/frontend/src/tests/agent-manager.test.js` | Tests |
| 5.13 | Write frontend tests for ActionExecutor logic | `src/frontend/src/tests/action-executor.test.js` | Tests |
| 5.14 | Write frontend tests for favorites and theme utilities | `src/frontend/src/tests/favorites.test.js`, `theme.test.js` | Tests |

---

## Execution Summary

| Phase | Name | Teams | Tasks | Can Parallelize With |
|-------|------|-------|-------|---------------------|
| **1** | Critical Fixes | Backend, Cleanup | 12 | — |
| **2** | Input Validation | Backend | 10 | Phase 3, 4 |
| **3** | UX Refinement | Frontend UX | 14 | Phase 2, 4 |
| **4** | Accessibility | A11y, Frontend UX | 12 | Phase 2, 3 |
| **5** | Tests & Cleanup | Tests, Cleanup | 14 | After Phases 1-4 |
| | **Total** | | **62** | |

### Parallelization Strategy

```
Timeline:

Phase 1  ████████████████                          ← Sequential (security-first)
Phase 2       ████████████████                     ← Start after 1.1-1.3
Phase 3       ████████████████                     ← Parallel with Phase 2
Phase 4       ████████████████                     ← Parallel with Phase 2 & 3
Phase 5                        ████████████████    ← After all code changes stabilize
```

### Claude Code Orchestration Notes

Each task is scoped to specific files and line numbers. To execute:

1. **Spawn one agent per team** — each works its file list independently
2. **Phase 1 is blocking** — complete before spawning Phase 2-4 agents
3. **Phases 2, 3, 4 run in parallel** — no file overlap between teams
4. **Phase 5 runs last** — tests validate all prior changes
5. **Use `Explore` agents first** when a task says "audit" or "scan" — then hand off to `general-purpose` for the fix
6. **Use `isolation: "worktree"`** for test-writing agents to avoid conflicts with code-change agents
