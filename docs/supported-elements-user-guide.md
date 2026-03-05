# Supported Elements — User Guide

This guide describes the **dynamic UI elements** that Conduit’s chat frontend supports. Agents can send these elements in assistant messages; they are rendered in the **dynamic panel** (sidebar) next to the chat. Element state (selections, text inputs, etc.) is sent back to the agent as `client_context` on the next user message.

---

## How elements are sent

Elements are delivered in assistant message content using a special block:

```
[ELEMENTS]<json>[/ELEMENTS]
```

- The payload is a **single JSON object** with an `elements` array.
- Each item in `elements` must have `type` and `id`; other fields depend on the type.
- Elements are **upserted by `id`**: same `id` updates the existing element, new `id` adds a new one. Order is preserved.
- Sending `elements: []` clears the panel.

**Example (minimal):**

```json
{
  "elements": [
    {
      "type": "button",
      "id": "submit_btn",
      "label": "Submit",
      "action": "send_message",
      "payload_template": "Done"
    }
  ]
}
```

---

## 1. Button

Triggers an action. Currently the only supported action is sending a message back to the agent, with optional templating from other elements’ state.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `type` | string | Yes | Must be `"button"`. |
| `id` | string | Yes | Unique element id. |
| `label` | string | Yes | Button text. |
| `variant` | string | No | `"primary"` (default), `"secondary"`, or `"danger"`. |
| `action` | string | No | Use `"send_message"` to send a message when clicked. |
| `payload_template` | string | No | Message text. Supports `{{context.path.to.value}}` to inject values from `client_context` (e.g. `{{my_input.value}}` for a text input with `id: "my_input"`). |

**Example:**

```json
{
  "type": "button",
  "id": "submit_btn",
  "label": "Submit",
  "variant": "primary",
  "action": "send_message",
  "payload_template": "Selected: {{companies_table.selected}}"
}
```

When the user clicks the button, the frontend sends a chat message with the resolved template (e.g. selected row data) so the agent can continue the flow.

---

## 2. Text input

Single-line or multi-line text field. Value is stored in panel state and can be referenced in button `payload_template` or read from `client_context`.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `type` | string | Yes | Must be `"text_input"`. |
| `id` | string | Yes | Unique element id. Use this in templates, e.g. `{{my_input.value}}`. |
| `label` | string | No | Label above the input. |
| `placeholder` | string | No | Placeholder text (default `""`). |
| `required` | boolean | No | Default `false`. |
| `multiline` | boolean | No | Default `false`. If `true`, renders a textarea. |
| `value` | string | No | Initial value (default `""`). |

**Example:**

```json
{
  "type": "text_input",
  "id": "username",
  "label": "Username",
  "placeholder": "Enter name",
  "required": true
}
```

---

## 3. Search bar

Search/filter input that drives the filter for a **table** with a given `id`. It does not store its own value in a way that’s useful for `payload_template`; it only filters the target table.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `type` | string | Yes | Must be `"search_bar"`. |
| `id` | string | Yes | Unique element id for the search bar. |
| `target` | string | Yes | `id` of the table to filter. |
| `placeholder` | string | No | Placeholder (default `"Search..."`). |

**Example:**

```json
{
  "type": "search_bar",
  "id": "company_search",
  "target": "companies_table",
  "placeholder": "Filter companies..."
}
```

---

## 4. Table

Data grid with optional selection, sorting, search, pagination, add/delete, and expand-to-modal.

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `type` | string | Yes | Must be `"table"`. |
| `id` | string | Yes | Unique element id. Referenced by search_bar `target` and in `payload_template` as `{{id.selected}}` (single row) or selection array. |
| `title` | string | No | Heading above the table. |
| `columns` | array | Yes | Column definitions: `{ "key": "fieldName", "label": "Display Name", "sortable": true }`. `sortable` is optional (default per column can be false). |
| `rows` | array | Yes | Row objects. Each row must have an `id` (unique) and keys matching `columns[].key`. |
| `select_mode` | string | No | `"none"`, `"single"`, or `"multi"` (default `"single"`). |
| `searchable` | boolean | No | If `true`, shows an inline search field that filters rows (default `false`). Can be combined with a separate search_bar that sets `target` to this table. |
| `deletable` | boolean | No | If `true`, shows a delete control per row (default `false`). |
| `addable` | boolean | No | If `true`, shows an “Add” input and button (default `false`). New rows use the first column’s key for the value. |
| `page_size` | number | No | Rows per page (default `10`). In expanded modal view, page size is 50. |

**Column object:**

- `key` (string): field name in each row.
- `label` (string): header text.
- `sortable` (boolean, optional): allow sorting by this column.

**Example:**

```json
{
  "type": "table",
  "id": "companies_table",
  "title": "Companies",
  "columns": [
    { "key": "name", "label": "Name", "sortable": true },
    { "key": "role", "label": "Role" }
  ],
  "rows": [
    { "id": 1, "name": "Acme", "role": "Vendor" },
    { "id": 2, "name": "Globex", "role": "Partner" }
  ],
  "select_mode": "multi",
  "searchable": true,
  "deletable": false,
  "addable": false,
  "page_size": 10
}
```

- **Selection:** With `select_mode` `"single"` or `"multi"`, selection is stored in panel state and sent in `client_context`; a button can send it with e.g. `payload_template`: `"Selected: {{companies_table.selected}}"`.
- **Expand:** User can open the table in a full-screen modal; selection and filtering stay in sync with the inline view.

---

## Client context (panel state)

When the user sends a message (or clicks a button with `action: "send_message"`), the frontend includes **client_context** in the request. It mirrors the panel state:

- **Text inputs:** `client_context[element_id] = { value: "..." }`.
- **Tables:** `client_context[element_id] = { selected: <row or array of rows> }`. For addable tables, `added` may be present; for deletable tables, `deleted` may be present.
- **Search bars:** Filter text is applied to the target table’s view only; it is not required to be in context for the agent unless you expose it via another mechanism.

So the agent can read user choices (e.g. selected rows, text field values) from `client_context` to drive the next step.

---

## File attachments (user → agent)

Users can attach files to messages. The frontend allows:

- **Max file size:** 10 MB.
- **Allowed types:** JPEG, PNG, GIF, WebP, PDF, plain text, CSV, Markdown, JSON, Word (.doc, .docx).

Files are sent as base64 in the chat request; the agent receives them according to the Conduit API contract.

---

## File download (agent → user)

The agent can provide a file for the user to download by embedding in the assistant message:

```
[FILE]<json>[/FILE]
```

JSON shape:

```json
{
  "name": "report.pdf",
  "type": "application/pdf",
  "content": "<base64-encoded bytes>"
}
```

The frontend decodes the base64, creates a blob, and shows a download link for the file in the chat.

---

## Summary

| Element       | Purpose |
|---------------|--------|
| **button**    | Send a message (with optional template from other elements’ state). |
| **text_input**| Single- or multi-line text; value available in context and in button templates. |
| **search_bar**| Filter a specific table by text. |
| **table**     | Display rows with optional selection, sort, search, pagination, add/delete, expand. |

All elements are identified by `id` and updated by re-sending the same `id` in a later `[ELEMENTS]` block. Use `client_context` in your agent to read user input and selections after each message or button click.
