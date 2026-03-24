# Frontier Codebase Issues

Comprehensive scan performed 2026-03-23. Issues organized by severity and category.

---

## Critical / High Severity

### 1. Hardcoded `app_env = "prod"`
- **File:** `src/core/config.py` (lines 114-117)
- **Type:** Configuration / Logic bug
- **Description:** The `app_env` property always returns `"prod"` — the line reading `APP_ENV` is commented out. This forces production behavior everywhere (approval workflows, stricter validation) even in development.

### 2. Class-level mutable state in AgentManager
- **File:** `src/core/agent/agent_manager.py` (line 22)
- **Type:** Bug / Thread safety
- **Description:** `agents = {}` is a class variable shared across all instances. In a concurrent FastAPI app, this causes race conditions — one request may overwrite or read stale agent data from another.

### 3. Hardcoded default JWT secret
- **File:** `src/core/config.py` (line 161)
- **Type:** Security
- **Description:** Falls back to `"frontier-dev-secret-key-change-in-production"` if no secret is configured. If config is missing this key, all JWTs use a guessable secret.

### 4. Admin credentials stored as plain text in config
- **File:** `src/core/config.py` (lines 246-251)
- **Type:** Security
- **Description:** `admin.username` and `admin.password` are loaded directly from YAML config. No support for environment variables or secrets management for these values.

---

## Medium Severity

### 5. Approval defaults to enabled
- **File:** `src/core/config.py` (lines 274-280)
- **Type:** Logic bug
- **Description:** `approval_enabled` defaults to `True` when unconfigured. Combined with issue #1 (hardcoded prod), approval workflows are always active — even in development.

### 6. SQL injection risk in schema search_path
- **File:** `src/core/db/db.py` (lines 101-109)
- **Type:** Security
- **Description:** `_set_search_path()` uses f-string interpolation: `cursor.execute(f"SET search_path TO {schema}, public")`. This bypasses SQLAlchemy's parameterization.

### 7. Missing database indexes
- **File:** `src/core/db/`
- **Type:** Performance
- **Description:** No indexes on frequently queried columns: `{project}_conversation.user_id`, `{project}_messages.conversation_id`, `projects.project_name`, `agents.project_id`. Will degrade with scale.

### 8. No database connection pool tuning
- **File:** `src/core/db/db.py` (lines 80-84)
- **Type:** Performance / Reliability
- **Description:** Only `pool_pre_ping` and `pool_recycle` are set. Missing `pool_size` and `max_overflow` — defaults (size=5) are insufficient for concurrent production use.

### 9. Global mutable state in db_chat.py
- **File:** `src/core/db/db_chat.py` (lines 50, 131)
- **Type:** Thread safety
- **Description:** Module-level dicts `_project_tables` and `_ensured_projects` cache table classes. Could cause issues under concurrency or if projects are deleted and recreated.

### 10. Broad exception handling (multiple locations)
- **Type:** Code quality
- **Locations:**
  - `src/core/db/db_project.py` line 704 — bare `except Exception` swallows table deletion errors
  - `src/core/db/db_project.py` line 1559 — `except Exception: pass` silently ignores analytics errors
  - `src/api/static/spa.py` lines 34-36 — generic catch masks SPA serving failures
  - `src/core/agent/connectors/langgraph_connector.py` lines 80-82 — silently empties assistant list on error

### 11. Unhandled promise rejections in frontend
- **File:** `src/frontend/src/lib/ChatArea.svelte` (lines 67-81)
- **Type:** Bug / Error handling
- **Description:** `authFetch().then().then()` chain has no `.catch()`. Network errors produce unhandled rejections with no user feedback.

### 12. Silent catch blocks in frontend
- **Type:** Error handling
- **Locations:**
  - `src/frontend/src/lib/SiteRenderer.svelte` line 104 — empty `catch {}` on form submission
  - `src/frontend/src/lib/siteAnalytics.js` line 47 — `.catch(() => {})` hides analytics errors
  - `src/frontend/src/lib/markdown.js` line 22 — `catch (__) {}` hides syntax highlighting failures

### 13. Accessibility: suppressed warnings instead of fixes
- **Type:** Accessibility
- **Locations:**
  - `src/frontend/src/App.svelte` lines 462-488 — `svelte-ignore` on click events without keyboard handlers
  - `src/frontend/src/lib/DynamicPanel.svelte` lines 188-189 — same pattern
  - `src/frontend/src/lib/ContactUs.svelte` lines 43-44 — same pattern

