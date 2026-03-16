# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Frontier is a multi-project AI chat platform with a FastAPI backend and Svelte frontend. It provides project-based isolation, RBAC with LDAP integration, and supports multiple AI agent connectors (LangGraph, OpenAI, HTTP). Each project gets its own dynamically-created database tables for conversations and messages.

## Architecture

### Backend (Python/FastAPI)
- **Entry point**: [project.py](project.py) - CLI wrapper that calls `frontier.sdk.serve()`
- **FastAPI app**: [src/api/main.py](src/api/main.py) - Application setup, router registration, and SPA mounting
- **Core modules** ([src/core/](src/core/)):
  - `agent/`: Agent connector framework
    - [base_connector.py](src/core/agent/base_connector.py): Abstract base class defining `stream()` and `close()` methods
    - `connectors/`: Implementations for `langgraph_connector.py`, `openai_connector.py`, `http_connector.py`
  - `db/`: SQLAlchemy models and database operations
  - `auth/`: JWT authentication and LDAP integration
  - [config.py](src/core/config.py): YAML-based configuration loader with defaults
- **API routers** ([src/api/routers/](src/api/routers/)): REST endpoints for auth, chat, projects, agents, conversations, RBAC, metrics, usage
- **SDK** ([src/sdk/](src/sdk/)): Simple wrapper for starting the server

### Frontend (Svelte + Vite)
- **Location**: [src/frontend/](src/frontend/)
- **Build output**: `src/frontend/dist/` (served by FastAPI as static SPA)
- **Key components** ([src/frontend/src/lib/](src/frontend/src/lib/)):
  - [ChatArea.svelte](src/frontend/src/lib/ChatArea.svelte): Main chat interface with streaming support
  - [Sidebar.svelte](src/frontend/src/lib/Sidebar.svelte): Navigation and conversation list
  - [ProjectSettings.svelte](src/frontend/src/lib/ProjectSettings.svelte): Project configuration UI
  - [ModelSelector.svelte](src/frontend/src/lib/ModelSelector.svelte): Agent/model selection dropdown
  - [DynamicPanel.svelte](src/frontend/src/lib/DynamicPanel.svelte): Dynamic UI rendering

### Database Architecture
- **Supports**: PostgreSQL and YugabyteDB only (SQLite not supported)
- **Environment-based config**: Database settings under `database.<env>` in config.yaml (host, port, dbname, user, credential, schema)
- **Schema support**: Optional schema isolation via `database.<env>.schema` (uses PostgreSQL `search_path`)
- **Dynamic tables**: Each project gets isolated `{project_name}_conversation` and `{project_name}_messages` tables created automatically on first use
- **Global tables**: `users`, `projects`, `project_members`, `agents`, `project_ad_groups`
- **Project name sanitization**: Special characters replaced with underscores, names lowercased, max 63 chars
- See [docs/ard/DATABASE_SCHEMA.md](docs/ard/DATABASE_SCHEMA.md) for complete schema documentation

## Development Commands

### Running the Application
```bash
# Start backend server (from repository root)
python project.py
# With custom host/port:
python project.py --host 0.0.0.0 --port 8000

# Start frontend dev server (for development)
cd src/frontend && npm run dev

# Build frontend for production
cd src/frontend && npm run build
```

### Frontend Development
```bash
# Install dependencies
cd src/frontend && npm install

# Development server (hot reload)
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

### Configuration
- Copy [config.yaml.example](config.yaml.example) to `config.yaml` and customize
- Set `CONFIG_FILE` environment variable to use a different config path
- App runs with built-in defaults if no config file exists
- Key config sections: `app`, `database`, `jwt`, `ldap`, `cors`

## Key Patterns

### Agent Connectors
All agent connectors inherit from `BaseAgentConnector` ([src/core/agent/base_connector.py](src/core/agent/base_connector.py)) and implement:
- `stream(messages_history, message, conversation_id, files, metadata, **kwargs)`: Async generator yielding text chunks
- `close()`: Cleanup resources
- `get_auth_headers()`: Build auth headers from agent config (supports bearer, basic, api_key)

Connector types registered in [src/core/agent/connectors/__init__.py](src/core/agent/connectors/__init__.py):
- `langgraph`: LangGraph connector with thread management
- `openai`: OpenAI-compatible API connector
- `http`: Generic HTTP streaming connector

### Project Isolation
- Each project has its own conversation/message tables created dynamically via `db_chat.get_db(project_name)`
- Project names are sanitized to valid SQL identifiers (e.g., "my-project" → "my_project_conversation")
- Tables created automatically using SQLAlchemy's `create_all(checkfirst=True)`
- Foreign keys reference project-specific tables

### Authentication & Authorization
- JWT-based auth with configurable expiry (`jwt.secret_key`, `jwt.expire_minutes` in config)
- Optional LDAP integration for user authentication
- RBAC via `project_members` table with roles: `owner`, `admin`, `member`
- AD group-based access via `project_ad_groups` table

### Frontend-Backend Communication
- REST API for CRUD operations (all routers in [src/api/routers/](src/api/routers/))
- SSE (Server-Sent Events) for streaming chat responses
- Static file uploads stored in `data/uploads/` and served at `/uploads`
- SPA served from `frontend/dist/` with fallback to `index.html`

## File Locations

- **Python source**: [src/](src/)
- **Frontend source**: [src/frontend/src/](src/frontend/src/)
- **Frontend build**: `src/frontend/dist/`
- **Database**: PostgreSQL/YugabyteDB (configured in config.yaml)
- **Uploads**: `data/uploads/`
- **Config**: [config.yaml](config.yaml) (root directory)
- **Documentation**: [docs/README.md](docs/README.md) — [ard](docs/ard/) (architecture), [prd](docs/prd/) (product), [user-guide](docs/user-guide/) (connectors, elements), [feature](docs/feature/), [user-journey](docs/user-journey/)

## Important Notes

- Frontend must be built before production deployment (FastAPI serves the dist folder)
- Database tables are created automatically on first use per project
- Agent configurations stored in `agents` table with JSON `extras` field for connector-specific config
- Agent auth stored in `auth` field as JSON: `{"auth_type": "bearer|basic|api_key", "credentials": ...}`
- CORS origins must be configured in `config.yaml` for frontend access
- The `is_default` flag on agents ensures only one default agent per project

## Frontend Design System

> **Rule**: Use MY design tokens (colors, fonts, spacing, radius, shadows) from this file,
> but follow WIX layout patterns and component structure from `docs/wix-patterns.md`.
> When in conflict, MY tokens win. When layout/structure is undefined here, Wix patterns win.

---

### Colors
- **CSS variables**: `--bg-primary: #ffffff`, `--bg-secondary: #f9f9fa`, `--text-primary: #0f0f0f`, `--text-secondary: #6b6b6b`, `--border-color: #e5e5e5`, `--primary-accent: #f59e0b` (amber), `--primary-accent-hover: #d97706`
- **Semantic**: Error `#dc2626` (bg `#fef2f2`), Info `#3b82f6`, Accent fallback `#6366f1` (indigo)
- **Hover states**: `rgba(0,0,0, 0.04–0.06)`, disabled `opacity: 0.6–0.7`, modal backdrop `rgba(0,0,0, 0.5)`

