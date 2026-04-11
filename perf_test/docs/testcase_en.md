# Frontier Frontend Functional Test Cases

## Scope

- Type: Functional UI test cases
- Exclusions: Performance testing, SiteBuilder
- Basis: Currently implemented frontend UI and interactions, including Login, Create Project, Sidebar, ChatArea, ModelSelector, Artefacts, Workbench, ProjectSettings, AgentManager, ChangeRequests, ContactUs

## Status Definitions

- Draft: Test case defined but not yet executed
- Pass: Executed, result matches expectation
- Fail: Executed, result does not match expectation
- Blocked: Cannot be executed due to environment or dependency issues

---

## Module 1: Login & Global Safeguards (4 cases)

| ID | Module | Priority | Preconditions | Test Case | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FE-FUNC-001 | Login | P0 | User is on the login page; backend login endpoint is available; a valid account exists | Successful login with valid credentials | Enter valid username and password, click Sign in | access_token is written to localStorage; page route switches from login to the chat view | Draft |
| FE-FUNC-002 | Login | P1 | User is on the login page | Invalid credentials handling | Enter incorrect username or password, click Sign in | Page displays an error message — either the backend-returned error or the default "Login failed" | Draft |
| FE-FUNC-037 | Login / Global | P0 | User is logged in; replace the token value in DevTools > Application > localStorage with an invalid string (e.g. expired_xxx) | Token expiry & 401 interception | Click New chat, Workbench, or any entry that triggers an authenticated request | Frontend intercepts the 401 response, clears the token from localStorage, and auto-redirects to the login page with no unhandled exceptions or white screen | Draft |
| FE-FUNC-041 | Global | P1 | User is logged in; the current account has only the member role on the target project (no admin/owner permissions) | 403 insufficient permissions interception | Attempt an operation requiring admin privileges (e.g. modify project settings or manage members) | Page displays a permission-denied message or blocks the operation; no unhandled exceptions or white screen | Draft |

## Module 2: Workbench & Project Management (4 cases)

| ID | Module | Priority | Preconditions | Test Case | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FE-FUNC-004 | Create Project | P0 | User is logged in with project creation permissions; currently on the Create Project page | Create project with a valid name | Enter a valid lowercase project name, click Create Project | Creation form closes automatically; the new project name appears in the project list or sidebar | Draft |
| FE-FUNC-005 | Create Project | P1 | User is logged in, on the Create Project page; a project named "test-existing" already exists in the system | Project name validation (illegal characters & duplicate name) | ① Enter "My Project!" (contains uppercase and special characters), observe validation; ② Clear the field and enter the existing project name "test-existing", click Create Project | ① Inline validation error is displayed, submit button is blocked, no request is sent; ② Request is sent but backend returns an error, form remains open | Draft |
| FE-FUNC-022 | Workbench | P1 | User is logged in but the account has no owned/admin projects | Empty project list state | Open Workbench | Page displays an empty-state message and a Create Project button | Draft |
| FE-FUNC-023 | Workbench | P0 | User is logged in; Workbench contains at least one manageable project | Navigate from project card to project workspace | Click any project card | Page enters the selected project's workspace view with the Agents section activated by default | Draft |

## Module 3: Sidebar & Conversation Routing (2 cases)

| ID | Module | Priority | Preconditions | Test Case | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FE-FUNC-008 | Sidebar | P0 | User is logged in, on the chat route, with a project selected | Create new conversation from sidebar | Click New chat | A new conversation is created, added to Recents, and becomes the active conversation | Draft |
| FE-FUNC-012 | Sidebar | P0 | User is logged in | Logout | Click the logout button in the sidebar | Auth token is cleared, user session ends, page redirects to the login page | Draft |

## Module 4: AI Chat Core Flow (8 cases)