### 14. Accessibility: empty alt text on meaningful images
- **Type:** Accessibility
- **Locations:**
  - `src/frontend/src/lib/Artefacts.svelte` line 103 — agent icon `alt=""`
  - `src/frontend/src/lib/AgentManager.svelte` line 584 — agent icon `alt=""`
  - `src/frontend/src/lib/Sidebar.svelte` line 157 — company logo `alt=""`
  - `src/frontend/src/lib/ChatArea.svelte` line 489 — assistant avatar `alt=""`

### 15. No API rate limiting
- **File:** `src/api/`
- **Type:** Security
- **Description:** No rate limiting on any endpoint. Vulnerable to abuse and denial-of-service.

### 16. Missing PyYAML dependency
- **File:** `pyproject.toml`
- **Type:** Dependency
- **Description:** `pyyaml` is not listed in dependencies, but `src/core/config.py` imports it. Config loading fails if a YAML file is present and PyYAML isn't installed separately.

### 17. Outdated documentation: SQLite still listed as supported
- **File:** `docs/ard/DATABASE_SCHEMA.md` (lines 5-9)
- **Type:** Documentation
- **Description:** States SQLite is the default, but `src/core/db/db.py` explicitly rejects it. Users following docs will hit errors.

---

## Low Severity

### 18. Deprecated `datetime.utcnow()` usage
- **File:** `src/core/db/db_chat.py` (lines 21, 43, 90-91, 122, 381)
- **Type:** Deprecation
- **Description:** Uses timezone-naive `datetime.utcnow()`. Python 3.12+ warns; should use `datetime.now(datetime.UTC)`.

### 19. WebSocket connector raises NotImplementedError
- **File:** `src/core/agent/connectors/__init__.py` (lines 38-39)
- **Type:** Incomplete implementation
- **Description:** `connection_type == "websocket"` raises `NotImplementedError` at runtime with no guard in the UI.

### 20. Missing frontend build fallback
- **File:** `src/core/frontend/frontend.py` (lines 28-30)
- **Type:** Code quality
- **Description:** `get_build_dir()` has a `pass` where a warning should go: "Fallback or warning could go here." No feedback when the frontend isn't built.

### 21. `console.log` left in production code
- **File:** `src/frontend/src/lib/ChatArea.svelte` (line 370)
- **Type:** Code quality
- **Description:** `console.log("frontend enabled: ", frontendEnabled)` — debug statement left in.

### 22. Unsafe `window.open()` without URL validation
- **Type:** Security
- **Locations:**
  - `src/frontend/src/lib/SiteRenderer.svelte` lines 71-72
  - `src/frontend/src/lib/ActionExecutor.js` line 24
  - `src/frontend/src/lib/ContactUs.svelte` lines 24, 30
- **Description:** Opens URLs from user-provided props without schema validation. Potential `javascript:` protocol attack vector.

### 23. Deprecated project-level artefact fields
- **File:** `src/core/db/db_project.py` (lines 46-47, 1591-1625)
- **Type:** Technical debt
- **Description:** `is_artefact` and `artefact_visibility` on the Project model are marked DEPRECATED but still present. Old methods `set_artefact()` and `list_artefacts()` remain.

### 24. Outdated `connection_type` values in docs
- **File:** `docs/ard/DATABASE_SCHEMA.md` (line 236)
- **Type:** Documentation
- **Description:** Lists "http, websocket, grpc" but actual code uses "http, langgraph, openai".

### 25. Missing test dependencies in pyproject.toml
- **File:** `pyproject.toml`
- **Type:** Dependency
- **Description:** No test dependencies listed (pytest, pytest-asyncio, etc.). Tests won't run without manual installation.

### 26. Low test coverage
- **File:** `tests/`
- **Type:** Testing
- **Description:** Only ~546 lines across 6 test files. No coverage for: agent connectors, approval workflows, chat streaming, LDAP auth, site builder, RBAC permissions, or schema migration.

### 27. No input size validation on messages
- **File:** `src/core/db/db_chat.py` (lines 352-405)
- **Type:** Validation
- **Description:** Message `content` stored as TEXT with no size limit. No protection against excessively large payloads.

### 28. Insecure defaults in config.yaml.example
- **File:** `config.yaml.example` (lines 18, 30, 62)
- **Type:** Security
- **Description:** Placeholder credentials like `password` and `change-this-in-production` could be used as-is in production.
