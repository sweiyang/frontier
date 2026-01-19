# Conduit Database Schema

This document describes the database schema and relationships between tables in the Conduit application.

**Supported Databases:**
- SQLite (default)
- PostgreSQL (including YugabyteDB)

The application uses SQLAlchemy ORM and supports both SQLite and PostgreSQL-compatible databases. You can configure the database connection using the `DATABASE_URL` environment variable.

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
│ created_at          │       │ connection_type     │
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
          │ 1:N
          ▼
┌─────────────────────┐       ┌─────────────────────┐
│   conversations     │──────▶│      messages       │
├─────────────────────┤  1:N  ├─────────────────────┤
│ id (PK)             │       │ id (PK)             │
│ user_id (FK→users)  │       │ conversation_id(FK) │
│ project             │       │ role                │
│ title               │       │ content             │
│ created_at          │       │ model               │
│ updated_at          │       │ token_count         │
└─────────────────────┘       │ created_at          │
                              └─────────────────────┘
```

---

## Tables Overview

| Table | Description |
|-------|-------------|
| `users` | User accounts in the system |
| `conversations` | Chat conversations belonging to users |
| `messages` | Individual messages within conversations |
| `projects` | Projects that users can create and belong to |
| `project_members` | Association table for user-project membership (M:N) with roles |
| `agents` | AI agent configurations per project |
| `project_ad_groups` | AD/LDAP group memberships for project RBAC |

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
- → `conversations` (1:N) — A user can have many conversations
- → `projects` (1:N as owner) — A user can own many projects
- ↔ `projects` (N:M via `project_members`) — Users can be members of many projects

---

### `conversations`

Chat conversation sessions.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `user_id` | INTEGER | FK → users.id, NOT NULL | Owner of the conversation |
| `project` | VARCHAR(255) | NULLABLE | Project name (for filtering) |
| `title` | VARCHAR(255) | NULLABLE | Conversation title |
| `created_at` | DATETIME | DEFAULT now | Creation timestamp |
| `updated_at` | DATETIME | DEFAULT now, ON UPDATE | Last update timestamp |

**Relationships:**
- ← `users` (N:1) — Each conversation belongs to one user
- → `messages` (1:N) — A conversation contains many messages

---

### `messages`

Individual messages within conversations.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Auto-increment ID |
| `conversation_id` | INTEGER | FK → conversations.id, NOT NULL | Parent conversation |
| `role` | VARCHAR(50) | NOT NULL | Message role: "user" or "assistant" |
| `content` | TEXT | NOT NULL | Message content |
| `model` | VARCHAR(100) | NULLABLE | AI model used (e.g., "gpt-4", "claude-3") |
| `token_count` | INTEGER | NULLABLE | Token count for the message |
| `created_at` | DATETIME | DEFAULT now | Creation timestamp |

**Relationships:**
- ← `conversations` (N:1) — Each message belongs to one conversation

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
| `users` → `conversations` | 1:N | A user owns many conversations |
| `users` → `projects` (owner) | 1:N | A user can own many projects |
| `users` ↔ `projects` | N:M | Users can be members of many projects (via `project_members`) |
| `conversations` → `messages` | 1:N | A conversation contains many messages |
| `projects` → `agents` | 1:N | A project can have many agent configurations |
| `projects` → `project_ad_groups` | 1:N | A project can have many AD group associations |

---

## Cascade Rules

| Parent Table | Child Table | On Delete |
|--------------|-------------|-----------|
| `projects` | `agents` | CASCADE (delete-orphan) |
| `projects` | `project_ad_groups` | CASCADE (delete-orphan) |

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
    ┌────────────────┐      ┌───────────────┐       ┌───────────────┐
    │ conversations  │      │   projects    │◀──────│project_members│
    └───────┬────────┘      │   (owner)     │       └───────────────┘
            │               └───────┬───────┘
            ▼                       │
    ┌────────────────┐              ├──────────────────┐
    │   messages     │              │                  │
    └────────────────┘              ▼                  ▼
                           ┌───────────────┐  ┌─────────────────┐
                           │    agents     │  │project_ad_groups│
                           └───────────────┘  └─────────────────┘
```

---

## Notes

1. **Soft deletes are not implemented** — All deletes are hard deletes.
2. **Project membership** uses an association table with role information.
3. **LAN IDs** are usernames in the `users` table. Access is granted via `project_members` with role assignments.
4. **Member Agent Permissions** — Individual members can be assigned specific agents they can access via `member_agent_permissions`.
5. **Conversation.project** is stored as a string (project name) rather than a foreign key for flexibility.
6. **Agents** support a `is_default` flag — only one agent per project can be marked as default.
7. **AD Groups** enable LDAP-based access control at the project level.

