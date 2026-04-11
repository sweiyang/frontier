# Frontier Frontend Functional Test Coverage Review

## Review Context

- Review target: `testcase_en.md`
- Review basis: current frontend actually served by the standard startup path (`docker compose up -d --build`)
- Current frontend shape reviewed against the live code includes: Login, Dashboard, Sidebar, TopBar, NotificationBanner, ChatArea, ModelSelector, Artefacts, Workbench, ProjectSettings, AgentManager, ChangeRequests, AdminPanel, ContactUs, SiteRenderer

## Overall Conclusion

The current test suite is **partially suitable**.

- It still covers the traditional core paths well: login, create project, chat send, model selector, artefact click-through, workbench project management, project settings, agent management, and approval flow.
- It is **not yet sufficient** for the current frontend actually being served now, because the current UI has a richer home/dashboard flow, favorites, top bar interactions, notification banners, direct URL fallback handling, and site/chat dual-view behavior that are either not covered at all or are only indirectly covered.

## Cases That Are No Longer Fully Appropriate

| ID | Current Issue | Why It No Longer Matches Current Frontend | Recommended Update |
| --- | --- | --- | --- |
| FE-FUNC-001 | Expected result says login switches to `chat view` | The current app can land on the global Dashboard/home state, restore a preserved route, or enter a project route depending on URL and state | Change the expected result to: authenticated state is established, token is stored, and the user lands on the correct post-login route (home/dashboard, restored route, or project route) |
| FE-FUNC-004 | Expected result says the new project appears in `project list or sidebar` | Current create-project success flow returns to Workbench project list, not directly to sidebar navigation | Change the expected result to: create form closes, route returns to Workbench, and the new project appears in the Workbench project list |
| FE-FUNC-021 | Only validates clicking an artefact card | Current Artefacts page also has loading, retry, empty-state, and search behavior | Keep this case for click-through, but split page-state coverage into separate cases |
| FE-FUNC-024 | Too generic for current Project Settings page | Current General settings now include `description`, `logo`, `default_view`, and `view_locked`, each with visible downstream impact | Expand this case or split it so those fields and their effects are explicitly validated |
| FE-FUNC-041 | Too generic for current 403 handling | Current app has route-level forbidden handling with dedicated fallback behavior, not just generic operation blocking | Extend expected result to include access-denied messaging/fallback behavior where applicable |

## Coverage Gaps For The Current Frontend

### 1. Dashboard / Home Flow Is Missing

The new frontend has a real global home/dashboard, not just direct chat entry.

Missing coverage:

- Root-path landing behavior when no project or agent is selected
- Dashboard all-agents list loading from `/me/agents`
- Dashboard search behavior
- Dashboard sort behavior
- Dashboard card click routing to project + agent context
- Dashboard empty state when no accessible agents exist

### 2. Favorites Are Not Covered

The current frontend has a favorites system used in both Dashboard and Sidebar.

Missing coverage:

- Favorite/unfavorite an agent from Dashboard
- Favorite ordering priority on Dashboard
- Favorite persistence via localStorage after refresh
- Favorite section rendering in Sidebar
- Clicking a favorited agent from Sidebar

### 3. Top Bar Interactions Are Not Covered

The current frontend has more top-bar behavior than the old suite reflects.

Missing coverage:

- Breadcrumb home navigation back to Dashboard
- Sidebar collapse toggle
- Theme toggle behavior
- Theme persistence after refresh/login restore
- User info / project description display

### 4. Notification Banners Are Not Covered

The current frontend now includes announcement banners and a bell panel.

Missing coverage:

- Banner rendering when active banners exist
- Multi-banner carousel navigation
- Dismiss behavior
- Restore behavior from bell panel
- Dismiss persistence via localStorage
- Banner link behavior

### 5. Site/Chat Dual-View Behavior Is Not Covered

The current frontend is not chat-only anymore. It supports project site rendering and site/chat switching.

Missing coverage:

- Project landing in `site` mode when the project default view is site
- View switcher behavior between Site and Chat
- `view_locked` disabling the switcher
- Project site rendering through `SiteRenderer`
- Fullscreen site behavior when configured
- Workbench `View Site` button from a project card

Note:

