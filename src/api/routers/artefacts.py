"""Artefacts: agent-level artefacts accessible via the gallery."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from api.deps.auth import get_current_user
from core.auth.jwt import CurrentUser
from core.db import db_project

router = APIRouter(prefix="/artefacts", tags=["artefacts"])


@router.get("")
async def list_artefacts(current_user: CurrentUser = Depends(get_current_user)):
    """List all agent-level artefacts."""
    artefacts = db_project.list_artefact_agents()
    return JSONResponse({"artefacts": artefacts})
