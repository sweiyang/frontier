# Frontier Frontend — Getting Started

A quick guide to logging in, navigating the interface, and starting your first conversation.

## Table of Contents

1. [Logging In](#1-logging-in)
2. [Navigating the Interface](#2-navigating-the-interface)
3. [Your First Conversation](#3-your-first-conversation)
4. [Switching Projects](#4-switching-projects)
5. [What to Read Next](#5-what-to-read-next)

---

## 1. Logging In

Open the application URL in your browser. You will see the login screen.

1. Enter your **Username** and **Password** (LDAP credentials).
2. Click **Sign in**.
3. If your credentials are valid, you are redirected to the default project's chat view.

**Error states:**

| Message | Meaning |
|---------|---------|
| "Login failed" | Invalid username or password. Check your LDAP credentials. |
| "Connection error. Please try again." | The server is unreachable. Verify the URL and your network connection. |

Your session is persisted via a JWT token. If you close the browser and return later, you will be automatically signed back in until the token expires.

---

## 2. Navigating the Interface

After login, the main layout has three areas:

- **Sidebar** (left, 260 px) — navigation, conversation history, and user menu.
- **Main content** (center) — the chat area, artefacts gallery, or project site depending on context.
- **Dynamic panel** (right, when active) — interactive elements returned by an agent.

### Sidebar sections

| Element | Description |
|---------|-------------|
| **Brand header** | App name and optional company logo at the top. |
| **Home** | Returns to the chat view for the current project. |
| **Artifacts** | Opens the organisation-wide shared agent gallery. |
| **New chat** | Creates a new conversation in the current project. Shows a project tag indicating the active project. |
| **Recents** | Lists past conversations, newest first. Click any conversation to resume it. |
| **User menu** | Click your avatar at the bottom to open a dropdown with **Contact Us**, **FAQ**, **Workbench**, **Artefacts**, and your owned projects. |
| **Sign out** | The door icon to the right of your avatar. |

The sidebar can be collapsed to a narrow strip (44 px) by clicking the panel icon at the top-right of the sidebar. Click the same icon in the collapsed strip to expand it again. On screens narrower than 768 px the sidebar is hidden automatically.

---

## 3. Your First Conversation

1. Make sure a project is selected (shown as a tag next to **New chat**). If no project appears, ask your administrator to add you to one or navigate to a project URL directly (e.g. `/{project_name}`).
2. Click **New chat** in the sidebar (or just start typing — a conversation is created automatically when you send your first message).
3. Select an agent from the **agent selector** dropdown above the message input. The project's default agent is pre-selected.
4. Type a message in the input box at the bottom and press **Enter** to send (use **Shift + Enter** for a new line).
5. The agent's response streams in real time. Markdown formatting (headings, bold, code blocks, lists, links) is rendered automatically.
6. The conversation appears in the **Recents** list in the sidebar. Its title updates after the first exchange.

If the agent provides **sample questions**, they appear as clickable pills in an empty conversation. Click one to send it immediately.

---

## 4. Switching Projects

Each project has its own set of agents, conversations, and settings. To switch projects:

- **Via URL** — navigate to `/{project_name}` in your browser.
- **Via sidebar** — click your avatar to open the user menu. Under **Your Projects**, click a project name to switch to it.

If you navigate to a project that does not exist, a **"Project not found"** dialog appears and redirects you to the default project. If you lack access, an **"Access denied"** dialog appears instead.

---

## 5. What to Read Next

| Guide | Who it's for | What it covers |
|-------|-------------|----------------|
| [Chat Guide](frontend-chat-guide.md) | All users | Messages, file attachments, agent selection, dynamic UI, artefacts |
| [Workbench & Project Management](frontend-workbench-guide.md) | Project owners / admins | Create projects, manage agents, RBAC, settings |
| [Site Builder](frontend-site-builder-guide.md) | Project owners / admins | Visual drag-and-drop dashboard editor |
| [Approval Workflow](frontend-approval-guide.md) | Approvers / admins | Change requests, approvals, version history, rollback |
