"""SPA static files mounting logic."""
import mimetypes

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.frontend.frontend import Frontend
from core.logging import get_logger

logger = get_logger(__name__)


class SPAStaticFiles(StaticFiles):
    """StaticFiles that serves index.html for unknown paths (SPA fallback)."""

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except Exception:
            logger.debug("SPA fallback: serving index.html for path: %s", path)
            return await super().get_response("index.html", scope)


def mount_spa(app: FastAPI) -> None:
    """Mount the frontend build as SPA at /."""
    mimetypes.add_type("text/javascript", ".js")
    frontend = Frontend()
    app.mount(
        "/",
        SPAStaticFiles(directory=frontend.get_build_dir(), html=True),
        name="spa-static-files",
    )
