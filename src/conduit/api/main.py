"""App creation and router inclusion only."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from conduit.api.middleware.cors import add_cors
from conduit.api.routers import (
    agents,
    auth,
    chat,
    config,
    conversations,
    langgraph,
    ldap,
    metrics,
    projects,
    rbac_groups,
    rbac_members,
    usage,
)
from conduit.api.static.spa import mount_spa
from conduit.core.db import db_chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize resources on startup."""
    db_chat.get_db()
    print("Database initialized")
    yield
    print("Shutting down")


app = FastAPI(lifespan=lifespan)

add_cors(app)

app.include_router(auth.router)
app.include_router(config.router)
app.include_router(conversations.router)
app.include_router(chat.router)
app.include_router(projects.router)
app.include_router(agents.router)
app.include_router(rbac_groups.router)
app.include_router(rbac_members.router)
app.include_router(usage.router)
app.include_router(metrics.router)
app.include_router(ldap.router)
app.include_router(langgraph.router)

mount_spa(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
