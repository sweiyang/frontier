"""Config route: /config."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from conduit.api.app_config import APP_NAME

router = APIRouter(tags=["config"])


@router.get("/config")
async def get_config():
    """Get application configuration. Public endpoint for frontend initialization."""
    return JSONResponse({"app_name": APP_NAME})
