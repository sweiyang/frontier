# Docker environment

Docker Compose stack for Conduit development and testing.

## Services

| Service             | Image / Build              | Port(s)         | Description                                |
|---------------------|----------------------------|-----------------|--------------------------------------------|
| `yugabytedb`        | `yugabytedb/yugabyte`      | 5433, 15433     | PostgreSQL-compatible database             |
| `mock-ldap`         | `docker/Dockerfile.mock-ldap` | 1389          | Mock LDAP server (dev authentication)      |
| `conduit-server`    | `docker/Dockerfile.conduit`| 8000            | Conduit backend + built Svelte frontend    |
| `http-example`      | `docker/Dockerfile.http-example` | 8080       | HTTP example agent (FastAPI)               |
| `langgraph-example` | `docker/Dockerfile.langgraph-example` | 2024  | LangGraph example agent (dev server)       |

## Quick start

From the repository root:

```bash
# Start everything
docker compose up -d

# Watch logs
docker compose logs -f
```

Once all containers are healthy, open **http://localhost:8000** in your browser.

## Connecting agents in Conduit

After logging in, create a project and add agents with these endpoints:

| Agent type | Endpoint (from Conduit's perspective inside Docker) | Endpoint (if Conduit runs on host) |
|------------|------------------------------------------------------|-------------------------------------|
| HTTP       | `http://http-example:8080`                           | `http://localhost:8080`             |
| LangGraph  | `http://langgraph-example:2024`                      | `http://localhost:2024`             |

When Conduit runs inside Docker Compose (the `conduit-server` container), use the **Docker service names** as hostnames. When Conduit runs on your host machine, use `localhost`.

## Configuration

### Docker config

The file `docker/config.yaml` is mounted into the Conduit container. It points the database at the `yugabytedb` service:

```yaml
database:
  url: postgresql://yugabyte:yugabyte@yugabytedb:5433/yugabyte
```

LDAP points at the `mock-ldap` service:

```yaml
ldap:
  server: ldap://mock-ldap:1389
```

Edit this file to change JWT settings, CORS origins, etc.

### Running Conduit on the host instead

If you prefer to run only the database and example agents in Docker while running Conduit on your host:

```bash
# Start only supporting services
docker compose up -d yugabytedb mock-ldap http-example langgraph-example

# Point your local config.yaml at localhost
# database:
#   url: postgresql://yugabyte:yugabyte@localhost:5433/yugabyte
# ldap:
#   server: ldap://localhost:1389

python project.py
```

## Ports reference

| Port  | Service              | Purpose                              |
|-------|----------------------|--------------------------------------|
| 1389  | Mock LDAP server      | LDAP authentication (dev)            |
| 5433  | YugabyteDB YSQL      | Database connection                  |
| 15433 | YugabyteDB UI        | Cluster monitoring (browser)         |
| 8000  | Conduit server        | Backend API + frontend               |
| 8080  | HTTP example agent    | Example HTTP agent                   |
| 2024  | LangGraph example     | Example LangGraph dev server         |
| 9042  | YugabyteDB YCQL      | Cassandra-compatible API (optional)  |
| 7000  | YugabyteDB Master RPC | Internal (optional)                 |
| 9000  | YugabyteDB TServer    | Internal (optional)                 |

**macOS note:** If port 7000 conflicts with AirPlay, edit `docker-compose.yml` and change `7000:7000` to `7001:7000`.

## Data persistence

Database data is stored in the `yugabyte_data` Docker volume. Uploaded files are stored in `conduit_uploads`.

To wipe everything and start fresh:

```bash
docker compose down -v
docker compose up -d
```

## Rebuilding images

After code changes, rebuild the affected service:

```bash
# Rebuild all
docker compose build

# Rebuild one service
docker compose build conduit-server

# Rebuild and restart
docker compose up -d --build conduit-server
```

## YSQL shell

Connect to YugabyteDB directly:

```bash
docker exec -it conduit-yugabytedb bash -c \
  '/home/yugabyte/bin/ysqlsh --host $(hostname) -U yugabyte -d yugabyte'
```

Default credentials: `yugabyte` / `yugabyte`.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `conduit-server` exits immediately | Check `docker compose logs conduit-server` — usually a DB connection timeout. Make sure `yugabytedb` is healthy first. |
| Port 7000 conflict on macOS | Change `7000:7000` to `7001:7000` in `docker-compose.yml`. |
| LangGraph server won't start | Ensure `langgraph-cli[inmem]` installed correctly. Check `docker compose logs langgraph-example`. |
| Frontend shows blank page | Rebuild: `docker compose build conduit-server && docker compose up -d conduit-server`. |
