# Frontier Frontend High-Priority Functional Test Cases

## Scope

- Type: High-priority functional UI test cases
- Basis: Current frontend actually served by the standard startup flow (`docker compose up -d --build`)
- Focus: Highest-value user flows and robustness paths for the current dashboard-first, project-aware frontend
- Exclusions: Performance benchmarking, SiteBuilder editing features, low-priority cosmetic behavior
- Included modules: Login, route bootstrap, Dashboard, Sidebar, Workbench, Project Settings, AgentManager, ChatArea, ModelSelector, Artefacts, ChangeRequests

## Design Rules

- Each test case validates one core assertion only
- Steps are limited to 3-8 actions
- Expected results are objective and observable
- Preconditions state exact system and data conditions
- Robustness scenarios are explicitly included
- Descriptions focus on interaction logic, not brittle pixel-level UI details

## Status Definitions

- Draft: Test case defined but not yet executed
- Pass: Executed and matches expected result
- Fail: Executed but does not match expected result
- Blocked: Cannot be executed due to environment, data, or dependency constraints

---

## Module 1: Authentication & Route Bootstrap (6 cases)

| ID | Module | Priority | Preconditions | Test Case | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FE-HP-001 | Login | P0 | User is on `/`; backend `/login` and `/me` are reachable; valid account exists | Successful login from root path | 1. Open the login page at `/`. 2. Enter valid username and password. 3. Click Sign In. | `access_token` is written to localStorage; authenticated shell loads successfully; page leaves login state and enters the authenticated home flow without a blank screen or unhandled error. | Draft |
| FE-HP-002 | Login | P0 | User is on the login page; invalid credentials are available | Invalid credentials handling | 1. Enter an invalid username or password. 2. Click Sign In. 3. Observe the form state. | Login remains on the same page; an explicit error message is shown; no token is written to localStorage. | Draft |
| FE-HP-003 | Auth / Global | P0 | User is logged in; replace `frontier_access_token` in localStorage with an invalid string | 401 interception forces logout | 1. Corrupt the stored token in DevTools. 2. Trigger any authenticated action such as opening Workbench or creating a new chat. 3. Observe the app response. | Frontend clears the invalid token, ends the authenticated session, and returns to the login page with no white screen or uncaught exception. | Draft |
| FE-HP-004 | Routing / Login | P0 | Valid account exists; target project exists and is accessible; open browser at `/{project_name}?agent={agent_id}` while logged out | Deep link is preserved across login | 1. Open a valid project deep link while logged out. 2. Log in with valid credentials. 3. Wait for the authenticated route to resolve. | App lands in the target project context; the target Agent is selected; route is not reset to an unrelated page. | Draft |
| FE-HP-005 | Routing / Global | P0 | User is logged in; no project with name `missing-project-xyz` exists | Invalid project route fallback | 1. Manually open `/missing-project-xyz`. 2. Wait for route validation to finish. 3. Dismiss the fallback dialog. | App shows a deterministic `Project not found` dialog; no stale project content is rendered underneath; after dismissal the user is redirected to the configured fallback route or root route. | Draft |
| FE-HP-006 | Routing / Global | P0 | User is logged in; a project exists but the current account has no access to it | Unauthorized project route fallback | 1. Manually open a project URL that the current account cannot access. 2. Wait for route validation to finish. 3. Dismiss the fallback dialog. | App shows a deterministic `Access denied` dialog; unauthorized project content is not rendered; after dismissal the user lands on the configured fallback route or root route. | Draft |

## Module 2: Dashboard & Global Navigation (5 cases)

