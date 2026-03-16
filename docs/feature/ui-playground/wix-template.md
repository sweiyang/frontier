# Wix UI Patterns Reference

> Reference document for building Wix-style frontend UI.
> Update this file as you discover new patterns in your project.

---

## Typography

- **Font family**: `Madefor`, fallback to `'Helvetica Neue', Helvetica, Arial, sans-serif`
- **Font smoothing**: Always enable `-webkit-font-smoothing: antialiased`
- **Minimum font size**: 12px — never go below this
- **Hierarchy**:
  | Level       | Size  | Weight | Use                        |
  |-------------|-------|--------|----------------------------|
  | H1 Title    | 28px  | 700    | Page titles                |
  | H2 Subtitle | 20px  | 600    | Section headings           |
  | H3          | 16px  | 600    | Card titles, panel headers |
  | Body        | 14px  | 400    | Default content text       |
  | Small/Label | 12px  | 400    | Captions, hints, metadata  |

---

## Color System

### Brand Colors
| Token              | Value             | Usage                          |
|--------------------|-------------------|--------------------------------|
| Primary            | `#116DFF`         | CTAs, active states, links     |
| Primary Hover      | `#0F64EB`         | Hover state on primary buttons |
| Primary Light      | `#E7F0FF`         | Subtle highlights, backgrounds |

### Neutral Colors
| Token              | Value     | Usage                          |
|--------------------|-----------|--------------------------------|
| Text Primary       | `#1A1A1A` | Main content text              |
| Text Secondary     | `#575757` | Supporting text, labels        |
| Text Disabled      | `#AEAEB2` | Disabled states                |
| Border Default     | `#E5E5E5` | Cards, inputs, dividers        |
| Background         | `#FFFFFF` | Page background                |
| Surface            | `#F4F4F4` | Panels, sidebars, input fills  |

### Semantic Colors
| Token     | Value     | Usage              |
|-----------|-----------|--------------------|
| Success   | `#3DB47F` | Confirmations      |
| Error     | `#E11C1C` | Errors, deletions  |
| Warning   | `#F4B000` | Warnings, caution  |
| Info      | `#116DFF` | Informational      |

---

## Spacing Scale

Base unit: **4px**

| Token | Value | Common Use                        |
|-------|-------|-----------------------------------|
| xs    | 4px   | Icon gaps, tight internal padding |
| sm    | 8px   | Compact elements                  |
| md    | 12px  | Default padding inside components |
| lg    | 16px  | Section padding, card padding     |
| xl    | 24px  | Gaps between sections             |
| 2xl   | 32px  | Page-level spacing                |
| 3xl   | 48px  | Large section breaks              |

---

## Border Radius

| Context         | Value | Notes                          |
|-----------------|-------|--------------------------------|
| Buttons         | 18px  | Fully pill-shaped              |
| Cards           | 8px   | Standard card rounding         |
| Inputs          | 6px   | Form fields                    |
| Tags / Badges   | 12px  | Small pill labels              |
| Modals          | 8px   | Dialog containers              |
| Tooltips        | 4px   | Small popups                   |

---

## Shadows

```css
/* Card shadow — default */
box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08), 0 2px 8px rgba(0, 0, 0, 0.06);

/* Card shadow — hover */
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12), 0 2px 6px rgba(0, 0, 0, 0.08);

/* Panel / Sidebar shadow */
box-shadow: 2px 0 8px rgba(0, 0, 0, 0.08);

/* Modal shadow */
box-shadow: 0 8px 32px rgba(0, 0, 0, 0.16);

/* Dropdown / Popover */
box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
```

---

## Buttons

### Primary Button
```css
background: #116DFF;
color: #FFFFFF;
border-radius: 18px;
height: 36px;
padding: 6px 24px;
font-size: 16px;
font-weight: 530;
min-width: 84px;
transition: background-color 0.1s linear;

/* Hover */
background: #0F64EB;

/* Disabled */
background: #AEAEB2;
cursor: not-allowed;
```

