"""Config route: /config and /logo."""
import mimetypes
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse, Response

from conduit.api.app_config import (
    APP_NAME,
    SPLASH_TEXT,
    DEFAULT_PROJECT,
    FOOTNOTE,
    LOGO,
    CONTACT_EMAIL_ENABLED,
    CONTACT_EMAIL_ADDRESS,
    CONTACT_EMAIL_SUBJECT_PREFIX,
    CONTACT_JIRA_ENABLED,
    CONTACT_JIRA_URL,
    CONTACT_JIRA_BUTTON_TEXT,
)
from conduit.core.config import get_config

router = APIRouter(tags=["config"])


def _resolve_logo_path() -> Path | None:
    """Resolve the logo file path relative to the config file or as absolute."""
    if not LOGO:
        return None
    logo_path = Path(LOGO)
    if logo_path.is_absolute():
        return logo_path if logo_path.is_file() else None
    # Resolve relative to config file directory
    config_dir = get_config()._path.parent
    resolved = (config_dir / logo_path).resolve()
    return resolved if resolved.is_file() else None


@router.get("/config")
async def get_config_endpoint():
    """Get application configuration. Public endpoint for frontend initialization."""
    config = {
        "app_name": APP_NAME,
        "splash_text": SPLASH_TEXT,
        "default_project": DEFAULT_PROJECT,
        "footnote": FOOTNOTE,
        "logo_url": "/logo" if _resolve_logo_path() else None,
        "contact": {
            "email": {
                "enabled": CONTACT_EMAIL_ENABLED,
                "address": CONTACT_EMAIL_ADDRESS,
                "subject_prefix": CONTACT_EMAIL_SUBJECT_PREFIX,
            },
            "jira": {
                "enabled": CONTACT_JIRA_ENABLED,
                "url": CONTACT_JIRA_URL,
                "button_text": CONTACT_JIRA_BUTTON_TEXT,
            },
        },
    }
    return JSONResponse(config)


@router.get("/logo")
async def get_logo():
    """Serve the configured logo image file."""
    logo_path = _resolve_logo_path()
    if not logo_path:
        return Response(status_code=404)
    media_type, _ = mimetypes.guess_type(str(logo_path))
    return FileResponse(logo_path, media_type=media_type or "image/png")
