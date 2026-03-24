# Google Stitch Prompt — Frontier AI Chat Platform Redesign

## What to Build

Design a complete, modern UI for **Frontier** — an enterprise AI chat platform where teams create isolated **projects**, each with its own AI **agents** (LLM connectors), conversations, permissions, and dashboards. Think of it as a self-hosted, multi-tenant ChatGPT with project management, approval workflows, and a visual site builder baked in.

The redesign should feel like a premium SaaS product (Linear, Vercel, Raycast, Arc Browser quality) — not a generic admin panel.

---

## Core Screens to Design (in priority order)

### 1. Chat View (Primary Screen — users spend 80% of time here)

**Layout:** Full-height app shell. Collapsible left sidebar (260px expanded / 48px icon-strip collapsed). Main chat canvas taking remaining width. Optional right panel that slides in for "dynamic content" (tables, forms, stats rendered by the AI agent).

**Sidebar contains:**
- App logo + project name at top (clickable to switch projects)
- "New Chat" button (prominent, primary action)
- Agent selector pill/chip showing which agent is active (clicking opens a quick-switch popover, not a full page)
- Conversation history grouped by: Today, Yesterday, Previous 7 Days, Older — each conversation shows title + agent icon + timestamp
- Pinned conversations section at top of list
- Bottom: user avatar + name, settings gear, "Artifacts" gallery link, "Workbench" link

**Chat canvas:**
- Messages centered with max-width ~720px
- User messages: right-aligned, subtle dark bubble with light text
- Assistant messages: left-aligned, no bubble background, just clean typography with agent avatar inline
- Code blocks with syntax highlighting, copy button, and language tag
- Streaming indicator: subtle animated dots or gentle pulse on the last assistant message
- File attachments shown as compact chips with icon + filename + size, removable before send
- Input bar pinned to bottom: pill-shaped, multi-line expandable textarea, attach button (left), send button (right, filled primary), model/agent indicator chip inside the input bar

**Key UX improvements over typical chat UIs:**
- Keyboard-first: Cmd+K command palette to switch projects, agents, search conversations
- Drag-and-drop file upload with a full-canvas drop zone overlay
- Message actions on hover: copy, regenerate, edit, bookmark
- Conversation branching indicator (subtle fork icon) when user edits a past message
- Empty state: beautiful illustration + 3-4 sample question cards based on the active agent's purpose

### 2. Project Switcher / Home

**Trigger:** Clicking the project name in sidebar, or Cmd+K.

**Design:** A modal/overlay (not a full page) showing:
- Search bar at top (auto-focused)
- Grid of project cards: project name, description snippet, member count, agent count, last active timestamp
- "Create New Project" card with dashed border and plus icon
- Projects the user owns get a subtle crown/star badge
- Recent projects shown first, then alphabetical

### 3. Workbench (Project Admin Hub)

**Layout:** Full-page view with a horizontal tab bar or vertical nav on the left. Sections:

**a) Agents Tab**
- Card grid of agents in this project
- Each card shows: agent name, connector type badge (LangGraph / OpenAI / HTTP), status indicator (green dot = healthy), "Default" badge if applicable, "Artefact" badge if shared org-wide, icon/avatar
- Click card → slide-over or modal with full config: endpoint URL, auth type dropdown (Bearer/Basic/API Key), connector type, custom extras JSON editor, icon upload, toggle for "is default" and "is artefact"
- "Add Agent" card with plus icon

**b) Permissions Tab**
- Two sub-sections: **Members** and **AD Groups**
- Members: table with columns — Name, LAN ID, Role (dropdown: Owner/Admin/Member), Agent Access (multi-select chips), Actions (remove)
- AD Groups: similar table with group name, permission level, agent access
- "Invite Member" button opens a clean form

**c) Approval Tab (Production only)**
- Approval settings card: approval type selector (Any / All / Majority) with visual explanation of each
- Approvers list with add/remove
- Change Requests table: filterable by status (Pending / Approved / Rejected), each row shows request type, agent name, requester, date, status badge
- Click a request → detail view with a beautiful **diff visualization** (green/red for added/removed config, side-by-side), approve/reject buttons with comment textarea

**d) Usage Tab**
- Clean dashboard cards: total conversations, total messages, messages this week (with sparkline), active users
- Time-series chart (line or area) for messages over time
- Agent breakdown bar chart (which agents get used most)

**e) General Tab**
- Project name (read-only or editable by owner)
- Project description textarea
- Danger zone: delete project (red outlined section at bottom)

### 4. Site Builder (Visual Dashboard Editor)