### Secondary Button
```css
background: transparent;
color: #116DFF;
border: 1px solid #116DFF;
border-radius: 18px;
height: 36px;
padding: 6px 24px;

/* Hover */
background: #E7F0FF;
```

### Icon Button (Ghost)
```css
background: transparent;
border: none;
border-radius: 6px;
padding: 6px;
color: #575757;

/* Hover */
background: #F4F4F4;
color: #1A1A1A;
```

### Button Hierarchy Rule
- **Primary** — one per section, the main action
- **Secondary** — supporting action
- **Contextual/Ghost** — destructive or less prominent actions

---

## Form Inputs

```css
/* Input field */
height: 36px;
border: 1px solid #E5E5E5;
border-radius: 6px;
padding: 0 12px;
font-size: 14px;
background: #FFFFFF;
color: #1A1A1A;
transition: border-color 0.1s;

/* Focus */
border-color: #116DFF;
outline: none;
box-shadow: 0 0 0 2px rgba(17, 109, 255, 0.15);

/* Error */
border-color: #E11C1C;

/* Disabled */
background: #F4F4F4;
color: #AEAEB2;
```

---

## Cards

```css
background: #FFFFFF;
border: 1px solid #E5E5E5;
border-radius: 8px;
padding: 16px;
box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);

/* Hover (for clickable cards) */
box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
transition: box-shadow 0.15s ease;
```

---

## Layout Structure (Page Builder / Editor Style)

```
┌─────────────────────────────────────────────────────────┐
│                    TOP TOOLBAR (48px)                   │
│  [Logo]  [Undo/Redo]  [Preview]  [Publish]    [Account] │
├──────────┬──────────────────────────────┬───────────────┤
│          │                              │               │
│  LEFT    │        CANVAS / EDITOR       │  RIGHT PANEL  │
│ SIDEBAR  │                              │  (Properties) │
│  (220px) │     (flex, takes remainder)  │    (240px)    │
│          │                              │               │
│ [Panels] │                              │  [Settings]   │
│ [Layers] │                              │  [Styles]     │
│ [Assets] │                              │  [Layout]     │
│          │                              │               │
└──────────┴──────────────────────────────┴───────────────┘
```

### Key Layout Rules
- Top toolbar: `48px` height, `z-index: 100`, full-width, border-bottom
- Left sidebar: `220px` width, scrollable, background `#F4F4F4`
- Right panel: `240px` width, scrollable, background `#FFFFFF`, border-left
- Canvas: takes all remaining space, background `#E8E8E8` (checkerboard or neutral)

---

## Sidebar Panels

```css
/* Panel container */
width: 220px;
height: 100%;
background: #F4F4F4;
border-right: 1px solid #E5E5E5;
overflow-y: auto;

/* Panel section header */
font-size: 12px;
font-weight: 600;
color: #575757;
text-transform: uppercase;
letter-spacing: 0.5px;
padding: 12px 16px 6px;

/* Panel item (draggable widget) */
display: flex;
align-items: center;
gap: 8px;
padding: 8px 12px;
border-radius: 6px;
cursor: grab;
font-size: 14px;
color: #1A1A1A;

/* Hover */
background: #EAEAEA;
```

---

## Icons

- Use 24px as the default icon size
- Use 20px for compact/toolbar icons
- Use 16px for inline/label icons
- The `?` icon always opens a tooltip or help panel
- The `⋯` (3-dot) icon always opens a context menu with more actions
- Clickable icons should have a hover background (`border-radius: 4px, background: #F4F4F4`)
- Color icons to match their context: primary blue for active, grey for inactive

---

## Feedback & States

### Notifications / Toasts
- Success: green left border or icon `#3DB47F`
- Error: red left border or icon `#E11C1C`
- Warning: yellow left border `#F4B000`
- Auto-dismiss after 4–5 seconds
- Position: bottom-center or top-right

### Loading States
- Use skeleton screens (not spinners) for content loading
- Use spinner only for action-triggered loading (button click, save)
- Spinner: 20px, `#116DFF`

