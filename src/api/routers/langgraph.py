"""LangGraph assistants: /langgraph/assistants."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from api.deps.auth import get_current_user
from api.schema import LangGraphAssistantsRequest
from api.services.langgraph_service import fetch_assistants
from core.auth.jwt import CurrentUser
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/langgraph", tags=["langgraph"])


@router.post("/assistants")
async def fetch_langgraph_assistants(
    request: LangGraphAssistantsRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Fetch available assistants from a LangGraph endpoint.
    Allows discovering LangGraph assistants before saving an agent configuration.
    """
    try:
        assistants = await fetch_assistants(
            endpoint=request.endpoint,
            graph_id=request.graph_id,
            auth=request.auth,
        )
        return JSONResponse({"assistants": assistants})
    except ImportError:
        logger.opt(exception=True).error("LangGraph SDK not installed")
        raise HTTPException(
            status_code=400,
            detail="LangGraph SDK not installed. Install with: pip install langgraph-sdk",
        )
    except Exception as e:
        logger.opt(exception=True).error("Failed to fetch LangGraph assistants from {}", request.endpoint)
        raise HTTPException(status_code=400, detail=f"Failed to fetch assistants: {str(e)}")