**Layout:** Three-panel layout like Figma/Framer:
- Left panel (220px): component palette organized by category (Text, Media, Interactive, Data, Layout) with drag handles
- Center: canvas with 8px grid dots, zoom controls bottom-right, page tabs at top
- Right panel (280px): properties inspector for selected component — fields for content, styling, actions, data binding

**Components available:** Heading, Paragraph, Button, Image, Divider, Spacer, Form (multi-field), Chat Window (embedded), Table (data-bound)

**Top toolbar:** Page selector dropdown, Preview toggle, Undo/Redo buttons, Publish button, "Back to Workbench" breadcrumb

**Key UX:**
- Smooth drag-and-drop with snap-to-grid guides (blue alignment lines)
- Component selection with resize handles (corner + edge)
- Multi-select with Shift+Click
- Context menu (right-click) with Duplicate, Delete, Bring Forward, Send Back
- Preview mode: hides all builder chrome, shows the site as end users would see it

### 5. Artifacts Gallery

**Layout:** Full-page grid view.
- Top: "Artifacts" title + search bar + filter chips (by connector type, by project)
- Grid of agent cards: large icon, agent name, project name (subtle), description, "Open" button
- Cards have a subtle gradient or color wash background derived from the agent's icon
- Empty state if no artefacts exist yet

### 6. Login Screen

- Centered card on a subtle gradient or mesh background
- App logo + "Frontier" wordmark
- Username + password fields (or LDAP badge indicating enterprise auth)
- "Sign In" primary button
- Minimal — no clutter

---

## Design System Requirements

### Colors
- **Background:** Pure white `#FFFFFF` primary, `#F9FAFB` secondary/sidebar
- **Text:** `#0F0F0F` primary, `#6B7280` secondary, `#9CA3AF` tertiary/placeholder
- **Primary accent:** Amber `#F59E0B` (hover: `#D97706`) — used sparingly for CTAs, badges, active states
- **Borders:** `#E5E7EB` default, `#D1D5DB` on hover
- **Semantic:** Success `#10B981`, Error `#EF4444`, Info `#3B82F6`, Warning `#F59E0B`
- **Surfaces:** Cards on white with `1px solid #E5E7EB` + subtle shadow, modals with `rgba(0,0,0,0.5)` backdrop
- **Dark elements:** Sidebar can optionally use a near-black (`#111111`) for a two-tone look

### Typography
- **Font:** Inter for everything (body + headings). Fallback: system sans-serif.
- **Scale:** 12px (caption), 13px (small/label), 14px (body), 16px (subheading), 20px (heading), 28px (page title)
- **Weight:** 400 (body), 500 (labels/buttons), 600 (headings), 700 (page titles only)
- **Line height:** 1.5 for body, 1.3 for headings

### Spacing
- Base unit: 4px. Use multiples: 4, 8, 12, 16, 20, 24, 32, 40, 48, 64.

### Border Radius
- Small (inputs, badges): 6px
- Medium (cards, buttons): 8px
- Large (modals, panels): 12px
- Pill (primary CTAs, chips, tags): 9999px

### Shadows
- `sm`: `0 1px 2px rgba(0,0,0,0.05)` — cards, inputs
- `md`: `0 4px 12px rgba(0,0,0,0.08)` — dropdowns, popovers
- `lg`: `0 12px 40px rgba(0,0,0,0.12)` — modals

### Icons
- Use Lucide icon set, 18-20px size, 1.5px stroke weight

### Motion
- Hover transitions: 120ms ease
- Modal/panel open: 150ms ease-out with slight scale (0.98 → 1.0)
- Sidebar collapse: 200ms ease
- Page transitions: 150ms fade

---

## Key UX Principles

1. **Density without clutter** — show lots of information but with clear hierarchy and breathing room
2. **Keyboard-first** — every major action reachable via shortcut. Cmd+K palette is the power-user hub.
3. **Progressive disclosure** — don't show everything at once. Agent config is a slide-over, not a page. Permissions are a tab, not always visible.
4. **Contextual actions** — hover-reveal actions on messages, conversation rows, agent cards. No permanent action button clutter.
5. **Status at a glance** — agent health dots, approval status badges, unread indicators, active user presence
6. **Delightful empty states** — every empty list/page gets an illustration + helpful description + primary CTA
7. **Consistent patterns** — every list is searchable, every table is sortable, every destructive action gets a confirmation modal

---

## What NOT to Do

- No heavy gradients or glassmorphism — keep it flat and clean
- No sidebar icons without labels (collapsed mode uses icon-only, but expanded always shows text)
- No full-page navigations for things that should be overlays (project switcher, agent config, user profile)
- No raw JSON display to end users — always structured key-value pairs or diff views
- No generic "Settings" dump page — break settings into logical tabs with clear headers
- No loading states that block the entire screen — use skeleton placeholders inline
