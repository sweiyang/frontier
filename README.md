# Conduit


## Quick Start

1. sh scripts/install_env.sh
2. Copy `config.yaml.example` to `config.yaml` and adjust if needed (optional; defaults work without it).
3. sh scripts/start.sh

## Configuration

All settings are read from a **configuration file** (YAML). Keep a single `config.yaml` at the **project root**; by default Conduit looks for `config.yaml` in the current working directory (run the server from the repo root). To use a different path, set the `CONFIG_FILE` environment variable:

```bash
export CONFIG_FILE=/path/to/config.yaml
```

If no config file exists, built-in defaults are used so the app runs without one.

Example: copy `config.yaml.example` to `config.yaml` and edit:

- **app**: `app.name`, `app.splash_text`
- **database**: `database.url` (omit for default SQLite at `data/conduit.db`)
- **jwt**: `jwt.secret_key`, `jwt.expire_minutes`
- **ldap**: `ldap.server`, `ldap.base_dn`, `ldap.use_ssl`, `ldap.users_dn`
- **cors**: `cors.allow_origins` (list of allowed origins)

## Database

Conduit supports SQLite (default) and PostgreSQL-compatible databases (including YugabyteDB).

### SQLite (Default)

If `database.url` is not set in `config.yaml`, Conduit uses SQLite and creates `data/conduit.db`.

### PostgreSQL / YugabyteDB

Set `database.url` in `config.yaml`:

```yaml
database:
  url: postgresql://username:password@localhost:5432/conduit
  # YugabyteDB: postgresql://yugabyte:password@host:5433/yugabyte
  # With driver: postgresql+psycopg2://user:pass@host:port/dbname
```

Make sure `psycopg2-binary` is installed (included in requirements).

## Docker Compose

A full Docker Compose stack is provided for local development. From the repository root:

```bash
docker compose up -d
```

### Services

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| `yugabytedb` | `conduit-yugabytedb` | 5433, 15433 | YugabyteDB (PostgreSQL-compatible database) |
| `mock-ldap` | `conduit-mock-ldap` | 1389 | Mock LDAP server (dev authentication) |
| `conduit-server` | `conduit-server` | 8000 | Conduit backend + Svelte frontend |
| `http-example` | `conduit-http-example` | 8080 | HTTP example agent (FastAPI) |
| `langgraph-example` | `conduit-langgraph-example` | 2024 | LangGraph example agent (dev server) |

Once running, open **http://localhost:8000**. The YugabyteDB UI is at **http://localhost:15433**.

### Agent endpoints

When adding agents inside Conduit (running in Docker), use the Docker service names:

- **HTTP agent:** `http://http-example:8080`
- **LangGraph agent:** `http://langgraph-example:2024`

### Key files

- `docker-compose.yml` — service definitions
- `docker/config.yaml` — Docker-specific Conduit config (database points to `yugabytedb` service)
- `docker/Dockerfile.conduit` — multi-stage build (Node.js frontend + Python backend)
- `docker/Dockerfile.http-example` — HTTP example agent image
- `docker/Dockerfile.langgraph-example` — LangGraph example agent image

See [docker/README.md](docker/README.md) for the full reference (ports, rebuilding, YSQL shell, troubleshooting).