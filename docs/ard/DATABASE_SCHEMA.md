# Frontier Database Schema

This document describes the database schema and relationships between tables in the Frontier application.

**Supported Databases:**
- SQLite (default)
- PostgreSQL (including YugabyteDB)

The application uses SQLAlchemy ORM and supports both SQLite and PostgreSQL-compatible databases. Configure the database connection via `database.url` in `config.yaml` (see `config.yaml.example`).

**Important:** Conversations and messages are stored in **project-specific tables** that are created dynamically. Each project has its own isolated set of tables for conversations and messages.

---

## Entity Relationship Diagram (Text)

```
┌─────────────────────┐
│       users         │
├─────────────────────┤
│ id (PK)             │
│ username            │
│ created_at          │
└─────────┬───────────┘
          │
          │ 1:N (owner)
          ▼
┌─────────────────────┐       ┌─────────────────────┐
│      projects       │──────▶│       agents        │
├─────────────────────┤  1:N  ├─────────────────────┤
│ id (PK)             │       │ id (PK)             │
│ project_id (UUID)   │       │ project_id (FK)     │
│ project_name        │       │ name                │
│ owner_id (FK→users) │       │ endpoint            │
│ created_at          │       │ connection_type      │
│ updated_at          │       │ is_default          │
└─────────┬───────────┘       │ extras (JSON)       │
          │                   │ created_at          │
          │ 1:N               │ updated_at          │
          ▼                   └─────────────────────┘
┌─────────────────────┐
│  project_ad_groups  │
├─────────────────────┤
│ id (PK)             │
│ project_id (FK)     │
│ group_dn            │
│ group_name          │
│ role                │
│ added_at            │
└─────────────────────┘

┌─────────────────────┐
│       users         │
└─────────┬───────────┘
          │
          │ N:M (via project_members)
          ▼
┌─────────────────────┐
│   project_members   │  (Association Table)
├─────────────────────┤
│ user_id (FK, PK)    │
│ project_id (FK, PK) │
│ role                │
│ joined_at           │
└─────────────────────┘

┌─────────────────────┐
│       users         │
└─────────┬───────────┘
          │
          │ 1:N (per project)
          ▼
┌─────────────────────────────────────┐       ┌─────────────────────────────────────┐
│  {project_name}_conversation        │──────▶│  {project_name}_messages            │
├─────────────────────────────────────┤  1:N  ├─────────────────────────────────────┤
│ id (PK)                             │       │ id (PK)                             │
│ user_id (FK→users)                   │       │ conversation_id (FK)                │
│ title                               │       │ role                                 │
│ thread_id (LangGraph)               │       │ content                              │
│ created_at                          │       │ model                                │
│ updated_at                          │       │ token_count                          │
└─────────────────────────────────────┘       │ created_at                           │
                                              └─────────────────────────────────────┘

Note: Tables are created dynamically per project. For example:
- Project "test" → tables: test_conversation, test_messages
- Project "my-project" → tables: my_project_conversation, my_project_messages
```

---

## Tables Overview

| Table | Description |
|-------|-------------|
| `users` | User accounts in the system |
| `projects` | Projects that users can create and belong to |
| `project_members` | Association table for user-project membership (M:N) with roles |
| `agents` | AI agent configurations per project |
| `project_ad_groups` | AD/LDAP group memberships for project RBAC |
| `{project_name}_conversation` | Chat conversations for a specific project (dynamic table) |
| `{project_name}_messages` | Individual messages within conversations for a specific project (dynamic table) |

---

## Table Definitions

### `users`

Primary user account table.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `username` | VARCHAR(255) | UNIQUE, NOT NULL | Unique username |
| `created_at` | DATETIME | DEFAULT now | Account creation timestamp |

**Relationships:**
- → `projects` (1:N as owner) — A user can own many projects
- ↔ `projects` (N:M via `project_members`) — Users can be members of many projects
- → `{project_name}_conversation` (1:N per project) — A user can have many conversations per project

---

### `{project_name}_conversation`

Chat conversation sessions for a specific project. **Dynamic table created per project.**

**Table Naming:** `{sanitized_project_name}_conversation`

