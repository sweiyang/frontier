# Frontier Frontend — Chat Guide

Everything about the chat experience: sending messages, attaching files, selecting agents, using the dynamic UI panel, and browsing the artefacts gallery.

## Table of Contents

1. [Sending Messages](#1-sending-messages)
2. [Selecting an Agent](#2-selecting-an-agent)
3. [File Attachments](#3-file-attachments)
4. [Streaming Responses and Markdown](#4-streaming-responses-and-markdown)
5. [Dynamic UI Panel](#5-dynamic-ui-panel)
6. [Sample Questions](#6-sample-questions)
7. [Conversation History](#7-conversation-history)
8. [Artefacts Gallery](#8-artefacts-gallery)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Sending Messages

The message input is at the bottom of the chat area.

- Type your message and press **Enter** to send.
- Press **Shift + Enter** to insert a new line without sending.
- Messages appear as bubbles: **your messages** on the right in a lighter background, **assistant responses** on the left in gray.
- Each message includes the sender's display name (or username) and an avatar.

If no conversation exists yet, one is created automatically when you send your first message. The conversation title updates after the first exchange and appears in the sidebar under **Recents**.

---

## 2. Selecting an Agent

The **agent selector** dropdown sits above the message input.

- Click it to see the list of agents available in the current project.
- The project's **default agent** is pre-selected (marked with a "Default" badge).
- Each agent shows a **type badge** indicating its connection type: `http`, `langgraph`, or `openai`.
- Agents marked as **artefacts** (shared org-wide) are filtered out of the dropdown. Access them via the [Artefacts Gallery](#8-artefacts-gallery) instead.
- Switching agent mid-conversation affects subsequent messages; earlier messages keep the agent they were sent to.

---

## 3. File Attachments

You can attach files to your messages. There are two ways:

- **Click the attach button** (paperclip icon) next to the message input to open a file picker.
- **Drag and drop** files directly onto the chat area. A visual drop zone appears while dragging.

### Supported file types

| Type | MIME types |
|------|------------|
| Images | JPEG, PNG, GIF, WebP |
| Documents | PDF, Word (.doc, .docx) |
| Text | Plain text, CSV, Markdown, JSON |

### Limits

- **Maximum file size:** 10 MB per file.
- Duplicate files (same name and size) are ignored.

### Managing attachments

- Attached files appear as chips below the message input, showing the file name, size, and a type icon.
- Click the **×** on a chip to remove a file before sending.
- Files are uploaded as base64 when you send the message.

---

## 4. Streaming Responses and Markdown

Agent responses stream in real time — you see tokens appear as they are generated. The chat area auto-scrolls to keep the latest content visible.

Responses are rendered as **Markdown**:

- Headings, bold, italic, strikethrough
- Ordered and unordered lists
- Fenced code blocks with syntax highlighting
- Inline code
- Links (open in a new tab)
- Tables

If the agent returns a **file download** (base64-encoded), a download link appears inline in the message.

---

## 5. Dynamic UI Panel

Some agents return interactive UI elements alongside their text response. When this happens, a **dynamic panel** appears to the right of the chat area.

### Supported element types

| Element | Description |
|---------|-------------|
| **Button** | Triggers an action — typically sends a templated message back to the agent. |
| **Text Input** | A text field whose value is tracked and sent as `client_context` with your next message. |
| **Search Bar** | Filters data across multiple columns in a connected table. |
| **Table** | Displays tabular data with row selection (checkboxes), sorting, and filtering. Can be expanded to a full-screen modal. Supports add-row and delete-row actions. |
| **Stats** | Displays metric cards (key/value pairs). |

### How it works

1. The agent includes an `elements` payload in its response.
2. The panel renders the elements and tracks their state (selected rows, input values, etc.).
3. When you send your next message, the current panel state is included as `client_context` so the agent can act on your selections.

The panel resizes alongside the chat area. If the agent sends an empty elements array, the panel is hidden.

For the full element specification (JSON contract, field reference, examples), see the [Supported Elements Guide](supported-elements-user-guide.md).

---

## 6. Sample Questions

If an agent provides **sample questions**, they appear as clickable pill buttons when a conversation is empty (no messages yet). Click any pill to send that question as your first message. Sample questions are configured per-agent by the project owner.

---

## 7. Conversation History

All your conversations are listed in the sidebar under **Recents**, sorted newest first.

- Click a conversation to resume it. The full message history loads in the chat area.
- Conversations persist across browser sessions.
- When an agent filter is active (you clicked an agent name elsewhere), only conversations for that agent appear. Click the **All** pill next to the "Recents" label to clear the filter.
- Each conversation stores its dynamic panel state, so switching between conversations preserves your selections.

---

## 8. Artefacts Gallery

Artefacts are agents that project owners have shared with the entire organisation.

### Accessing the gallery

- Click **Artifacts** in the sidebar navigation.
- Or open it from the user menu dropdown.

### Using the gallery

- Browse agent cards in a responsive grid layout. Each card shows the agent name, an icon, and the project it belongs to.
- Use the **search bar** at the top to filter agents by name.
- Click a card to open a new chat with that agent in its home project. You are switched to that project automatically.

### Empty and error states

- If no artefacts exist, a message reads "No artifacts available yet."
- If your search has no results, the message reads "No artifacts match your search."
- On network error, a **Retry** button appears.

---

## 9. Troubleshooting

| Issue | Solution |
|-------|----------|
| No agents appear in the selector | The project has no agents configured, or you lack permission. Contact the project owner. |
| File upload is rejected | Check that the file is under 10 MB and is a supported type (see [File Attachments](#3-file-attachments)). |
| Streaming stops mid-response | Refresh the page. If the issue persists, check your network connection or contact the agent owner. |
| Dynamic panel does not appear | The agent may not return `elements` in its response. This is agent-specific behavior, not a platform issue. |
| "Project not found" dialog on load | The project in the URL does not exist. You will be redirected to the default project. |
| "Access denied" dialog | You are not a member of the project. Ask a project owner to add you. |
| Conversation list is empty | You may be viewing a filtered list. Click **All** next to "Recents" to clear the agent filter. Or you may not have created any conversations in this project yet. |
