# Frontier Frontend — Site Builder Guide

The Site Builder is a visual drag-and-drop editor for creating custom project
dashboards and landing pages. You design pages by placing components on a
grid-based canvas, configuring their properties, and publishing the result as a
live site served within your Frontier project.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Accessing the Site Builder](#2-accessing-the-site-builder)
3. [Canvas and Grid System](#3-canvas-and-grid-system)
4. [Component Palette](#4-component-palette)
5. [Adding and Positioning Components](#5-adding-and-positioning-components)
6. [Component Properties](#6-component-properties)
7. [Page Management](#7-page-management)
8. [Preview Mode](#8-preview-mode)
9. [Undo / Redo](#9-undo--redo)
10. [Auto-Save](#10-auto-save)
11. [Published Site (SiteRenderer)](#11-published-site-siterenderer)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Overview

Every Frontier project can have its own dashboard site. The Site Builder gives
you a what-you-see-is-what-you-get editor where you:

- Drag components (headings, forms, tables, chat windows, etc.) onto a canvas.
- Position and resize them freely on an 8 px snap grid.
- Configure per-component properties in a right-side panel.
- Manage multiple pages with custom routes.
- Preview the result in real time and publish with one click.

The published site is rendered by the **SiteRenderer** component, which
displays the layout responsively and makes interactive components (forms,
tables, embedded chat) fully functional.

---

## 2. Accessing the Site Builder

Open the Site Builder from the Workbench:

1. Navigate to your project.
2. Open the **Workbench** (see [frontend-workbench-guide.md](./frontend-workbench-guide.md) for details).
3. Select the **Site Builder** section in the left navigation.

The builder loads your existing site data automatically. If no site exists yet,
you start with a blank `Home` page.

---

## 3. Canvas and Grid System

The central area of the builder is the **canvas** — a free-form surface where
you place components.

- **Grid size**: 8 px. Every component position and dimension snaps to the
  nearest 8 px increment.
- **Minimum canvas height**: 600 px. The canvas expands automatically as you
  add components further down the page.
- **Canvas width**: Stored alongside the site data (default 800 px). The
  SiteRenderer uses this reference width to calculate percentage-based
  positions, so layouts stay proportional on different screen sizes.
- **Click an empty area** of the canvas to deselect the current component.

---

## 4. Component Palette

The left panel is the **Component Palette**, titled `Add Elements`. It lists
every component type you can place on the canvas.

**Search**: Type in the search box at the top of the palette to filter
components by name.

**Category tabs**: Below the search box, a row of filter tabs lets you narrow
the list by category — `All`, `Text`, `Form`, `Button`, `Image`, `Chat`,
`Data`.

Components are grouped into two sections:

| Section | Components |
|---------|------------|
| **Basic Elements** | `Heading`, `Paragraph`, `Button`, `Image`, `Divider`, `Spacer` |
| **Advanced Elements** | `Form`, `Chat Window`, `Table` |

Click any palette card to add that component to the current page.

---

## 5. Adding and Positioning Components

### Adding

Click a component card in the palette. The new component is placed at the
first available position below existing components, snapped to the grid.

### Selecting

Click a component on the canvas to select it. A selection outline and resize
handles appear. The right panel updates to show that component's properties.

### Moving

Click and drag a selected component to reposition it. The position snaps to
the 8 px grid on both axes. Components cannot be dragged above the top edge of
the canvas (y = 0 minimum).

### Resizing

Drag the **resize handles** that appear on a selected component:

- **Corner handle** — adjusts both width and height.
- **Right-edge handle** — adjusts width only.
- **Bottom-edge handle** — adjusts height only.

The minimum size is 32 px (4 grid units) in each direction.

### Layering

When components overlap, use the toolbar actions to control stacking order:

- **Bring to Front** — moves the selected component above all others.
- **Send to Back** — moves it behind all others.

### Duplicating

Press `Cmd+D` (Mac) or `Ctrl+D` (Windows) to duplicate the selected
component. The clone is offset by 16 px in both directions.

### Deleting

Press `Delete` or `Backspace` to remove the selected component.

---

## 6. Component Properties

When you select a component, the **right panel** displays its editable
properties. The available fields depend on the component type.

### Heading

| Property | Description |
|----------|-------------|
| `Text` | The heading content |
| `Level` | `h1`, `h2`, or `h3` |
| `Alignment` | `left`, `center`, or `right` |

### Paragraph

| Property | Description |
|----------|-------------|
| `Text` | The paragraph content |
| `Alignment` | `left`, `center`, or `right` |

### Button

| Property | Description |
|----------|-------------|
| `Label` | Button text (default `Click Me`) |
| `Action` | URL to navigate to, or an action object |
| `Variant` | `primary`, `secondary`, or `outline` |
| `Size` | `medium` (default) |

### Image

| Property | Description |
|----------|-------------|
| `Upload` | Click `Upload Image` to select a file. **Max 5 MB**, accepted formats: JPEG, PNG, GIF, WebP, SVG. |
| `Alt text` | Accessible description of the image |
| `Object fit` | `cover` (default), `contain`, `fill`, `none` |

Images are uploaded to the server and the returned URL is stored in the
component's `src` property.

### Divider

| Property | Description |
|----------|-------------|
| `Style` | `solid`, `dashed`, `dotted` |
| `Color` | Any CSS color value (default `#e5e5e5`) |
| `Thickness` | Line thickness in pixels (default `1`) |

### Spacer

| Property | Description |
|----------|-------------|
| `Height` | Height in pixels (default `40`) |

### Form

| Property | Description |
|----------|-------------|
| `Submit label` | Text on the submit button (default `Submit`) |
| `Fields` | Ordered list of form fields — see field types below |
| `Submit actions` | One or more actions executed on submission |

**Form field types**: `Text (paragraph)`, `Text input`, `Email`, `Phone`,
`Text area`, `Dropdown`, `Checkbox`, `File attachment`.

Each field supports `Name`, `Label`, `Required`, and `Placeholder`. Dropdown
fields also accept a list of `Options`. File fields support drag-and-drop
upload with multi-file selection.

You can reorder fields with the up/down arrows and remove them with the
delete button. Click `Add Field` to append a new field.

**Submit actions** define what happens when the form is submitted. Each action
has a type:

- `http_request` — sends form data to a URL via the configured HTTP method,
  with optional authentication (bearer, basic, or API key).
- `navigate` — redirects the user to a route.

If no submit actions are configured, the form data is saved internally via the
`/projects/{project}/dashboard/forms/{componentId}/submit` endpoint.

### Chat Window

| Property | Description |
|----------|-------------|
| `Bot name` | Display name shown in the chat placeholder |
| `Agent` | The linked agent (selected by `agentId`) that powers the chat |
| `Color theme` | `light` (default) |

On the canvas, the Chat Window shows a static placeholder. In preview mode and
on the published site, it renders a **live ChatArea** connected to the
selected agent.

### Table

| Property | Description |
|----------|-------------|
| `Data endpoint` | URL that returns data in dataframe format |
| `HTTP method` | `GET` (default) or `POST` |
| `Data path` | Dot-notation path to the dataframe object in the response (default `data`) |
| `Refresh interval` | Auto-refresh period in seconds (`0` = disabled) |
| `Auth type` | `none`, `bearer`, `basic`, or `api_key` |
| `Auth credentials` | Token, password, or API key value |
| `Auth username` | Username for basic auth |
| `Auth header` | Custom header name for API key auth (default `X-API-Key`) |
| `Show header` | Toggle column headers on or off |
| `Empty message` | Text shown when no data is returned (default `No data found`) |
| `Row actions` | List of per-row action buttons |

**Expected data format**: The endpoint must return JSON with a dataframe-style
structure at the configured `Data path`:

```json
{
  "data": {
    "columns": ["name", "status", "updated"],
    "data": [
      ["Alice", "active", "2026-03-01"],
      ["Bob", "inactive", "2026-02-15"]
    ]
  }
}
```

**Row actions** appear as icon buttons in the last column. Each action has:

- `Icon` — `view`, `edit`, `delete`, `download`, or `link`
- `Label` — tooltip text
- `Mode` — `action` (client-side action) or `api` (calls an API endpoint)
- `API endpoint` — URL template supporting `{{row.column}}` interpolation
- `API method` — HTTP method for the API call
- `Query params` / `Body params` — comma-separated column names to include

---

## 7. Page Management

The Site Builder supports **multi-page sites**. Page controls appear in the
builder interface:

- **Default page**: Every new site starts with a `Home` page at path `/`.
- **Add page**: Click `Add Page` to create a new blank page. It is assigned an
  auto-generated slug like `/page-2`.
- **Rename**: Edit the page title directly in the page tab.
- **Set path**: Each page has a configurable URL path (must start with `/`).
- **Delete**: Remove a page by clicking its delete button. You cannot delete
  the last remaining page.
- **Switch pages**: Click a page tab to switch the canvas to that page.

Each page has its own independent set of components. Selecting a page clears
the current component selection.

---

## 8. Preview Mode

Click `Preview` in the top toolbar to toggle preview mode. The canvas is
replaced by the **SiteRenderer**, which displays your site exactly as visitors
will see it.

In preview mode:

- Components are rendered at their final positions with percentage-based widths.
- Interactive components (forms, tables, chat windows) are fully functional.
- The `Preview` button changes to `Exit Preview` — click it to return to the
  editor.

---

## 9. Undo / Redo

The builder tracks a history of up to **50 snapshots**.

- **Undo**: Click the undo button in the toolbar, or press `Cmd+Z` / `Ctrl+Z`.
- **Redo**: Click the redo button, or press `Cmd+Shift+Z` / `Ctrl+Shift+Z`.

History is recorded before every destructive or structural change (adding,
removing, moving, or resizing components; adding or removing pages).

---

## 10. Auto-Save

Changes are **auto-saved** with a 500 ms debounce. After you stop making
changes, the builder waits half a second and then persists the site to the
server.

The toolbar shows the current save state:

- `Saving...` — a save request is in progress.
- `Saved` (with a checkmark icon) — the latest version has been persisted.

You can also click `Publish` in the toolbar to trigger an immediate save.

The entire site structure — pages, components, positions, properties, and the
canvas width — is stored as a single JSON document in the `project_dashboards`
database table.

---

## 11. Published Site (SiteRenderer)

When visitors access your project's dashboard, the **SiteRenderer** displays
the published site.

### Layout

Components are positioned absolutely within a container. Horizontal positions
and widths are converted to percentages of the reference canvas width, so the
layout scales with the browser window. Vertical positions remain in pixels.

### Full-Page Scroll and Page Indicators

When a site has **two or more pages**, the SiteRenderer uses full-page scroll
snapping. Each page is rendered as a stacked full-viewport-height section:

- **Scroll snap**: Scrolling between pages snaps smoothly to the next section
  (CSS `scroll-snap-type: y mandatory`).
- **Page indicators**: Dot indicators appear on the right side of the viewport.
  The active page is shown as a filled red dot; inactive pages are hollow
  circles. Click any dot to scroll to that page.
- **All pages in DOM**: Unlike tab-based navigation, all pages are rendered
  simultaneously as stacked sections, enabling smooth scroll transitions.

For single-page sites, the layout behaves as a normal scrollable page with no
dot indicators.

### Interactive components

- **Buttons** execute their configured action (navigate, open URL, or custom
  action).
- **Forms** collect input, including drag-and-drop file uploads, and execute
  submit actions (HTTP requests or navigation). A success message is displayed
  for 3 seconds after submission.
- **Tables** fetch data from the configured endpoint, display it with sticky
  headers, and support row actions (API calls, downloads, navigation). An
  auto-refresh timer re-fetches data at the configured interval.
- **Chat Windows** render a live `ChatArea` connected to the specified agent.

### Analytics

The published site automatically tracks user interactions:

- **Page views** — recorded on every page navigation.
- **Button clicks** — recorded with the button label.
- **Form submissions** — recorded per form component.
- **Table actions** — recorded with the action name.

Events are buffered in memory and flushed to the server every 5 seconds (or on
page unload). Analytics data is sent to
`/projects/{project}/dashboard/analytics`.

### Empty states

If no site has been created, the renderer displays a message: "No custom page
yet — Use the Site Builder to create a landing page for this project." If a
page exists but has no components, it shows: "This page is empty — Add
components in the Site Builder."

---

## 12. Troubleshooting

| Issue | Solution |
|-------|----------|
| Components do not snap to grid | Positions snap to 8 px increments automatically. If a component appears misaligned, select it and nudge it — it will re-snap on the next move. |
| Image upload fails | Verify the file is under **5 MB** and in a supported format (JPEG, PNG, GIF, WebP, SVG). Check the browser console for network errors. |
| Table shows "Invalid dataframe format" | The endpoint must return `{ "columns": [...], "data": [[...], ...] }` at the configured `Data path`. Verify the response shape matches this structure. |
| Table shows "Error 401" | The endpoint requires authentication. Set the correct `Auth type` and `Auth credentials` in the table's properties panel. |
| Chat Window shows placeholder only | Chat Windows are interactive only in **Preview mode** or on the published site. On the builder canvas they always display a static placeholder. |
| Changes not saving | Check for network errors in the browser console. The toolbar should show `Saving...` then `Saved`. If it stays on `Saving...`, the API may be unreachable. |
| Undo button is disabled | You are at the beginning of the history stack. The builder stores up to 50 snapshots — older changes beyond that limit cannot be undone. |
| Published site layout looks different from editor | The SiteRenderer converts horizontal positions to percentages of the canvas width. If the viewer's browser is significantly wider or narrower than the canvas, proportions are preserved but absolute spacing will differ. |
| Form submission does nothing | Ensure at least one **submit action** is configured, or leave actions empty to use the default internal save endpoint. Verify any HTTP request URLs are correct and reachable. |
| Page path not resolving | Paths must start with `/`. The renderer matches by path first, then by page ID, then falls back to the first page. Check that your page path does not conflict with another page. |