For example:
- Project "test" → `test_conversation`
- Project "my-project" → `my_project_conversation`
- Project "test@123" → `test_123_conversation` (special characters sanitized)

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `user_id` | INTEGER | FK → users.id, NOT NULL | Owner of the conversation |
| `title` | VARCHAR(255) | NULLABLE | Conversation title |
| `thread_id` | VARCHAR(512) | NULLABLE | LangGraph thread ID for agent continuity |
| `created_at` | DATETIME | DEFAULT now | Creation timestamp |
| `updated_at` | DATETIME | DEFAULT now, ON UPDATE | Last update timestamp |

**Relationships:**
- ← `users` (N:1) — Each conversation belongs to one user
- → `{project_name}_messages` (1:N) — A conversation contains many messages

**Notes:**
- Tables are created automatically when first accessed
- Project names are sanitized to valid SQL identifiers (special characters replaced with underscores)
- Each project has completely isolated conversation data

---

### `{project_name}_messages`

Individual messages within conversations for a specific project. **Dynamic table created per project.**

**Table Naming:** `{sanitized_project_name}_messages`

For example:
- Project "test" → `test_messages`
- Project "my-project" → `my_project_messages`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `conversation_id` | INTEGER | FK → {project_name}_conversation.id, NOT NULL | Parent conversation |
| `role` | VARCHAR(50) | NOT NULL | Message role: "user" or "assistant" |
| `content` | TEXT | NOT NULL | Message content |
| `model` | VARCHAR(100) | NULLABLE | AI model used (e.g., "gpt-4", "claude-3") |
| `token_count` | INTEGER | NULLABLE | Token count for the message |
| `created_at` | DATETIME | DEFAULT now | Creation timestamp |

**Relationships:**
- ← `{project_name}_conversation` (N:1) — Each message belongs to one conversation

**Notes:**
- Tables are created automatically when first accessed
- Foreign key references the project-specific conversation table
- Each project has completely isolated message data

---

### `projects`

Project container for organizing work and access control.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `project_id` | VARCHAR(36) | UNIQUE, NOT NULL | UUID identifier |
| `project_name` | VARCHAR(255) | NOT NULL | Display name |
| `owner_id` | INTEGER | FK → users.id, NOT NULL | Project owner |
| `created_at` | DATETIME | DEFAULT now | Creation timestamp |
| `updated_at` | DATETIME | DEFAULT now, ON UPDATE | Last update timestamp |

**Relationships:**
- ← `users` (N:1 as owner) — Each project has one owner
- ↔ `users` (N:M via `project_members`) — Projects can have many members
- → `agents` (1:N) — A project can have many AI agents
- → `project_ad_groups` (1:N) — A project can have many AD group associations
- → `{project_name}_conversation` (logical 1:N) — Each project has its own conversation table
- → `{project_name}_messages` (logical 1:N) — Each project has its own messages table

---

### `project_members`

Association table for many-to-many relationship between users and projects.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | INTEGER | FK → users.id, PRIMARY KEY | User member |
| `project_id` | INTEGER | FK → projects.id, PRIMARY KEY | Project |
| `role` | VARCHAR(50) | DEFAULT "member" | Role: "owner", "admin", or "member" |
| `joined_at` | DATETIME | DEFAULT now | When user joined the project |

**Relationships:**
- ← `users` (N:1) — Links to user
- ← `projects` (N:1) — Links to project

---

### `agents`

AI agent configurations for projects.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `project_id` | INTEGER | FK → projects.id, NOT NULL | Parent project |
| `name` | VARCHAR(255) | NOT NULL | Agent display name |
| `endpoint` | VARCHAR(512) | NOT NULL | Agent API endpoint URL |
| `connection_type` | VARCHAR(50) | NOT NULL | Connection type: "http", "websocket", "grpc" |
| `is_default` | BOOLEAN | DEFAULT FALSE, NOT NULL | Whether this is the default agent |
| `extras` | JSON | NULLABLE | Additional configuration data |
| `created_at` | DATETIME | DEFAULT now | Creation timestamp |
| `updated_at` | DATETIME | DEFAULT now, ON UPDATE | Last update timestamp |

**Relationships:**
- ← `projects` (N:1) — Each agent belongs to one project

---

### `project_ad_groups`