| ID | Module | Priority | Preconditions | Test Case | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FE-HP-007 | Dashboard | P0 | User is logged in; current URL is `/`; account has access to at least one agent across one or more projects | Root path loads the global Dashboard | 1. Open `/` after authentication. 2. Wait for dashboard data to load. 3. Inspect the main content area. | Dashboard renders instead of ChatArea; at least one agent card appears; summary counters and search/sort controls are visible. | Draft |
| FE-HP-008 | Dashboard | P0 | User is logged in on `/`; dashboard contains at least one non-site agent card | Selecting an agent card opens correct project chat context | 1. Open the root Dashboard. 2. Click an agent card. 3. Observe route and chat state. | URL switches into the target project context; the target Agent becomes active; ChatArea is shown instead of Dashboard. | Draft |
| FE-HP-009 | Dashboard / Sidebar | P1 | User is logged in; Dashboard contains at least one agent card | Favorite persistence across refresh | 1. Favorite one agent from Dashboard. 2. Refresh the page. 3. Check Dashboard ordering and Sidebar favorites section. | Favorited agent remains marked as favorite after refresh; it appears in Sidebar favorites; favorite state persists from localStorage. | Draft |
| FE-HP-010 | Sidebar / Dashboard | P0 | User is logged in and currently inside a project chat context with an active Agent | `All Agents` clears project context | 1. While in project chat, click `All Agents` in the sidebar. 2. Observe route and main content. 3. Confirm active agent state is cleared. | Route returns to `/`; Dashboard is shown; prior project/agent context is cleared; stale chat content is not kept as the primary view. | Draft |
| FE-HP-011 | Sidebar / Permissions | P1 | Test once with an account having `hasWorkbenchAccess=true`, and once with an account having `hasWorkbenchAccess=false` | Workbench entry obeys access control state | 1. Log in with a user who has Workbench access. 2. Verify whether the Workbench entry is visible. 3. Repeat with a user who does not have Workbench access. | Workbench entry is visible only for accounts that have Workbench access; it is absent for users without that permission. | Draft |

## Module 3: Workbench, Project Settings & Agent Setup (8 cases)

| ID | Module | Priority | Preconditions | Test Case | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FE-HP-012 | Create Project | P0 | User is logged in with project creation permissions; Workbench is reachable | Create project with a valid name | 1. Open Workbench and enter the Create Project flow. 2. Enter a valid lowercase project name. 3. Submit the form. | Form closes successfully; route returns to Workbench; the new project appears in the Workbench project list. | Draft |
| FE-HP-013 | Create Project | P0 | User is logged in with project creation permissions; an existing project named `test-existing` already exists | Validation for illegal and duplicate project names | 1. Enter an illegal name such as `My Project!`. 2. Observe client-side validation state. 3. Enter `test-existing` and submit. | Illegal name is blocked before submission; duplicate name submission returns a visible backend error while keeping the form open; no duplicate project is created. | Draft |
| FE-HP-014 | Workbench | P0 | User is logged in; Workbench contains at least one manageable project | Project card opens workspace with Agents as default section | 1. Open Workbench. 2. Click a project card. 3. Observe the selected section inside project workspace. | Workbench enters the selected project workspace; the `Agents` section is active by default. | Draft |
| FE-HP-015 | Project Settings | P1 | User is logged in with owner/admin permissions; target project has a published site and at least one chat-capable agent | `default_view=site` controls initial project landing mode | 1. Open project settings. 2. Set `default_view` to `site` and save. 3. Return to the project route. | Project opens in site mode first; SiteRenderer is shown before ChatArea; no manual toggle is required. | Draft |
| FE-HP-016 | Project Settings | P1 | User is logged in with owner/admin permissions; target project supports both site and chat views | `view_locked` blocks view switching | 1. Open project settings. 2. Enable `view_locked` and save. 3. Return to the project route and inspect the top bar. | The site/chat switcher is hidden or non-interactive; user cannot manually switch view modes while lock is active. | Draft |
| FE-HP-017 | Project Settings | P1 | User is logged in with owner/admin permissions; target project settings page is open | General settings save and persist | 1. Modify a general field such as project description. 2. Save settings. 3. Refresh the page and reload the same project settings view. | Save succeeds with explicit success feedback; refreshed page shows the updated saved value. | Draft |
| FE-HP-018 | Agent Management | P1 | User is logged in with Agent management permissions; target project workspace is open on `Agents` | Successfully create an HTTP Agent | 1. Click Add Agent. 2. Fill in the required HTTP agent fields. 3. Save. | Agent is created successfully; agent list refreshes; form closes. | Draft |
| FE-HP-019 | Agent Management | P1 | User is logged in with Agent management permissions; add/edit agent form is open | Invalid JSON in extras blocks save | 1. Open the add/edit agent form. 2. Enter malformed JSON into the extras field. 3. Click Save. | A deterministic JSON error is shown; save request is not sent; form remains open for correction. | Draft |

## Module 4: Chat Core Flow (8 cases)

