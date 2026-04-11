# Frontier Acceptance Test Cases

> Version: v1.0
> Date: 2026-04-09
> Scope: Full-stack Frontier system launched via the standard Docker Compose startup
> Purpose: Validate that the system meets core business objectives from an end-user and delivery perspective
> Distinction from functional tests: Functional tests verify per-component UI behavior; acceptance tests verify that end-to-end user goals are achievable

## Design Principles

1. Each test case maps to a complete business goal, not a single UI interaction
2. Steps describe user intent without binding to specific button labels or CSS selectors
3. Expected results are measured by business value ("the user can accomplish X"), not technical metrics
4. Preconditions include the full environment and data state
5. Test cases are independent of each other and can be executed in isolation

## Environment Requirements

- Startup: `docker compose up -d --build` (from the repository root)
- Prerequisite: `http://localhost:8000` is accessible and LDAP login is functional
- Test accounts: At least one regular user (`testuser/test123`) and one admin (`admin/admin123`)
- Test data: At least one project with a working Agent that can respond to chat messages

---

## AT-001: New User Logs In and Completes a First AI Conversation

| Field | Details |
|---|---|
| **Business Goal** | A user who has never used the system can log in from scratch, discover available AI Agents, start a conversation, and receive a meaningful reply |
| **Priority** | P0 |
| **Preconditions** | System is running; a project exists with at least one configured and responsive HTTP Agent (e.g. Demo HTTP Agent); test user account exists but has never logged in (or clear localStorage to simulate first use) |
| **Steps** | 1. Open `http://localhost:8000` — the system should display the login page <br> 2. Log in with valid credentials <br> 3. After login, observe the home page — the Dashboard should show available Agents <br> 4. Select an Agent to start a conversation <br> 5. Type a message and send it <br> 6. Wait for the AI reply to fully arrive |
| **Acceptance Criteria** | ✅ The user can complete the entire journey from login to receiving an AI reply without additional guidance <br> ✅ The Dashboard displays at least one clickable Agent <br> ✅ The chat message streams in progressively and renders completely <br> ✅ No blank screens, 500 errors, or uncaught exceptions occur during the process |
| **Status** | Draft |

---

## AT-002: Project Admin Creates a Project and Configures a Working Agent

| Field | Details |
|---|---|
| **Business Goal** | A user with Workbench access can create a new project, configure an Agent connected to an external service, and make that Agent available to team members |
| **Priority** | P0 |
| **Preconditions** | System is running; current user has Workbench access; the example Agent backend (http-example container, port 8080) is healthy |
| **Steps** | 1. Navigate to Workbench from the sidebar <br> 2. Create a new project (using a valid lowercase name) <br> 3. Enter the new project's Agent management page <br> 4. Add an HTTP-type Agent with the endpoint `http://http-example:8080` <br> 5. Save the Agent configuration <br> 6. Return to the Dashboard and check whether the new Agent appears <br> 7. Click the Agent and send a test message |
| **Acceptance Criteria** | ✅ Project is created successfully and appears in the Workbench project list <br> ✅ Agent configuration is saved successfully and appears in the project's Agent list <br> ✅ The newly created Agent is discoverable by the current user on the Dashboard <br> ✅ Sending a message through the Agent returns a normal streaming reply |
| **Status** | Draft |

---

## AT-003: Conversation History Persists Across Sessions

| Field | Details |
|---|---|
| **Business Goal** | A user's conversation history is not lost when the browser is closed; after re-login the user can resume a previous conversation |
| **Priority** | P0 |
| **Preconditions** | System is running; user is logged in and has completed at least one round of conversation with an Agent (containing both a user message and an AI reply) |
| **Steps** | 1. In a conversation with an Agent, send a distinctive message (e.g. "Please remember the number 42") <br> 2. Confirm that an AI reply is received <br> 3. Close the browser tab <br> 4. Reopen `http://localhost:8000` and log in <br> 5. Locate the previous conversation in the sidebar history <br> 6. Click to enter that conversation |
| **Acceptance Criteria** | ✅ The previous conversation entry is visible in the sidebar history <br> ✅ Clicking it loads the full message history including both user messages and AI replies <br> ✅ Message content is identical to what was sent — no truncation or garbled text <br> ✅ New messages can be sent within the resumed conversation |
| **Status** | Draft |

