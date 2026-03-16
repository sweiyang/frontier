# Frontend Design Audit

> Generated 2026-03-14 — Full inventory of colors, typography, spacing, component patterns, and inconsistencies across the Svelte frontend.

## 1. Design Tokens (CSS Variables)

Defined in `src/frontend/src/app.css`:

### Colors
| Variable | Value | Usage |
|---|---|---|
| `--bg-primary` | `#ffffff` | Page/card backgrounds |
| `--bg-secondary` | `#f9f9fa` | Section backgrounds, assistant bubbles |
| `--text-primary` | `#0f0f0f` | Body text |
| `--text-secondary` | `#6b6b6b` | Labels, hints, captions |
| `--border-color` | `#e5e5e5` | Borders, dividers |
| `--primary-accent` | `#f59e0b` | Amber accent (buttons, badges, active states) |
| `--primary-accent-hover` | `#d97706` | Amber hover state |

### Shadows
| Variable | Value |
|---|---|
| `--shadow-sm` | `0 1px 2px 0 rgb(0 0 0 / 0.05)` |
| `--shadow-md` | `0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)` |
| `--shadow-lg` | `0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)` |

### Spacing
| Variable | Value |
|---|---|
| `--spacing-xs` | `0.25rem` (4px) |
| `--spacing-sm` | `0.5rem` (8px) |
| `--spacing-md` | `1rem` (16px) |
| `--spacing-lg` | `1.5rem` (24px) |
| `--spacing-xl` | `2rem` (32px) |

### Border Radius
| Variable | Value |
|---|---|
| `--radius-sm` | `0.375rem` (6px) |
| `--radius-md` | `0.5rem` (8px) |
| `--radius-lg` | `0.75rem` (12px) |
| `--radius-xl` | `1rem` (16px) |
| `--radius-full` | `9999px` |

### Fonts
| Variable | Value |
|---|---|
| `--font-sans` | `'Inter', sans-serif` |
| `--font-display` | `'Outfit', sans-serif` |

---

## 2. Color Palette — Full Inventory

### Core Palette (via CSS variables)
- White: `#ffffff`
- Near-white: `#f9f9fa`, `#f9fafb`, `#f5f5f5`, `#f3f4f6`
- Light gray: `#e5e5e5`, `#e5e7eb`, `#e8e8e8`, `#ddd`
- Mid gray: `#6b6b6b`, `#6b7280`, `#9ca3af`, `#999`, `#888`
- Dark gray: `#374151`, `#333`
- Near-black: `#0f0f0f`, `#111827`
- Black: `black`

### Semantic Colors
| Purpose | Color | Background | Border | Used In |
|---|---|---|---|---|
| Error/Danger | `#dc2626`, `#ef4444`, `#b91c1c` | `#fef2f2`, `rgba(220,38,38,0.08)` | `#fecaca` | Login, CreateProject, ProjectSettings |
| Info/Blue | `#3b82f6`, `#2563eb` | `rgba(59,130,246,0.1)`, `#eff6ff`, `#dbeafe` | — | ContactUs, DynamicTable, ProjectSettings |
| Success/Green | `#10b981` | — | — | ProjectSettings (permissions) |
| Purple | `#8b5cf6`, `#6366f1` | `rgba(139,92,246,0.15)`, `rgba(99,102,241,0.08)` | — | Owner badge, accent fallback, Sidebar avatar |
| Amber/Accent | `#f59e0b`, `#d97706`, `#a16207`, `#92400e` | `rgba(245,158,11,0.08–0.15)`, `#fef3c7→#fde68a` | — | Badges, buttons, toasts |
| Warning | `#e67e22`, `#e74c3c` | — | — | App.svelte popup icons |

### Opacity Patterns
| Value | Usage |
|---|---|
| `rgba(0,0,0, 0.04)` | Hover backgrounds (Sidebar, ModelSelector, Workbench) |
| `rgba(0,0,0, 0.05)` | Focus rings, subtle hover |
| `rgba(0,0,0, 0.06)` | Active/selected backgrounds |
| `rgba(0,0,0, 0.1)` | Toast close hover |
| `rgba(0,0,0, 0.4)` | Popup overlay (App.svelte) |
| `rgba(0,0,0, 0.5)` | Modal overlays (ContactUs, ProjectSettings) |
| `rgba(255,255,255, 0.2–0.4)` | Light overlays on dark backgrounds |

---

## 3. Typography

