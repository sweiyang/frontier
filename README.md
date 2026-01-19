# Conduit 


## Quick Start

1. sh scripts/install_env.sh
2. sh scripts/start.sh

## Database Configuration

Conduit supports both SQLite (default) and PostgreSQL-compatible databases (including YugabyteDB).

### SQLite (Default)

By default, Conduit uses SQLite and creates a database file at `src/conduit/data/conduit.db`. No configuration is needed.

### PostgreSQL / YugabyteDB

To use PostgreSQL or YugabyteDB, set the `DATABASE_URL` environment variable:

```bash
# PostgreSQL example
export DATABASE_URL="postgresql://username:password@localhost:5432/conduit"

# YugabyteDB example (PostgreSQL-compatible)
export DATABASE_URL="postgresql://yugabyte:password@yugabyte-host:5433/yugabyte"

# With explicit driver
export DATABASE_URL="postgresql+psycopg2://username:password@host:port/dbname"
```

The connection string follows the standard SQLAlchemy database URL format. Make sure `psycopg2-binary` is installed (included in requirements).