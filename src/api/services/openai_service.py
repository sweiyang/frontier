"""Fetch models from an OpenAI-compatible /v1/models endpoint."""

import base64
from typing import Optional

import httpx


def _build_auth_headers(auth: Optional[dict]) -> dict:
    """Build authentication headers from an auth config dict."""
    if not auth:
        return {}
    auth_type = auth.get("auth_type")
    credentials = auth.get("credentials")
    if not auth_type or not credentials:
        return {}

    if auth_type == "api_key":
        return {"X-API-Key": credentials}
    if auth_type == "bearer":
        return {"Authorization": f"Bearer {credentials}"}
    if auth_type == "basic" and isinstance(credentials, dict):
        username = credentials.get("username", "")
        password = credentials.get("password", "")
        encoded = base64.b64encode(f"{username}:{password}".encode()).decode()
        return {"Authorization": f"Basic {encoded}"}
    return {}


async def fetch_models(endpoint: str, auth: Optional[dict]) -> list:
    """Fetch available models from an OpenAI-compatible endpoint.

    Calls GET {endpoint}/v1/models and returns a simplified list.

    Returns:
        List of dicts with 'id' and 'name' keys.
    """
    ep = endpoint.rstrip("/")
    if ep.endswith("/v1"):
        url = f"{ep}/models"
    elif ep.endswith("/models"):
        url = ep
    else:
        url = f"{ep}/v1/models"

    headers = {"Accept": "application/json"}
    headers.update(_build_auth_headers(auth))

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

    raw_models = data.get("data", [])
    models = [{"id": m.get("id", ""), "name": m.get("id", "")} for m in raw_models]
    models.sort(key=lambda m: m["name"])
    return models