### Font Size Scale (all values found)
| Token | Value | Usage |
|---|---|---|
| Display | `2rem` | H1 greeting (App, ChatArea) |
| Title | `1.75rem` | Picker title (Workbench), headers (Login, CreateProject) |
| Heading 2 | `1.5rem` | Settings title (ProjectSettings) |
| Heading 3 | `1.25rem` | Popup title (App), builder header, modal header |
| Heading 4 | `1.15rem` | Empty state h3 (Workbench) |
| Subheading | `1.1rem` | Section headers (ProjectSettings) |
| Body+ | `1.05rem` | Product name (Sidebar) |
| Body | `1rem` | Inputs, buttons, project context, textarea |
| Body- | `0.95rem` | Model selector, builder descriptions, popup message |
| Small+ | `0.9rem` | Sidebar items, nav items, card names, buttons |
| Small | `0.875rem` | Message text, form labels, table body, stat labels |
| Small- | `0.85rem` | Dropdown items, descriptions, inspector inputs |
| XSmall+ | `0.8rem` | Chevrons, badges, hints, table headers, canvas type |
| XSmall | `0.75rem` | Section labels, captions, footnotes, badges |
| XXSmall | `0.7rem` | Footnote text, dropdown section labels |
| Tiny | `0.65rem` | Pills (ModelSelector), filter badges |

### Font Weight Scale
| Weight | Usage |
|---|---|
| `700` | Product name (Sidebar), workbench badge |
| `600` | Headings, popup title, markdown headings, panel headers, stat values |
| `500` | H1 greeting, labels, tabs, sub-tabs, active items, pills |
| `400` | Body text, agent names, settings labels |

### Line Height
- Default: `1.5` (body)
- Compact: `1.45` (message content)
- Tight: `1` (icons, spinners)

---

## 4. Spacing Patterns

### Padding (most common hardcoded values)
| Value | Frequency | Usage |
|---|---|---|
| `0.75rem` | High | Sidebar, input vertical, section padding |
| `1rem` | High | Card padding, grid gaps, section padding |
| `1.5rem` | Medium | Modal body, container padding, large gaps |
| `2rem` | Medium | Container padding, popup card, empty states |
| `0.5rem` | High | Small gaps, margins, input padding |
| `0.4rem 0.6rem` | High | List items, dropdown items, conversation items |
| `0.45rem 0.6rem` | Medium | Sidebar action items, palette items |
| `0.35rem 0.5rem` | Medium | Model selector, small buttons |
| `0.75rem 1rem` | Medium | Input fields (Login, CreateProject) |
| `0.875rem 1.5rem` | Low | Primary buttons (Login, CreateProject) |

### Gap Values
| Value | Usage |
|---|---|
| `0.1rem` | Message actions |
| `0.18rem` | Message stack |
| `0.25rem` | Input actions, small gaps |
| `0.45rem` | Message stack |
| `0.5rem` | Loading dots, header gaps |
| `0.75rem` | Project grid, builder column |
| `1rem` | Form gaps, grid gaps, builder body |
| `1.5rem` | Splash content |
| `2rem` | Picker header margin |

---

## 5. Layout Structure

### App Shell
```
┌─────────────────────────────────────────────┐
│ App Container (flex, 100vh × 100vw)         │
│ ┌──────────┬──────────────────────────────┐ │
│ │ Sidebar  │ Main Area (flex: 1)          │ │
│ │ 260px    │ ┌──────────────────────────┐ │ │
│ │ (44px    │ │ Top Bar (z-index: 10)    │ │ │
│ │ collapsed│ ├──────────────────────────┤ │ │
│ │          │ │ Chat Scroll Area         │ │ │
│ │          │ │ (messages max-w: 800px)  │ │ │
│ │          │ ├──────────────────────────┤ │ │
│ │          │ │ Input (max-w: 700px)     │ │ │
│ │          │ └──────────────────────────┘ │ │
│ └──────────┴──────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Key Dimensions
| Element | Value |
|---|---|
| Sidebar width | `260px` (collapsed: `44px`) |
| Sidebar breakpoint | `768px` (hidden on mobile) |
| Messages max-width | `800px` |
| Input max-width | `700px` |
| Settings max-width | `1000px` |
| Modal max-width | `1100px` (DynamicPanel), `500px` (ProjectSettings), `450px` (ContactUs) |
| Modal max-height | `90vh` |
| Project grid min column | `280px` |
| Dashboard grid row height | `80px` |

---

## 6. Component Patterns

### Buttons
| Type | Background | Text | Radius | Padding |
|---|---|---|---|---|
| Primary | `black` | `white` | `var(--radius-full)` | `0.875rem 1.5rem` |
| Accent | `var(--primary-accent)` | `white` | `999px` | `0.5rem 1rem` |
| Secondary | `transparent` | `var(--text-primary)` | `var(--radius-md)` | `0.35rem 0.75rem` |
| Icon | `transparent` | inherit | `50%` or `8px` | centered `32–36px` square |
| Danger | `#fee2e2` | `#b91c1c` | varies | varies |

