"""
External HTTP clients for FastAPI service.

Currently includes:
- Moralis token search proxy
"""

from typing import Any

import httpx

from services.api.config import settings


async def moralis_search_tokens(query: str, chain: str, limit: int) -> list[dict[str, Any]]:
    """Search tokens via Moralis API.

    Args:
        query: Search query string
        chain: Blockchain chain identifier
        limit: Maximum number of results

    Returns:
        List of token dicts from Moralis

    Raises:
        RuntimeError: If Moralis API key is not configured
    """
    if not settings.moralis_api_key:
        raise RuntimeError("Moralis API key is not configured")

    url = f"{settings.moralis_base_url}/token/search"
    params = {
        "chain": chain,
        "q": query,
        "limit": limit,
    }

    headers = {
        "X-API-Key": settings.moralis_api_key,
    }

    async with httpx.AsyncClient(timeout=settings.moralis_timeout) as client:
        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

    if isinstance(data, dict) and "result" in data:
        return data["result"]
    if isinstance(data, list):
        return data
    return []