AD/LDAP group associations for project-level access control.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `project_id` | INTEGER | FK → projects.id, NOT NULL | Parent project |
| `group_dn` | VARCHAR(512) | NOT NULL | AD distinguished name |
| `group_name` | VARCHAR(255) | NOT NULL | Display name |
| `role` | VARCHAR(50) | DEFAULT "member" | Role: "member" or "admin" |
| `added_at` | DATETIME | DEFAULT now | When the group was added |

**Relationships:**
- ← `projects` (N:1) — Each AD group association belongs to one project

---

## Relationship Summary

| Relationship | Type | Description |
|--------------|------|-------------|
| `users` → `projects` (owner) | 1:N | A user can own many projects |
| `users` ↔ `projects` | N:M | Users can be members of many projects (via `project_members`) |
| `users` → `{project_name}_conversation` | 1:N | A user can have many conversations per project |
| `{project_name}_conversation` → `{project_name}_messages` | 1:N | A conversation contains many messages |
| `projects` → `agents` | 1:N | A project can have many agent configurations |
| `projects` → `project_ad_groups` | 1:N | A project can have many AD group associations |

---

## Cascade Rules

| Parent Table | Child Table | On Delete |
|--------------|-------------|-----------|
| `projects` | `agents` | CASCADE (delete-orphan) |
| `projects` | `project_ad_groups` | CASCADE (delete-orphan) |
| `{project_name}_conversation` | `{project_name}_messages` | CASCADE (delete-orphan) |

---

## Visual Relationship Map

```
                              ┌──────────────┐
                              │    users     │
                              └──────┬───────┘
                                     │
             ┌───────────────────────┼───────────────────────┐
             │                       │                       │
             ▼                       ▼                       ▼
    ┌──────────────────────┐ ┌───────────────┐       ┌───────────────┐
    │{project}_conversation │ │   projects   │◀──────│project_members│
    └───────┬───────────────┘ │   (owner)    │       └───────────────┘
            │                  └───────┬───────┘
            ▼                         │
    ┌──────────────────────┐          ├──────────────────┐
    │{project}_messages    │          │                  │
    └──────────────────────┘          ▼                  ▼
                           ┌───────────────┐  ┌─────────────────┐
                           │    agents     │  │project_ad_groups│
                           └───────────────┘  └─────────────────┘
```

---

## Dynamic Table Creation

### Table Naming Convention

Project-specific tables are created dynamically using the following naming pattern:
- **Conversation table:** `{sanitized_project_name}_conversation`
- **Messages table:** `{sanitized_project_name}_messages`

### Project Name Sanitization

Project names are sanitized to ensure valid SQL identifiers:
- Special characters (non-alphanumeric except underscore) are replaced with `_`
- Names are converted to lowercase
- If the name doesn't start with a letter or underscore, a leading underscore is added
- Names are truncated to 63 characters (PostgreSQL identifier limit)

**Examples:**
- `"test"` → `test_conversation`, `test_messages`
- `"my-project"` → `my_project_conversation`, `my_project_messages`
- `"test@123"` → `test_123_conversation`, `test_123_messages`
- `"123project"` → `_123project_conversation`, `_123project_messages`

### Automatic Table Creation

Tables are created automatically when:
1. A conversation is created for a project
2. A message is saved for a project
3. Conversations are listed for a project
4. Messages are retrieved for a project

The application uses SQLAlchemy's `create_all()` with `checkfirst=True` to ensure tables exist before operations.

---

## Notes

1. **Soft deletes are not implemented** — All deletes are hard deletes.
2. **Project membership** uses an association table with role information.
3. **LAN IDs** are usernames in the `users` table. Access is granted via `project_members` with role assignments.
4. **Member Agent Permissions** — Individual members can be assigned specific agents they can access via `member_agent_permissions`.
5. **Project-segregated chats** — Each project has completely isolated conversation and message tables. This provides:
   - Complete data isolation between projects
   - Better scalability (can partition/archive by project)
   - Easier data management and cleanup
6. **Agents** support a `is_default` flag — only one agent per project can be marked as default.
7. **AD Groups** enable LDAP-based access control at the project level.
8. **Table cleanup** — When a project is deleted, its conversation and message tables can be dropped using the `delete_project_tables()` function (use with caution).

---

## Migration Notes

If migrating from the old single-table structure:
- Old `conversations` and `messages` tables are no longer used
- New project-specific tables are created automatically on first use
- Existing data would need to be migrated manually if required (not implemented by default)
