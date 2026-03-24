# Frontier Frontend — Approval Workflow Guide

This guide covers the approval workflow feature in Frontier, which enforces
change management for agent modifications in production environments.

---

## Table of Contents

1. [Overview](#overview)
2. [When Approvals Are Required](#when-approvals-are-required)
3. [Configuring Approval Settings](#configuring-approval-settings)
4. [Managing Approvers](#managing-approvers)
5. [Change Requests](#change-requests)
6. [Reviewing and Acting on Requests](#reviewing-and-acting-on-requests)
7. [Version History and Rollback](#version-history-and-rollback)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The approval workflow is a **production-only** feature that adds a review
gate to agent modifications. When enabled, any change to an agent
configuration (create, update, or delete) generates a change request that
must be approved before it takes effect. This prevents unreviewed changes
from reaching production and provides an auditable record of who requested
and approved each modification.

You manage approval settings and review change requests from the
**Workbench** inside your project. For instructions on accessing the
Workbench, see [frontend-workbench-guide.md](./frontend-workbench-guide.md).

---

## When Approvals Are Required

Approvals are enforced only when your Frontier instance is running in a
**production environment** (`app_env` set to production in `config.yaml`
with `approval.enabled: true`).

The following agent operations trigger a change request:

| Operation | Change Type Label | Description |
|-----------|-------------------|-------------|
| Add a new agent | `Create Agent` | A new agent is being introduced to the project |
| Modify an existing agent | `Update Agent` | Any field change on an existing agent |
| Remove an agent | `Delete Agent` | An agent is being removed from the project |

In non-production environments, agent changes apply immediately without
approval.

---

## Configuring Approval Settings

To configure approval settings, open the **Workbench** for your project,
then navigate to **General > Approval** (the `Approval` sub-tab under the
General section).

### Approval Type

The `Approval Type` dropdown controls how many approvals are needed to
approve a change request. Choose one of the following:

| Approval Type | UI Label | Behavior |
|---------------|----------|----------|
| Any | `Any single approver` | One approval from any designated approver is sufficient |
| Majority | `Majority of approvers` | More than 50% of approvers must approve |
| All | `All approvers` | Every designated approver must approve (unanimous) |

Select a value from the dropdown and it saves automatically.

---

## Managing Approvers

The **Approvers** section appears directly below the Approval Type
selector on the same **General > Approval** page.

### Adding an Approver

1. Click the `Add Approver` button in the Approvers section header.
2. A search panel appears listing eligible users. **Only project admins
   and owners** are eligible to be approvers.
3. Type in the search field to filter the list. Each entry shows the
   username and a badge indicating whether the user is an `Owner` or
   `Admin`.
4. Select a user, then click `Add`.
5. Click `Cancel` to dismiss the form without adding anyone.

If no eligible users are available, you will see the message:
"No eligible users available. Only project admins and owners can be added
as approvers."

**Auto-add behavior:** If no approvers are configured when a change
request is created, Frontier automatically adds the project owner as an
approver so the workflow can proceed.

### Viewing Approvers

The approver list shows each approver's **username** and the date they
were added (e.g., "Added 3/15/2026").

### Removing an Approver

Click the trash icon button to the right of an approver's name to remove
them. The removal takes effect immediately.

---

## Change Requests

To view change requests, open the **Workbench** and click the `Approval`
tab in the top navigation. This loads the **Change Requests** panel,
powered by the `ChangeRequests` component.

### List View

The header displays `Change Requests` along with a pending count badge
(e.g., "3 pending") when there are outstanding requests.

### Filtering

Use the status dropdown in the top-right corner to filter the list:

| Filter Option | Value | Shows |
|---------------|-------|-------|
| `All statuses` | `all` | Every change request regardless of status |
| `Pending` | `pending` | Requests awaiting review |
| `Approved` | `approved` | Requests that have been approved |
| `Rejected` | `rejected` | Requests that have been rejected |

Click the `Refresh` button next to the dropdown to reload the list.

### Request Cards

Each change request appears as a card showing:

- **Request ID** — a numeric identifier prefixed with `#`
- **Change type** — `Create Agent`, `Update Agent`, or `Delete Agent`
- **Requester** — the username of who initiated the change
- **Timestamp** — when the request was created
- **Approval progress** — displayed as a fraction (e.g., `1/2`) showing
  current approvals vs. required approvals
- **Status badge** — color-coded: yellow for `pending`, green for
  `approved`, red for `rejected`

Click any card to open its detail view.

### Empty State

When no change requests exist, you see the message: "No change requests
found. Change requests appear here when agent modifications are made in
production."

---

## Reviewing and Acting on Requests

Clicking a change request card opens a **detail modal** titled
"Change Request #N".

### Detail Information

The modal displays a grid of metadata:

- **Type** — the change type (`Create Agent`, `Update Agent`, `Delete Agent`)
- **Status** — current status with a color-coded badge
- **Requested By** — the requester's username; if you are the requester, a
  blue `You` badge appears next to your name
- **Approvals** — progress shown as a fraction with the approval type in
  parentheses (e.g., `1/2 (any)`)
- **Created** — timestamp of request creation
- **Resolved** — timestamp of resolution (shown only for resolved requests)

### Change Diff

For **update** requests, the modal displays a side-by-side diff of each
changed field. Fields compared include: `name`, `endpoint`,
`connection_type`, `is_default`, `extras`, `auth`, and `icon`. Each
changed field shows a **Before** value (highlighted in red) and an
**After** value (highlighted in green).

For **create** requests, the modal shows the full agent payload under the
label `New Agent`. For **delete** requests, it shows the payload under
`Agent to Delete`.

### Approval History

If any reviewers have already acted, the modal shows an **Approval
History** section listing each action with the reviewer's username, action
badge (`approve` or `reject`), timestamp, and optional comment.

### Taking Action

If the request status is `pending`, the modal shows a **Your Action**
section at the bottom.

**Self-approval prevention:** If you are the requester, you see a warning:
"You cannot approve or reject your own change request." The action buttons
are not available.

For other reviewers:

1. Optionally type a comment in the text area. **A comment is required for
   rejection** — the UI will prompt you if you attempt to reject without
   one.
2. Click `Approve` to approve the request, or `Reject` to reject it.
3. On success, the modal closes and the list refreshes automatically.

Press **Escape** or click outside the modal to close it without acting.

---

## Version History and Rollback

When a change request is approved, Frontier creates a **version snapshot**
of the agent's configuration. You can view past versions and roll back to
any previous state.

### Accessing Version History

Open the **Agents** tab in the Workbench. In the agents table, each agent
displays a version badge (e.g., `v3`). Click the version badge to open the
**Version History** modal.

### Version History Modal

The modal is titled "Version History: {agent name}" and lists all recorded
versions from newest to oldest. Each version entry shows:

- **Version number** — e.g., `v1`, `v2`
- **Author** — who triggered the change
- **Timestamp** — when the version was created
- **Snapshot details** — the agent's endpoint, connection type, and extras
  at that point in time

The most recent version is visually highlighted as the current version.

### Rolling Back

Each older version has a `Rollback to this version` button. When you click
it:

1. A confirmation dialog asks you to confirm the rollback.
2. In production environments, the rollback creates a **new change
   request** that must go through the approval workflow before taking
   effect.
3. In non-production environments, the rollback applies immediately.

If no version history exists, you see: "No version history available.
Versions are created when agent configurations are modified."

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Approval` tab not visible in the Workbench | The approval feature is production-only. Verify that `app_env` is set to production and `approval.enabled` is `true` in `config.yaml`. |
| No eligible users when adding an approver | Only users with `admin` or `owner` roles in the project can be approvers. Add the user as a project admin first via the Permissions sub-tab. |
| "You cannot approve or reject your own change request" | Self-approval is not allowed. A different approver must review your request. |
| Rejection fails with no comment | A comment is required when rejecting a change request. Enter a reason in the text area before clicking `Reject`. |
| Change request stuck in `pending` | Check that enough approvers have acted based on the configured approval type (any, majority, or all). |
| Version badge shows `v0` | The agent has no recorded versions yet. Versions are created when approved changes are applied. |
| Rollback button does nothing | Confirm the confirmation dialog appeared. In production, the rollback creates a new change request rather than applying immediately. |
| "Failed to approve request" error | You may not be a designated approver for this project. Ask a project owner to add you via **General > Approval > Approvers**. |