### Empty States
- Always include an icon, a heading, a short description, and a CTA button
- Example: 🖼 "No pages yet" / "Create your first page" `[+ Add Page]`

---

## Tables & Lists

```css
/* Table header */
background: #F4F4F4;
font-size: 12px;
font-weight: 600;
color: #575757;
text-transform: uppercase;
padding: 10px 16px;
border-bottom: 1px solid #E5E5E5;

/* Table row */
padding: 12px 16px;
border-bottom: 1px solid #F0F0F0;
font-size: 14px;

/* Table row hover */
background: #F8F8F8;
```

### Table Rules
- Always include a checkbox column for multi-select
- Row actions appear on hover (edit, delete, ⋯ more)
- Sort indicator on column headers
- Pagination or infinite scroll for large datasets

---

## Modals & Dialogs

```css
/* Overlay */
background: rgba(0, 0, 0, 0.5);
z-index: 1000;

/* Dialog */
background: #FFFFFF;
border-radius: 8px;
padding: 24px;
min-width: 400px;
max-width: 600px;
box-shadow: 0 8px 32px rgba(0, 0, 0, 0.16);
```

### Modal Structure
```
[Title]                              [✕ Close]
─────────────────────────────────────────────
[Body content / form]


─────────────────────────────────────────────
                     [Cancel]  [Primary Action]
```

---

## Navigation Tabs

```css
/* Tab item */
padding: 10px 16px;
font-size: 14px;
color: #575757;
border-bottom: 2px solid transparent;
cursor: pointer;

/* Active tab */
color: #116DFF;
border-bottom: 2px solid #116DFF;
font-weight: 600;

/* Hover */
color: #1A1A1A;
```

---

## Transitions & Animations

```css
/* Standard interaction transition */
transition: all 0.1s linear;

/* Smooth hover effects */
transition: background-color 0.15s ease, box-shadow 0.15s ease;

/* Panel slide-in */
transition: transform 0.2s ease;

/* Modal fade-in */
transition: opacity 0.15s ease;
```

### Animation Rules
- Keep transitions fast: 100–200ms for interactions, 200–300ms for panels
- Use `ease` for entrances, `linear` for color/state changes
- Micro-interactions on hover (slight lift, color shift) make UI feel polished
- No animation should ever exceed 400ms

---

## Drag & Drop Conventions

- Drag handle: `⠿` icon or appear on hover at left edge of item
- Cursor: `grab` on hover, `grabbing` while dragging
- Dragging item: `opacity: 0.6`, `box-shadow` elevated, slight scale `transform: scale(1.02)`
- Drop zone: dashed border `2px dashed #116DFF`, background `#E7F0FF`
- Valid drop target highlight: blue outline

---

## Responsive & Mobile Rules

- Mobile layout: single column, full-width panels stack vertically
- Touch targets minimum: **42px × 42px**
- Preferred touch target: **48px × 48px**
- Replace hover-only actions with tap-accessible alternatives
- Sidebars collapse into bottom sheets or hamburger menus on mobile
- Font size minimum: 14px on mobile (never 12px for body text on mobile)

---

## Language & Content Rules

- Keep labels short — **verb + noun** format: "Add Page", "Delete Item", "Save Changes"
- One idea per sentence, 25 words or less
- Avoid jargon: use "Log in" not "Authenticate", "End" not "Terminate"
- Error messages must be actionable: "Enter a valid email" not "Invalid input"
- Always confirm destructive actions: "Delete this page? This can't be undone."

---

## Checklist Before Shipping a Component

- [ ] Uses correct font family and size
- [ ] Hover, focus, active, and disabled states all defined
- [ ] Color contrast passes WCAG AA (4.5:1 for text)
- [ ] Spacing follows 4px base unit scale
- [ ] Transitions are 100–200ms
- [ ] Touch targets are minimum 42px on mobile
- [ ] Empty and loading states handled
- [ ] Error states handled with clear messaging