---

## AT-004: Platform Admin Manages Platform-Wide Announcements

| Field | Details |
|---|---|
| **Business Goal** | A platform admin can create, publish, reorder, and delete platform-wide announcement banners; regular users can see and dismiss these announcements |
| **Priority** | P1 |
| **Preconditions** | System is running; admin account (`admin/admin123`) can access the Admin Panel; a separate regular user account is available |
| **Steps** | 1. Log in as admin and navigate to the Admin Panel <br> 2. On the Banner management page, create a new announcement (fill in message, tag, and color) <br> 3. Confirm the announcement appears in the Banner list with Active status <br> 4. Open another browser (or incognito window) and log in as a regular user <br> 5. Observe whether the newly created announcement banner is displayed at the top of the page <br> 6. As the regular user, dismiss the announcement <br> 7. Refresh the page and confirm the dismissed announcement does not reappear automatically <br> 8. Switch back to the admin session and delete the announcement |
| **Acceptance Criteria** | ✅ Admin can successfully create an announcement that immediately appears in the management list <br> ✅ The regular user sees the announcement banner after logging in <br> ✅ After dismissing the announcement and refreshing, it no longer auto-displays <br> ✅ After the admin deletes the announcement, the regular user no longer sees it on refresh |
| **Status** | Draft |

---

## AT-005: Agent Changes Require Approval When Approval Workflow Is Enabled

| Field | Details |
|---|---|
| **Business Goal** | When a project has an approval workflow enabled, modifications to Agents do not take effect immediately — they require approval from a designated approver |
| **Priority** | P1 |
| **Preconditions** | System is running; a project exists where the current user is the owner; the project has at least one working Agent; at least one user can be designated as an approver |
| **Steps** | 1. As the project owner, navigate to the Approval tab in project settings <br> 2. Enable the approval workflow and add an approver <br> 3. Go to Agent management and modify an Agent's configuration (e.g. change description or endpoint) <br> 4. Save the changes <br> 5. Observe the save confirmation message <br> 6. Navigate to the Change Requests page to view pending requests |
| **Acceptance Criteria** | ✅ After enabling the approval workflow, the save message changes to "Submitted for approval" rather than "Saved" <br> ✅ The Agent's current configuration remains unchanged (the modification has not taken effect) <br> ✅ A pending change request appears on the Change Requests page <br> ✅ The change request contains an accurate summary of the modifications |
| **Status** | Draft |

---

## AT-006: Artefacts Page Displays All Publicly Shared Agents

| Field | Details |
|---|---|
| **Business Goal** | Agents marked as Artefacts are discoverable and usable by all authenticated users through the dedicated Artefacts page |
| **Priority** | P1 |
| **Preconditions** | System is running; at least one Agent has its `is_artefact` property set to true; that Agent can respond normally |
| **Steps** | 1. Log in as a regular user <br> 2. Navigate to the Artefacts page from the sidebar <br> 3. Locate the publicly shared Agent in the Artefacts list <br> 4. Click the Agent to start a conversation <br> 5. Send a message and wait for a reply |
| **Acceptance Criteria** | ✅ The Artefacts page loads correctly and displays the marked Agent <br> ✅ The Agent card shows key information including name, project, and connection type <br> ✅ Clicking it successfully opens the conversation interface <br> ✅ Messages can be sent and streaming replies are received normally |
| **Status** | Draft |

---

## AT-007: User Uploads a File Attachment in Chat and Receives a File-Aware Reply

