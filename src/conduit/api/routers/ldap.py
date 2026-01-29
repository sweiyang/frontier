"""LDAP search: /ldap/search."""
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from conduit.api.app_config import ldap_auth
from conduit.api.deps.auth import get_current_user
from conduit.core.auth.jwt import CurrentUser

router = APIRouter(prefix="/ldap", tags=["ldap"])


@router.get("/search")
async def ldap_search(
    q: str,
    type: str = "all",
    current_user: CurrentUser = Depends(get_current_user),
):
    """Search LDAP for users and groups."""
    if len(q) < 2:
        return JSONResponse({"results": []})

    results = ldap_auth.search_users_and_groups(q, search_type=type)
    return JSONResponse({"results": results})