| ID | Module | Priority | Preconditions | Test Case | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FE-FUNC-014 | Chat | P0 | User is logged in, project selected, current Agent available, chat endpoint responding normally | Send plain text message and receive streaming response | Enter content in the chat input, click send or press Enter | If no conversation exists one is auto-created; user message and assistant placeholder appear, streaming response renders incrementally | Draft |
| FE-FUNC-013 | Chat / Model Selector | P1 | User is logged in; current project has at least one Agent configured; on the chat page | Auto-select default Agent for current project | Open the project chat page | Model selector dropdown shows the selected Agent name — preferring the pre-selected Agent or the default Agent | Draft |
| FE-FUNC-016 | Chat | P1 | User is logged in, on the chat page; two locally available files of supported types and under 10 MB | Add valid file attachments via button and drag-and-drop | ① Click the attachment button and select the first file via the file picker; ② Drag the second file from the system file manager into the chat area and drop it | Both files appear in the attachment area showing icon, name, and size; a drag visual indicator appears in the chat area during drag-over | Draft |
| FE-FUNC-017 | Chat | P1 | User is logged in, on the chat page; prepare a .exe file (unsupported type) and a >10 MB .png file (oversized) | Reject unsupported or oversized files | Click the attachment button, select the unsupported or oversized file | File is rejected, user receives a prompt, and the invalid file does not appear in the attachment area | Draft |
| FE-FUNC-019 | Chat | P1 | User is logged in, project and Agent selected; ready to toggle DevTools > Network to Offline at different points | Chat network failure fallback (request failure & stream interruption) | ① Switch to Offline then send a message (simulates complete request failure); ② Restore network, send a new message, wait for the AI to begin returning streaming content then switch to Offline again (simulates mid-stream interruption) | In both scenarios the assistant message area shows "Error: Could not reach the server.", loading state ends, and the input field becomes usable again | Draft |
| FE-FUNC-038 | Chat | P1 | User is logged in, on the chat page; AI response contains headings, lists, code blocks with language tags, and inline script tags | Markdown rendering & XSS protection | Send a message and wait for the AI to return a complex Markdown reply | Code blocks have syntax-highlighted backgrounds; script and other dangerous tags do not appear in the rendered DOM; content does not overflow the message bubble boundaries | Draft |
| FE-FUNC-039 | Chat / Dynamic Panel | P1 | User is logged in, on the chat page; current Agent returns elements data containing DynamicTable or DynamicButton | Dynamic component mounting resilience | Send a message that triggers the AI to return dynamic components | DynamicTable column headers are visible and row data renders correctly; chat area scrolling is not obstructed; no component-level runtime errors in the browser console | Draft |
| FE-FUNC-040 | Create Project / Chat | P1 | User is logged in; DevTools > Network > Throttling set to Slow 3G to slow down request responses; Create Project page or chat page is open | Concurrency & debounce control | Rapidly click Create Project or the send button multiple times in quick succession | Frontend prevents duplicate submissions via loading disable or equivalent debounce mechanism; only one valid request is sent; no duplicate projects or messages are created | Draft |

## Module 5: Artefacts Flow (1 case)

| ID | Module | Priority | Preconditions | Test Case | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FE-FUNC-021 | Artefacts | P1 | User is logged in; Artefacts page has loaded with an artefact list | Navigate from Artefacts to project chat context | Click any artefact card | Page navigates to the corresponding project's chat view; Agent auto-switches to the target Agent | Draft |

## Module 6: Project Settings & Agent Management (6 cases)

| ID | Module | Priority | Preconditions | Test Case | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FE-FUNC-024 | Project Settings | P1 | User is logged in, on the target project settings page; account has owner/admin permissions | Save general project settings | Modify settings on the General tab, click save | Page displays a save-success feedback and reloads the latest saved values | Draft |
| FE-FUNC-025 | Project Settings | P1 | User is logged in, navigated to target project settings > Permissions > LAN IDs; account has member-management permissions; assignable Agents exist | Manage LAN ID members (add & edit) | ① Click the add button, fill in username, select role and Agent permissions, click save; ② Click the edit button on an existing member, modify role or Agent permissions, click save | After adding: the new member appears in the list with correct permissions; after editing: the modified member's role and Agent permissions reflect the new values | Draft |
| FE-FUNC-027 | Project Settings | P1 | User is logged in, navigated to target project settings > Permissions > AD Groups; account has permission-management ability; assignable Agents exist | Manage AD group permissions (add & edit) | ① Click the add button, fill in Group DN, Group Name, select role and Agent permissions, click save; ② Click the edit button on an existing AD group, modify role or Agent permissions, click save | After adding: the new AD group appears in the list with correct permissions; after editing: the modified AD group's permissions reflect the new values | Draft |
| FE-FUNC-029 | Project Settings | P1 | User is logged in, navigated to target project settings > Approval; account has approval configuration permissions | Change approval type | Switch the approval type (any / all / majority), click save | Approval type is persisted; after page refresh the updated approval type is still displayed | Draft |
| FE-FUNC-031 | Agent Management | P1 | User is logged in, on the target project's Agents page; account has Agent management permissions | Successfully create an HTTP Agent | Click add Agent, fill in the required HTTP Agent fields, and save | New Agent is created, list refreshes, form closes | Draft |
| FE-FUNC-032 | Agent Management | P1 | User is logged in, on the target project's Agents page; add/edit Agent form is open | Invalid JSON in extras blocks save | Enter malformed JSON in the Agent extras field (e.g. {key: value}), click save | Page displays a JSON format error message; no save request is sent | Draft |

