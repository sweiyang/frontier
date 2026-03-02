"""OpenAI-compatible model discovery: /openai/models."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from conduit.api.deps.auth import get_current_user
from conduit.api.schema import OpenAIModelsRequest
from conduit.api.services.openai_service import fetch_models
from conduit.core.auth.jwt import CurrentUser

router = APIRouter(prefix="/openai", tags=["openai"])


@router.post("/models")
async def fetch_openai_models(
    request: OpenAIModelsRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Fetch available models from an OpenAI-compatible endpoint.
    Allows discovering models before saving an agent configuration.
    """
    try:
        models = await fetch_models(
            endpoint=request.endpoint,
            auth=request.auth,
        )
        return JSONResponse({"models": models})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch models: {str(e)}")
