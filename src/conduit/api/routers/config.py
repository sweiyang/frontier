"""Config route: /config."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from conduit.api.app_config import (
    APP_NAME,
    SPLASH_TEXT,
    DEFAULT_PROJECT,
    CONTACT_EMAIL_ENABLED,
    CONTACT_EMAIL_ADDRESS,
    CONTACT_EMAIL_SUBJECT_PREFIX,
    CONTACT_JIRA_ENABLED,
    CONTACT_JIRA_URL,
    CONTACT_JIRA_BUTTON_TEXT,
)

router = APIRouter(tags=["config"])


@router.get("/config")
async def get_config():
    """Get application configuration. Public endpoint for frontend initialization."""
    config = {
        "app_name": APP_NAME,
        "splash_text": SPLASH_TEXT,
        "default_project": DEFAULT_PROJECT,
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