- Excluding SiteBuilder editing is still reasonable.
- Excluding **site rendering and site/chat navigation** is no longer reasonable for the current frontend.

### 6. Direct URL / Fallback Handling Is Not Covered

The current frontend includes route parsing and explicit fallback UX for invalid or unauthorized project URLs.

Missing coverage:

- Direct visit to `/{project}` with a valid project
- Direct visit to `/{project}?agent={id}` deep link
- Invalid project route shows `Project not found`
- Unauthorized project route shows `Access denied`
- Fallback behavior after dismissing those dialogs

### 7. Artefacts Page State Coverage Is Incomplete

The current suite only covers artefact navigation after the list is already loaded.

Missing coverage:

- Artefacts loading state
- Artefacts empty state
- Artefacts search filtering
- Artefacts network error state
- Artefacts retry button behavior

### 8. AdminPanel Is Uncovered

The current frontend includes an AdminPanel, but the test suite does not cover it.

Missing coverage:

- Platform admin access to AdminPanel
- Workbench access grant creation/removal
- Admin project list loading
- Admin banner creation / deletion / toggle
- Admin project deletion flow if considered in-scope for frontend validation

### 9. Contact Support Was Trimmed Too Aggressively

The current frontend still exposes ContactUs from Login and Sidebar.

Impact:

- Removing the old ContactUs case means a visible user-facing entry point is now untested

Recommendation:

- Reintroduce at least one smoke test for opening and closing ContactUs from Login or Sidebar

### 10. Some Current Behaviors Are Under-Specified Rather Than Fully Missing

These cases are still useful, but should be strengthened:

- FE-FUNC-019 should also validate the current stream-error retry affordance if retry is expected UX
- FE-FUNC-024 should explicitly cover logo upload, default view, and view lock
- FE-FUNC-031 should consider current AgentManager behaviors such as preset logos and artefact toggle when relevant
- FE-FUNC-022 should distinguish `no manageable projects` from `no Workbench access`

## Suggested New Cases To Add

| Suggested ID | Module | Priority | Proposed Test Case |
| --- | --- | --- | --- |
| FE-FUNC-047 | Dashboard | P0 | Root path loads global Dashboard when no project/agent context is active |
| FE-FUNC-048 | Dashboard | P1 | Dashboard search, sorting, and empty-state behavior |
| FE-FUNC-049 | Dashboard / Sidebar | P1 | Favorite/unfavorite agents and persist favorites after refresh |
| FE-FUNC-050 | TopBar | P1 | Breadcrumb home navigation and sidebar toggle |
| FE-FUNC-051 | Theme | P1 | Theme toggle persists across refresh or restored session |
| FE-FUNC-052 | Notification Banner | P1 | Banner dismiss/restore and multi-banner rotation |
| FE-FUNC-053 | Routing | P0 | Direct project deep link (`/{project}` and `?agent=`) resolves to correct context |
| FE-FUNC-054 | Routing / Auth | P0 | Invalid or unauthorized project URL shows the correct fallback modal |
| FE-FUNC-055 | Site / Chat Views | P0 | Site/chat switcher respects `default_view` and `view_locked` |
| FE-FUNC-056 | Workbench | P1 | `View Site` button on a project card opens the published site route |
| FE-FUNC-057 | Artefacts | P1 | Artefacts search, empty state, network error, and retry |
| FE-FUNC-058 | AdminPanel | P1 | Workbench access grant management UI |
| FE-FUNC-059 | AdminPanel / Banner | P1 | Admin announcement banner creation and visibility loop |
| FE-FUNC-060 | ContactUs | P2 | Open and close ContactUs modal from a visible entry point |

## Recommended Action

Recommended disposition for the current suite:

- Keep the current 30 cases as the baseline for classic login/chat/workbench/approval coverage
- Update the outdated expectations in FE-FUNC-001, FE-FUNC-004, FE-FUNC-021, FE-FUNC-024, and FE-FUNC-041
- Add a second small expansion set focused on Dashboard, favorites, notification banners, route fallback handling, site/chat switching, Artefacts page states, and AdminPanel

## Short Verdict

If the goal is to validate the **current frontend that is now correctly started**, the present suite is **not enough by itself**.

- It is still a useful base.
- It does **not yet fully represent the new home/dashboard-first and site-enabled frontend behavior**.