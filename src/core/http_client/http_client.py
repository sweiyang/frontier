"""Shared HTTP client for outbound requests."""

import httpx

http_client = httpx.Client(timeout=None)