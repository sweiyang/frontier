"""App creation and router inclusion only."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.config import get_config
from core.logging import setup_logging, get_logger
from api.middleware.cors import add_cors
from api.routers import (
    agents,
    auth,
    chat,
    config,
    conversations,
    langgraph,
    ldap,
    metrics,
    openai_models,
    projects,
    rbac_groups,
    rbac_members,
    usage,
)
from api.static.spa import mount_spa
from core.db import db_chat

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize resources on startup."""
    setup_logging()
    db_chat.get_db()
    logger.info("Database initialized")
    yield
    logger.info("Shutting down")


app = FastAPI(lifespan=lifespan)

add_cors(app, allow_origins=get_config().cors_allow_origins)

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
app.include_router(openai_models.router)

from fastapi.staticfiles import StaticFiles
import os

# Create uploads directory if it doesn't exist
uploads_dir = os.path.join(os.path.dirname(__file__), "../data/uploads")
os.makedirs(uploads_dir, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

mount_spa(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
