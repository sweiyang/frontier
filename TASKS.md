# Frontier – Pending Tasks

## 1. Welcome Message per Agent
- Add a configurable welcome message field to each agent's settings
- Display the welcome message in `ChatArea.svelte` when a new conversation starts (before the first user message)
- Store in the `agents` table (e.g. as `extras.welcome_message` or a dedicated column)

## 2. Agent Analytics (per-agent stats card)
- Inspired by the first screenshot: show **active users** and **total interactions** as pill/badge counters on each agent card
- Surface this data on `Dashboard.svelte` and/or the agent list inside the Workbench
- Backend: extend the `/projects/{project}/agents` or usage endpoint to return per-agent stats (active users count, total message count)

## 3. Agent Versioning Display
- Show version history for each agent in the Workbench agent detail view
- Display the current version number, previous versions, timestamps, and who made the change
- Allow rollback to a previous version from the UI
- Pull from the existing `agent_versions` table via the approval/version service

## 4. Remove Duplicate Sign-Out Button
- There are currently two sign-out buttons: one in the Sidebar footer and one in the TopBar (top-right)
- **Keep only the TopBar top-right sign-out button**; remove the one from `Sidebar.svelte` footer

## 5. Workbench Styling (match second screenshot)
- Restyle `Workbench.svelte` to match the second screenshot:
  - Active section highlighted with a warm amber/orange pill background
  - Shield icon for "Admin Workbench" header
  - Section items (Settings, Help Centre) with matching icon + label layout
  - Clean white card style with rounded corners and subtle shadows

## 6. Hide Disabled Chat History from Sidebar
- If chat history is disabled for a project/agent, do **not** create or store conversation/message entries
- Do **not** render the conversation list in `Sidebar.svelte` at all when history is off
- This means no entries should appear in the left-hand sidebar

## 7. Workbench Route Fix
- Clicking "Workbench" in the sidebar should navigate to `/workbench` route
- Currently navigates to an empty or incorrect route — fix the `pushState` call in `Sidebar.svelte` (or wherever the Workbench link is)

## 8. Dashboard Stats: Replace "Projects" with "Interactions"
- In the third screenshot the stat card shows number of interactions, not number of projects
- On the home `Dashboard.svelte`, replace the **Projects** count card with an **Interactions** count (total messages/conversations across all agents)
- Keep "Available Agents" card as-is

## 9. Persist Light / Dark Mode
- The selected theme is not being saved across sessions
- Fix `theme.js` / `App.svelte` so the theme stored in `localStorage` under `frontier_theme` is correctly read and applied on page load
- Ensure the toggle in `TopBar.svelte` updates state and persists reliably

## 10. Disable Site Builder & Revert to Chat Interface
- Add a toggle in project settings (General tab) to **disable the Site Builder** for a project
- When disabled: hide the Site Builder nav item in the Workbench sidebar and do not show the site/dashboard — revert to the standard chat interface instead
- Store the setting as a boolean flag on the project (e.g. `site_builder_enabled`)

## 11. Hide "Search All Chats" When History Is Disabled
- When chat history is disabled, also remove the **Search All Chats** input/button from `Sidebar.svelte`
- The search bar should only appear when history is enabled

## 12. Metrics Displayed Monthly
- In the Usage / metrics views (ProjectSettings usage tab and any analytics panels), change the default aggregation from daily/all-time to **monthly**
- Add a month selector or default the chart/table to the current calendar month
- Update backend query parameters accordingly if needed

## 13. Remove "Set as Default" and "Set as Artefact" from Add Agent Form
- In `AgentManager.svelte` (or wherever the add/create agent form lives), remove the **"Set as Default Agent"** and **"Set as Artefact"** checkboxes/options
- These should not be exposed during initial agent creation (can be set later from the agent detail/settings view if needed)