### Inputs
- Padding: `0.75rem 1rem`
- Border: `1px solid var(--border-color)`
- Radius: `var(--radius-md)` or `1.5rem` (chat input)
- Focus: `box-shadow: 0 0 0 3px rgba(0,0,0,0.05)` or `rgba(245,158,11,0.1)`
- Background: `var(--bg-primary)` or `var(--bg-secondary)`

### Cards
- Background: `var(--bg-primary)` or `var(--bg-secondary)`
- Border: `1px solid var(--border-color)`
- Radius: `0.75rem` to `1rem` (Login/CreateProject: `32px`)
- Shadow: `var(--shadow-sm)` default, `var(--shadow-md)` on hover

### Message Bubbles
- Assistant: `var(--bg-secondary, #f5f5f5)`, top-left radius `0.25rem`
- User: `#e8e8e8`, top-right radius `0.25rem`
- Padding: `0.3rem 0.72rem 0.2rem`
- Other corners: `1rem`

### Modals
- Backdrop: `rgba(0,0,0, 0.5)`, `z-index: 1000`
- Container: white bg, `border-radius: 0.75rem`, `var(--shadow-lg)`
- Animation: `fadeIn 0.15s` (backdrop) + `scaleIn 0.15s` or `slideUp 0.2s` (content)

### Dropdowns
- Background: white
- Border: `1px solid var(--border-color)`
- Radius: `10px`
- Shadow: `0 4px 16px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.04)`
- Animation: `slideUp 0.12s ease-out`

### List Items (Sidebar, Dropdowns)
- Padding: `0.4rem 0.6rem`
- Radius: `8px`
- Hover: `rgba(0,0,0, 0.04)`
- Active: `rgba(0,0,0, 0.06)`, `font-weight: 500`
- Transition: `background 0.12s ease`

---

## 7. Transitions & Animations

### Transition Speeds
| Speed | Duration | Easing | Usage |
|---|---|---|---|
| Fast | `0.12s` | `ease` | Hover backgrounds, color changes |
| Medium | `0.15s` | `ease-out` | Modal animations, tag removes |
| Standard | `0.2s` | `ease` | Focus states, sidebar width, card hover |
| Slow | `0.3s` | `ease-out` | Slide animations, toast entry |

### Keyframe Animations
| Name | Duration | Usage |
|---|---|---|
| `spin` | `0.8s` / `1s` linear infinite | Loading spinners |
| `dotBounce` | `1.4s` ease-in-out infinite | Typing indicator |
| `slideUp` | `0.12–0.3s` ease-out | Dropdowns, modals, toasts |
| `fadeIn` | `0.15–0.2s` ease-out | Modal backdrops |
| `scaleIn` | `0.15s` ease-out | Modal content |
| `popupFadeIn` | `0.2s` ease-out | Popup overlay |
| `popupSlideIn` | `0.25s` ease-out | Popup card |
| `dropFadeIn` | `0.15s` ease-out | Drag zone |
| `dropBounce` | `0.5s` ease-in-out infinite alternate | Drag icon |
| `pulse` | `2s` ease-in-out infinite | Splash logo |
| `bounce` | `1.4s` ease-in-out infinite | Splash dots |

### Z-Index Scale
| Value | Usage |
|---|---|
| `10` | Top bar, sidebar collapse button, agent search results |
| `20` | Model selector wrapper, search dropdown |
| `50` | Model dropdown |
| `100` | Drop overlay, user dropdown |
| `1000` | Modal overlays, popup overlay |
| `9999` | Splash screen |
| `10000` | Approval toast |

---

## 8. Inconsistencies & Issues

### Color Inconsistencies

1. **Gray scale fragmentation** — At least 12 distinct gray values used across components:
   - Near-white: `#f9f9fa`, `#f9fafb`, `#f5f5f5`, `#f3f4f6`, `#fafafa`
   - Mid-gray: `#6b6b6b`, `#6b7280`, `#9ca3af`, `#999`, `#888`
   - Dark: `#374151`, `#333`, `#111827`
   - These should consolidate to the CSS variables (`--bg-secondary`, `--text-secondary`, `--text-primary`).

