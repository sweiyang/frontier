# Frontier Frontend — Workbench & Project Management Guide

This guide covers the Frontier Workbench: creating projects, configuring
agents, managing access control, and monitoring usage.

Related guides:
[Chat Interface](frontend-chat-guide.md) |
[Approval Workflow](frontend-approval-guide.md) |
[Site Builder](frontend-site-builder-guide.md)

---

## Table of Contents

1. [Accessing the Workbench](#1-accessing-the-workbench)
2. [Creating a Project](#2-creating-a-project)
3. [Workbench Navigation](#3-workbench-navigation)
4. [Managing Agents](#4-managing-agents)
5. [Access Control (RBAC)](#5-access-control-rbac)
6. [General Project Settings](#6-general-project-settings)
7. [Usage Statistics](#7-usage-statistics)
8. [Troubleshooting](#8-troubleshooting)

---

## 1. Accessing the Workbench

You access the Workbench from the main application sidebar. It opens to the
**project picker** view, titled `Your Projects`, which displays all projects
you own or administer in a responsive card grid. Each card shows the project
name and agent count. If a project has a published dashboard, a `View Site`
button appears on its card. Click any card to enter its workspace.

### Breadcrumb Navigation

After selecting a project, a breadcrumb bar appears: `Projects / my-project`.
Click **Projects** (the back arrow) to return to the picker. A **Workbench**
badge in the upper-right corner confirms your current view.

### Creating a Project from the Picker

If you have existing projects, a `Create Project` button appears in the
picker header. If you have no projects, an empty state with a centered
`Create Project` button is shown instead.

---

## 2. Creating a Project

Clicking `Create Project` opens a centered form with a single field:
`Project Name`.

### Name Validation Rules

| Rule | Detail |
|------|--------|
| **Allowed characters** | Lowercase letters `a-z`, digits `0-9`, hyphens `-`, underscores `_` |
| **Maximum length** | 63 characters |
| **Cannot start with** | Hyphen `-` or underscore `_` |
| **Case** | Automatically lowercased on submission |

If you enter an invalid name, an inline error appears. Frontier also offers
an **auto-suggestion** — for example, typing `My Project!` produces a
clickable hint: "Use **my-project** instead?" Click the suggestion to apply
it.

Click `Create Project` to submit. A spinner appears while processing. On
success you enter the new project. If the name is taken, an error is shown.
`Cancel` returns you to the previous view.

---

## 3. Workbench Navigation

After selecting a project, the workspace shows a **left sidebar** (200px) and
a **content area**. The sidebar is labeled `Configure` and contains five
sections:

| Section | Description |
|---------|-------------|
| `Agents` | Create and manage AI agent connections (default view) |
| `Site Builder` | Opens the visual site/dashboard builder in full-page mode |
| `Approval` | View and act on change requests for production environments |
| `Usage` | View message, token, and site analytics |
| `General` | Project settings, permissions (RBAC), and approval configuration |

The active section is highlighted in amber. Clicking `Site Builder` navigates
to the full-page builder at `/<project>/site-builder`. On screens narrower
than 768px, the sidebar becomes a horizontal scrollable tab bar.

---

## 4. Managing Agents

The `Agents` section is powered by the **AgentManager** component. It lists
all agents configured for the current project and provides full CRUD
operations.

### Agent List

Each agent is displayed as a card showing:
- **Icon** (custom upload or default placeholder)
- **Name**
- **Connection type** badge (`http`, `langgraph`, or `openai`)
- **Default** badge if the agent is set as the project default
- **Artefact** badge if shared to the organization gallery

Action buttons on each card let you **edit**, **duplicate**, **delete**, or
view **version history**.

### Creating an Agent

Click `Add Agent` to open the agent form. The form fields adapt based on the
selected `Connection Type`.

**Common fields (all connection types):**

| Field | Required | Description |
|-------|----------|-------------|
| `Name` | Yes | Display name in the chat UI |
| `Endpoint` | Yes | Full URL to the agent endpoint |
| `Connection Type` | Yes | One of `http`, `langgraph`, `openai` |
| `Set as Default` | No | Toggle to make this the default agent for the project |
| `Mark as Artefact` | No | Toggle to share this agent in the organization-wide gallery |
| `Icon` | No | Upload an image (max 5 MB; image files only) |
| `Extras (JSON)` | No | Arbitrary JSON merged into every request payload |

**LangGraph-specific fields:**
- `Graph ID` — optional filter for a specific graph
- `Fetch Assistants` button — queries the endpoint for available assistants
- `Assistant` dropdown — select from fetched assistants (required)

**OpenAI-specific fields:**
- `Fetch Models` button — queries the endpoint for available models
- `Model` dropdown — select from fetched models (required)
- `System Prompt` — optional system-level instructions sent with every request

### Authentication Configuration

Below the connection fields, you configure how Frontier authenticates with
the agent endpoint.

| Auth Type | Credentials Field | Header Sent |
|-----------|-------------------|-------------|
| `None` | — | No auth header |
| `API Key` | Single token string | `X-API-Key: <token>` |
| `Bearer Token` | Single token string | `Authorization: Bearer <token>` |
| `Basic Auth` | Username + Password | `Authorization: Basic <base64>` |

Credentials are hidden by default. Click the **show/hide toggle** to reveal
them.

### Editing and Duplicating

- **Edit**: Click the edit icon on an agent card. The form opens pre-filled
  with the agent's current configuration. Make changes and click `Save`.
- **Duplicate**: Click the duplicate action. The form opens pre-filled but
  in "create" mode, so saving creates a new agent with the copied settings.

### Deleting an Agent

Click the delete icon on the agent card. A confirmation dialog appears:
`Delete agent "<name>"?`. Confirm to proceed.

In **production environments** with approval enabled, create, edit, and
delete actions may produce a change request instead of applying immediately.
A notification banner appears: "Your change request has been submitted and is
pending approval." See the [Approval Workflow Guide](frontend-approval-guide.md)
for details.

### Version History and Rollback

Click the **version history** icon on an agent card to open the version
history panel. This panel lists all saved versions of the agent, created
automatically when changes are approved.

Each version entry shows the version number and a `Rollback` button. Click
`Rollback` and confirm the dialog to restore the agent to that version. In
production environments, rollbacks may also require approval.

---

## 5. Access Control (RBAC)

Access control is managed under **General > Permissions**. This section has
three sub-tabs: `LAN IDs`, `AD Groups`, and `Roles`.

### Members (LAN IDs)

The `LAN IDs` sub-tab manages individual user access. The member table
displays columns for **LAN ID**, **Agents**, **Role**, and **Actions**.

**Adding a member:**
1. Click `Add LAN ID`.
2. In the modal, enter the user's **LAN ID (username)** (e.g., `jsmith`).
3. Select a **Role**: `Member` or `Admin`.
4. Optionally assign **per-agent permissions** by searching for agents and
   adding them to the permission list. If no agents are explicitly assigned,
   the member can access all agents.
5. Click `Save`.

**Editing a member:**
Click the edit icon in the Actions column. The modal opens with the
username locked (non-editable). You can change the role and agent
permissions.

**Changing a role inline:**
For non-owner members, a role dropdown appears directly in the table. Change
it to update the role immediately.

**Removing a member:**
Click the delete icon. Confirm the dialog: `Remove "<username>" from
project?`.

The project **Owner** is always listed in the table with an `Owner` badge and
cannot be edited or removed.

### AD Groups

The `AD Groups` sub-tab manages group-based access through Active Directory.
The table displays columns for **Group Name**, **DN**, **Agents**, **Role**,
and **Actions**.

**Adding an AD group:**
1. Click `Add AD Group`.
2. Enter the **Group DN** (Distinguished Name) and a **Group Name** (display
   label).
3. Select a **Role**: `Member` or `Admin`.
4. Optionally assign per-agent permissions.
5. Click `Save`.

Editing and removing AD groups follows the same pattern as members. Role
changes can also be made inline via the dropdown in the table.

### Roles Reference

The `Roles` sub-tab displays read-only role definition cards:

| Role | Permissions |
|------|-------------|
| **Member** | Use AI agents, view project resources, create conversations |
| **Admin** | All Member permissions, manage project settings, add/remove members, configure AI agents |
| **Owner** | Full control (set at project creation, cannot be changed) |

---

## 6. General Project Settings

The **General** section has three sub-tabs: `General`, `Permissions`, and
`Approval`.

### General Sub-Tab

This sub-tab contains the following toggle:

- **Disable Message Content Storage** — when enabled, only the thread ID and
  conversation ID are stored in the database. Message content is not
  persisted. This is useful for compliance scenarios where you must not
  retain conversation text.

Click `Save Settings` to apply changes.

### Permissions Sub-Tab

This sub-tab contains:

- **Disable Authentication (Allow Anonymous Access to Agents)** — when
  enabled, users can chat with agents in this project without logging in.
  **Warning: this makes your agents publicly accessible.** Click
  `Save Settings` to apply.

Below the toggle, the RBAC management interface appears (LAN IDs, AD Groups,
and Roles sub-tabs as described in [Section 5](#5-access-control-rbac)).

### Approval Sub-Tab

This sub-tab configures the approval workflow for the project.

**Approval Type** — a dropdown with three options:

| Type | Behavior |
|------|----------|
| `Any single approver` | One approval from any designated approver is sufficient |
| `Majority of approvers` | More than 50% of approvers must approve |
| `All approvers` | Every designated approver must approve |

**Approvers list** — shows current approvers and a `Add Approver` button.
Only project admins and owners are eligible to be approvers. Use the search
field to filter eligible users, select one, and click `Add`. To remove an
approver, click the delete icon next to their name.

For the full approval workflow (change requests, approve/reject actions, and
status filtering), see the [Approval Workflow Guide](frontend-approval-guide.md).

---

## 7. Usage Statistics

The `Usage` section provides analytics for both chat activity and site
dashboards. Data loads automatically when you navigate to this section. Click
`Refresh` to reload.

### Chat Usage

Three summary cards appear at the top:

| Metric | Description |
|--------|-------------|
| **Total Messages** | Cumulative message count across all agents |
| **Total Tokens** | Cumulative token usage across all agents |
| **Agents Used** | Number of distinct agents that have handled messages |

Below the summary, a **Usage by Agent** table breaks down per-agent stats:

| Column | Description |
|--------|-------------|
| `Agent Name` | The agent's display name |
| `Messages` | Total messages handled |
| `Tokens` | Total tokens consumed |
| `Avg Tokens/Message` | Computed average tokens per message |
| `Total Users` | Number of distinct users who have used this agent |
| `Active Users` | Users who used this agent in the last 7 days |

### Site Analytics

If the project has a published dashboard, a **Site Analytics** section appears
below chat usage, covering the last 7 days:

- **Summary cards**: Page Views, Unique Visitors, Interactions
- **Views by Page** table: Page Path, Views, Unique Visitors
- **Top Components** table: Component ID, Type, Interactions

If no usage data exists yet, an empty state message is displayed:
"Usage statistics will appear here once messages are sent in this project."

---

## 8. Troubleshooting

| Issue | Solution |
|-------|----------|
| Project name rejected on creation | Ensure the name uses only lowercase `a-z`, `0-9`, `-`, `_`, does not start with `-` or `_`, and is at most 63 characters. Use the auto-suggestion if offered. |
| Cannot see a project in the picker | You must be the project owner or an admin. Ask the owner to add you as a member with the appropriate role. Platform owners can see all projects. |
| Agent form rejects extras JSON | Verify the `Extras (JSON)` field contains valid JSON. Use a JSON validator if needed. Common mistake: trailing commas. |
| "Fetch Assistants" or "Fetch Models" returns nothing | Confirm the `Endpoint` URL is correct and reachable. Verify authentication credentials are configured if the endpoint requires them. |
| Agent save shows "pending approval" | You are in a production environment with approval enabled. Your change was submitted as a change request. An approver must approve it before it takes effect. See the [Approval Workflow Guide](frontend-approval-guide.md). |
| Cannot remove the project owner | The owner role is fixed at project creation and cannot be removed or reassigned through the UI. |
| Role dropdown missing for a member | The member is the project owner. Owner roles are displayed as static text and cannot be changed. |
| Usage data shows "No usage data available" | Messages must be sent through agents in this project before usage statistics appear. Send a test message and refresh. |
| Site analytics section not visible | The project must have a published dashboard. Create and publish one using the [Site Builder](frontend-site-builder-guide.md). |
| Workbench sidebar missing on mobile | On screens narrower than 768px, the sidebar converts to a horizontal scrollable tab bar at the top of the workspace. Scroll horizontally to find all sections. |
| Icon upload rejected | Only image files are accepted (JPEG, PNG, GIF, WebP, SVG). Maximum file size is 5 MB. |
| AD group access not working | Verify the **Group DN** matches the exact Distinguished Name in Active Directory. Ensure LDAP integration is configured in the server's `config.yaml`. |