| ID | Module | Priority | Preconditions | Test Case | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FE-HP-020 | Chat / Model Selector | P0 | User is logged in; target project has at least one Agent; open either project route or a deep link with `?agent=` | Correct Agent is auto-selected on page entry | 1. Open a project route with either a default Agent or a deep-linked Agent. 2. Wait for the chat header and selector to load. 3. Inspect the selected Agent label. | Model selector shows the deep-linked Agent when provided; otherwise it shows the project default Agent or the first eligible Agent. | Draft |
| FE-HP-021 | Chat | P0 | User is logged in; current project and Agent are valid; chat endpoint responds normally | Send plain text message and receive streaming response | 1. Enter a text prompt. 2. Send the message. 3. Observe message rendering until completion. | If needed a conversation is auto-created; user message appears immediately; assistant response renders incrementally via streaming; final response remains visible after completion. | Draft |
| FE-HP-022 | Sidebar / Chat | P0 | User is logged in within a project context that allows chat storage | Create a new conversation from sidebar | 1. Open a project context. 2. Click `New chat`. 3. Inspect the recents list and active conversation state. | A new conversation is created exactly once; it becomes the active conversation; the recents list updates accordingly. | Draft |
| FE-HP-023 | Chat | P1 | User is logged in on the chat page; two supported files under size limit are available locally | Add valid attachments using picker and drag-drop | 1. Add one supported file using the attachment picker. 2. Drag a second supported file into the chat area. 3. Inspect the attachment tray. | Both files appear in the attachment area with deterministic metadata; drag-over visual feedback appears during drag-drop. | Draft |
| FE-HP-024 | Chat | P1 | User is logged in on the chat page; one unsupported file and one oversized file are available | Reject invalid attachments | 1. Attempt to add an unsupported file. 2. Attempt to add an oversized file. 3. Inspect attachment area and feedback state. | Each invalid file is rejected with explicit feedback; invalid files never appear in the attachment list. | Draft |
| FE-HP-025 | Chat | P0 | User is logged in; current project and Agent are selected; DevTools can simulate offline mode | Request failure or mid-stream interruption recovers cleanly | 1. Switch network offline before sending a message and submit. 2. Restore network and send again. 3. Turn network offline after streaming has already started. | In both scenarios loading ends deterministically; an error message is shown in the assistant area; input becomes usable again; page does not hang in infinite loading state. | Draft |
| FE-HP-026 | Chat | P1 | User is logged in; current Agent can return Markdown with code fences and unsafe HTML/script tags | Markdown rendering and XSS protection | 1. Send a prompt that returns Markdown with code blocks and unsafe tags. 2. Wait for rendering to complete. 3. Inspect rendered output and DOM. | Code blocks render as formatted code sections; unsafe script content is not executed or rendered as active DOM; message layout remains contained inside the chat UI. | Draft |
| FE-HP-027 | Chat / Dynamic Panel | P1 | User is logged in; current Agent can return dynamic elements such as `DynamicTable` or `DynamicButton` | Dynamic panel mounts without breaking chat interaction | 1. Send a prompt that returns supported dynamic elements. 2. Wait for dynamic panel content to mount. 3. Continue interacting with the chat view. | Dynamic elements render visibly and structurally; chat scrolling and message input remain usable; no component-level runtime error appears in the console. | Draft |

## Module 5: Artefacts & Approval Flow (3 cases)

| ID | Module | Priority | Preconditions | Test Case | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FE-HP-028 | Artefacts | P1 | User is logged in; Artefacts page contains at least one artefact entry | Artefact card opens target project and Agent | 1. Open the Artefacts page. 2. Click an artefact card. 3. Observe route and chat context. | App navigates to the linked project; the linked Agent becomes active; user lands in the correct chat context rather than an unrelated prior project. | Draft |
| FE-HP-029 | Change Requests | P1 | User is logged in as a valid approver; a pending change request exists; the user is not the requester | Approve a pending change request | 1. Open the target project Approval view. 2. Open a pending request detail. 3. Click Approve. | Approval action succeeds once; request status updates from pending; list/detail refresh reflects the approved state. | Draft |
| FE-HP-030 | Change Requests | P1 | One pending request exists where the current user is the requester; another pending request exists where the user is a valid approver | Reject requires a reason and requester cannot self-approve | 1. Open a pending request as a valid approver and click Reject with an empty reason. 2. Verify the action is blocked. 3. Open a request created by the current user. | Empty-reason reject is blocked with explicit feedback and no state change; for the self-request, approval actions are hidden or disabled so the requester cannot approve their own change. | Draft |

---

## Priority Distribution

| Priority | Count | Percentage |
| --- | --- | --- |
| P0 | 15 | 50% |
| P1 | 15 | 50% |

## Notes

- This version contains 30 high-priority cases only.
- SiteBuilder editing is intentionally excluded, but current site/chat runtime behavior is included where it affects user navigation and project landing behavior.
- Compared with the older suite, this version adds coverage for the dashboard-first home flow, route fallback handling, current project view rules, and the current approval/chat behavior that matters most in production.