2. **Indigo vs Amber identity crisis** — `#6366f1` (indigo) is used as an accent fallback in Sidebar, ChatArea, and ContactUs, competing with the declared `--primary-accent` amber (`#f59e0b`). The indigo appears in avatar backgrounds, link colors, drag overlays, and project tags.

3. **Hardcoded colors instead of variables** — Many components use raw hex/rgb instead of CSS variables:
   - `#e8e8e8` (user bubble) — should be a variable like `--user-bubble-bg`
   - `#1e1e1e` / `#d4d4d4` (code blocks) — should be `--code-bg` / `--code-text`
   - `#ddd` / `#333` (user avatar) — should reference design tokens
   - `#999`, `#888` used as text-secondary fallbacks instead of `var(--text-secondary)`

4. **DynamicTable and DynamicSearchBar** use a completely different color palette (`#d1d5db`, `#374151`, `#6b7280`, `#f3f4f6`, `#9ca3af`) that doesn't reference any CSS variables — feels like a different design system.

### Typography Inconsistencies

5. **Font size proliferation** — 16+ distinct font sizes found. The scale jumps irregularly: `0.65, 0.7, 0.75, 0.8, 0.85, 0.875, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.25, 1.5, 1.75, 2.0 rem`. No font-size CSS variables are defined. Consider defining a type scale: `--text-xs`, `--text-sm`, `--text-base`, `--text-lg`, `--text-xl`, `--text-2xl`.

6. **Inconsistent body text sizes** — Body text alternates between `0.875rem`, `0.9rem`, `0.95rem`, and `1rem` with no clear rule for when each is used.

7. **`--font-display` underused** — Only referenced in ProjectSettings (settings title). Most headings use `--font-sans` implicitly.

### Spacing Inconsistencies

8. **CSS spacing variables rarely used** — `--spacing-*` variables are defined but most components use hardcoded values. Only Login, CreateProject, ContactUs, and ProjectSettings reference them. ChatArea, Sidebar, ModelSelector, and Workbench use raw values exclusively.

9. **Inconsistent list item padding** — Sidebar uses `0.45rem 0.6rem`, `0.4rem 0.6rem`, and `0.5rem 0.6rem` for similar list items. ModelSelector uses `0.4rem 0.6rem`. These should be unified.

### Border Radius Inconsistencies

10. **Radius variable adoption is partial** — `--radius-*` variables exist but many components hardcode: `8px`, `10px`, `16px`, `32px`, `4px`, `6px`, `7px`. The `8px` used everywhere for list items equals `--radius-md` (0.5rem = 8px) but isn't referenced as such.

11. **Card radius varies** — Login/CreateProject cards use `32px`, other cards use `0.75rem` (12px) or `var(--radius-lg)`. No consistency.

### Shadow Inconsistencies

12. **Custom shadows alongside variables** — Several components define one-off shadows instead of using `--shadow-*`:
    - Popup card: `0 20px 60px rgba(0,0,0,0.15)` (App.svelte)
    - Toast: `0 10px 25px rgba(0,0,0,0.15)` (ProjectSettings)
    - Dropdown: `0 4px 16px rgba(0,0,0,0.08)` (Sidebar, ModelSelector — consistent with each other but not a variable)
    - DynamicSearchBar dropdown: `0 4px 12px rgba(0,0,0,0.1)` (different from other dropdowns)

### Component Pattern Inconsistencies

13. **Modal animation varies** — DynamicPanel uses `scaleIn`, ProjectSettings uses `slideUp`, ContactUs uses `slideUp`. Popup in App.svelte uses its own `popupSlideIn`. Should standardize.

14. **Spinner animation speed** — `spin 0.8s` in ChatArea vs `spin 1s` in ProjectSettings.

15. **Focus ring styles differ** — Chat input uses `0 0 0 1px var(--border-focus, #c0c0c0)`, ProjectSettings uses `0 0 0 3px rgba(245,158,11,0.1)`, Login/CreateProject uses `var(--shadow-md)`. No unified focus pattern.

16. **Button padding not standardized** — Primary buttons range from `0.5rem 1rem` to `0.875rem 1.5rem` to `0.6rem 2rem` depending on the component.

### Structural Issues

17. **No dark mode support** — All colors are hardcoded for light theme. CSS variables exist but no alternate theme definitions.

18. **No responsive type scale** — Font sizes are fixed; no `clamp()` or media query adjustments for different screen sizes.

19. **Z-index gaps** — Scale jumps from 100 to 1000 to 9999 to 10000 with no documented layering system.
