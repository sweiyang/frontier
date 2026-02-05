# Conduit


## Quick Start

1. sh scripts/install_env.sh
2. Copy `config.yaml.example` to `config.yaml` and adjust if needed (optional; defaults work without it).
3. sh scripts/start.sh

## Configuration

All settings are read from a **configuration file** (YAML). By default Conduit looks for `config.yaml` in the current working directory. To use a different path, set the `CONFIG_FILE` environment variable:

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

If `database.url` is not set in `config.yaml`, Conduit uses SQLite and creates `src/conduit/data/conduit.db`.

### PostgreSQL / YugabyteDB

Set `database.url` in `config.yaml`:

```yaml
database:
  url: postgresql://username:password@localhost:5432/conduit
  # YugabyteDB: postgresql://yugabyte:password@host:5433/yugabyte
  # With driver: postgresql+psycopg2://user:pass@host:port/dbname
```

Make sure `psycopg2-binary` is installed (included in requirements).