### Fonts
- **Families**: `--font-sans: 'Inter', sans-serif` (body), `--font-display: 'Outfit', sans-serif` (headings) — Google Fonts, weights 300–600
- **Sizes**: Display `1.75–2rem`, Body `0.9–1rem`, Small `0.8–0.875rem`, Caption `0.7–0.75rem`
- **Weights**: Headings `600–700`, Labels `500`, Body `400`

### Spacing
- **Variables**: `--spacing-xs: 0.25rem`, `--spacing-sm: 0.5rem`, `--spacing-md: 1rem`, `--spacing-lg: 1.5rem`, `--spacing-xl: 2rem`
- **Common inline**: padding `0.3–2rem`, gap `0.1–2rem`

### Border Radius
- **Variables**: `--radius-sm: 0.375rem`, `--radius-md: 0.5rem`, `--radius-lg: 0.75rem`, `--radius-xl: 1rem`, `--radius-full: 9999px`
- **Usage**: Buttons pill-shaped (`radius-full`), inputs `1.5rem`, message bubbles `1rem` with asymmetric corners, cards `0.75–1rem`, avatars `50%`

### Shadows
- `--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05)`, `--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1)`, `--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1)`
- Dropdowns: `0 4px 16px rgba(0,0,0,0.08)`, Modals: `0 25px 50px -12px rgba(0,0,0,0.25)`

### Component Patterns
- **Layout**: Full-screen flex (`100vh/100vw`), sidebar `260px` fixed width (hidden at `768px`), chat area `flex: 1`, messages `max-width: 800px` centered, input `max-width: 700px`
- **Buttons**: Primary = black bg/white text/pill-shaped, Secondary = transparent/bordered, Icon = 32–36px circle/square
- **Inputs**: `padding: 0.75rem 1rem`, border `var(--border-color)`, focus adds `box-shadow: 0 0 0 3px rgba(0,0,0,0.05)`
- **Message bubbles**: Assistant `var(--bg-secondary)`, User `#e8e8e8`, padding `0.3rem 0.72rem`, asymmetric radius
- **Dropdowns**: White bg, `border-radius: 10px`, `slideUp 0.12s` animation
- **Modals**: Fixed overlay, `max-width: 1100px`, `max-height: 90vh`, `scaleIn 0.15s` animation
- **List items**: `padding: 0.4rem 0.6rem`, `border-radius: 8px`, hover `rgba(0,0,0,0.04)`, active `rgba(0,0,0,0.06)`

### Transitions
- Fast `0.12s ease` (hover), Medium `0.15s ease-out` (modals), Standard `0.2s ease` (focus), Slow `0.3s ease-out` (slides)
- Spinner: `spin 0.8s linear infinite`, Typing: `dotBounce 1.4s ease-in-out infinite`

### Styling Approach
- Global CSS variables defined in `src/frontend/src/app.css`
- Scoped `<style>` blocks in each Svelte component (no Tailwind, no CSS-in-JS)
- Light theme only, clean/minimal aesthetic with black primary actions and amber accent

---

## Layout & UX Patterns (from Wix — see `docs/wix-patterns.md`)

Follow these Wix structural patterns but skin them with the tokens above:

- **Page editor layout**: Top toolbar (48px) + left sidebar (220px) + canvas + right panel (240px)
- **Sidebar panels**: Section headers in uppercase 12px `--text-secondary`, draggable items with hover bg
- **Drag & drop**: `grab`/`grabbing` cursor, drop zone with dashed border using `--primary-accent`
- **Button hierarchy**: One primary black action per section, secondary bordered, ghost for destructive
- **Feedback**: Toast notifications bottom-center, skeleton loaders for content, spinner for actions
- **Empty states**: Icon + heading + description + CTA button — never leave blank space
- **Tables**: Checkbox column, hover-reveal row actions, uppercase 12px column headers
- **Modals**: Always confirm destructive actions, footer = `[Cancel] [Primary Action]` right-aligned
- **Transitions**: Follow my transition tokens above — do NOT use Wix's 100–200ms defaults