## Module 7: Change Request Approval Flow (5 cases)

| ID | Module | Priority | Preconditions | Test Case | Steps | Expected Result | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FE-FUNC-030 | Project Settings | P1 | User is logged in, navigated to target project settings > Approval; eligible approvers exist (members with admin or owner role) | Add or remove approvers | Select an eligible approver from the dropdown and add; or click the remove button on an existing approver | Approver list refreshes in real time — added approver appears in the list, or removed approver disappears from the list | Draft |
| FE-FUNC-034 | Change Requests | P1 | User is logged in, on the target project Approval page; at least one change request exists in the list | View change request details | Click any change request in the list | Detail modal opens, displaying requester, request type, change content, and other information | Draft |
| FE-FUNC-035 | Change Requests | P1 | User is logged in; a pending change request detail is open; current account is a legitimate approver for this request (not the requester) | Approve a change request | Click the Approve button | Request status updates, detail modal closes, list refreshes to reflect the new status | Draft |
| FE-FUNC-036 | Change Requests | P1 | User is logged in; a pending change request detail is open; current account is a legitimate approver (not the requester); comment field is empty | Reject requires a reason | Click Reject with the comment field empty | A prompt appears requiring a rejection reason; request status remains unchanged; no reject action is sent | Draft |
| FE-FUNC-044 | Change Requests | P1 | User is logged in, on the target project Approval page; the current user is the requester of a pending change request | Requester cannot approve their own change request | Open the change request detail initiated by the current user | Approve and Reject buttons are disabled or hidden; the user cannot perform approval actions on their own request | Draft |

---

## Priority Distribution

| Priority | Count | Percentage |
| --- | --- | --- |
| P0 | 6 | 20% |
| P1 | 24 | 80% |

## Trimming Notes

This version was trimmed from 46 cases to 30, using the following strategies:

### Merged Cases (5 groups)
| Merged ID | Sources | Rationale |
| --- | --- | --- |
| FE-FUNC-005 | Original 005 + 007 | Frontend validation and backend validation on the same form, covered in two sequential steps |
| FE-FUNC-016 | Original 016 + 043 | Two input paths for the same feature (adding attachments), merged into button + drag-and-drop |
| FE-FUNC-019 | Original 019 + 045 | Same failure type (network fault) at two different points, merged into request failure + stream interruption |
| FE-FUNC-025 | Original 025 + 026 | Add and edit operations on the same page, merged into full CRUD |
| FE-FUNC-027 | Original 027 + 028 | Add and edit operations on the same page, merged into full CRUD |

### Removed Cases (11 cases)
| Removed ID | Original Priority | Removal Rationale |
| --- | --- | --- |
| FE-FUNC-003 | P1 | Login network error — same fetch failure pattern already covered by chat network error in 019 |
| FE-FUNC-006 | P2 | Project name suggestion feature — non-critical path |
| FE-FUNC-009 | P1 | Conversation switching (⚠️ Known trim risk: high-frequency operation — should be re-added first if regression issues are found) |
| FE-FUNC-010 | P2 | Dropdown menu toggle — low-priority UI interaction |
| FE-FUNC-011 | P2 | Contact Us modal — non-critical path |
| FE-FUNC-015 | P2 | Sample question click — non-critical path |
| FE-FUNC-018 | P2 | Remove attachment before sending — low-priority operation |
| FE-FUNC-020 | P2 | Artefacts search/filter — core navigation already covered by 021 |
| FE-FUNC-033 | P1 | Filter change requests by status — detail and approval actions already covered by 034–036 |
| FE-FUNC-042 | P2 | Empty submission interception — covered by browser-native required attribute |
| FE-FUNC-046 | P2 | No-Agent empty state — edge case |

### Priority Adjustments (3 cases)
| ID | Original | Adjusted | Rationale |
| --- | --- | --- | --- |
| FE-FUNC-022 | P2 | P1 | Empty state is a baseline UX metric for B2B products |
| FE-FUNC-023 | P1 | P0 | Entering project context is the gateway to all subsequent operations |
| FE-FUNC-040 | P2 | P1 | Debounce failure can cause data duplication — severe impact in production |

## Notes

- This document contains 30 test cases (P0 × 6, P1 × 24), trimmed from the 46-case full version.
- SiteBuilder is explicitly excluded from this document.
- The Status column is initialized to Draft; update to Pass, Fail, or Blocked as tests are executed.