| Field | Details |
|---|---|
| **Business Goal** | Users can attach files in a conversation and the Agent can receive and provide replies informed by the file content |
| **Priority** | P1 |
| **Preconditions** | System is running; the target Agent has `enable_file_attachments` enabled in its configuration; the Agent backend supports processing file attachments; a small test file is prepared (e.g. .txt or .csv, < 10MB) |
| **Steps** | 1. As a logged-in user, open the conversation interface for the target Agent <br> 2. Add a test file via the attachment button or drag-and-drop <br> 3. Confirm the file preview displays correctly (file name, size) <br> 4. Type a question about the file content and send <br> 5. Wait for the AI reply |
| **Acceptance Criteria** | ✅ The file attachment is added successfully with correct preview information (name, size) <br> ✅ After sending, the message area shows the user message along with attachment info <br> ✅ The AI reply demonstrates understanding of or reference to the file content <br> ✅ Unsupported file types are correctly rejected with a user-visible prompt |
| **Status** | Draft |

---

## AT-008: Project Admin Configures Member Permissions and Verifies Access Control

| Field | Details |
|---|---|
| **Business Goal** | A project admin can assign different roles and Agent-level permissions to team members, and the permission configuration takes effect immediately for the authorized user |
| **Priority** | P1 |
| **Preconditions** | System is running; a project exists where the current user is the owner; another test user (e.g. testuser) exists and has not been added to this project |
| **Steps** | 1. As the project owner, navigate to the Members tab in project settings <br> 2. Add testuser as a member and assign access to a specific Agent <br> 3. Save the member configuration <br> 4. Log in as testuser <br> 5. Check the Dashboard for visibility of the authorized Agent <br> 6. Attempt to use the conversation feature in the authorized project |
| **Acceptance Criteria** | ✅ The member is added successfully and appears in the project member list <br> ✅ After logging in, testuser can see the authorized Agent on the Dashboard <br> ✅ testuser can successfully enter the authorized project and chat with the designated Agent <br> ✅ testuser cannot see Agents that were not authorized (if other restricted Agents exist) |
| **Status** | Draft |

---

## AT-009: Deep Link Opens the Specified Project and Agent Conversation Directly

| Field | Details |
|---|---|
| **Business Goal** | Users can open a specific project and Agent conversation interface directly via a shared URL without manual navigation |
| **Priority** | P1 |
| **Preconditions** | System is running; a project named `demo` exists with an Agent (ID is known); the test user has access to this project |
| **Steps** | 1. Enter `http://localhost:8000/demo?agent={agent_id}` directly in the browser <br> 2. If not logged in, complete the login flow <br> 3. Observe the page state after login |
| **Acceptance Criteria** | ✅ After login, the app lands directly in the `demo` project context <br> ✅ The specified Agent is automatically selected <br> ✅ The chat interface is ready and a conversation can be started immediately <br> ✅ The project and Agent parameters in the URL are not lost during the login redirect |
| **Status** | Draft |

---

## AT-010: Theme Toggle and User Preferences Persist Across Sessions

| Field | Details |
|---|---|
| **Business Goal** | User interface preferences (theme mode, favorited Agents) persist across browser sessions and are not lost on logout or page refresh |
| **Priority** | P2 |
| **Preconditions** | System is running; user is logged in; current theme is light mode; the Dashboard has multiple available Agents |
| **Steps** | 1. Click the theme toggle button in the TopBar to switch to dark mode <br> 2. Favorite an Agent on the Dashboard <br> 3. Close the browser tab <br> 4. Reopen `http://localhost:8000` and log in <br> 5. Observe the theme and favorite state |
| **Acceptance Criteria** | ✅ After re-login, the system automatically applies the dark theme <br> ✅ The previously favorited Agent still shows the favorite marker <br> ✅ The favorited Agent is sorted higher in the Dashboard list <br> ✅ The favorited Agent appears in the sidebar's favorites section |
| **Status** | Draft |
