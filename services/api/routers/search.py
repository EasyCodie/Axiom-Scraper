"""
Search router for token search across local and external sources.

Provides endpoint:
- GET /search - Search tokens by name, symbol, or contract address
"""

from fastapi import APIRouter, Depends, Query

from axiom.core.db import Database
from services.api.cache import cached
from services.api.config import settings
from services.api.dependencies import get_database, limiter
from services.api.external import moralis_search_tokens
from services.api.schemas import SearchResponse, SearchResult

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=SearchResponse)
@cached(settings.cache_ttl_medium, namespace="search")
@limiter.limit(settings.rate_limit_search)
async def search_tokens(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    chain: str = Query(default="sol", description="Chain identifier"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum results"),
    include_external: bool = Query(default=True, description="Include external sources (Moralis)"),
    db: Database = Depends(get_database),
) -> SearchResponse:
    """
    Search tokens by name, symbol, or contract address.

    Merges results from local database and external sources (Moralis).

    Args:
        q: Search query string
        chain: Chain identifier (default: sol)
        limit: Maximum number of results (1-100)
        include_external: Include results from Moralis API
        db: Database connection

    Returns:
        SearchResponse with merged search results
    """
    results: list[SearchResult] = []
    sources: list[str] = []

    # Search local database
    conn = db.connect()
    query_pattern = f"%{q.lower()}%"

    # Search by name, symbol, or contract address
    local_results = conn.execute(
        """
        SELECT
            t.ca,
            t.chain,
            t.token_name,
            t.symbol,
            tm.score,
            tm.price_usd,
            tm.volume_usd_24h
        FROM tokens t
        LEFT JOIN token_metrics tm ON t.ca = tm.ca AND t.chain = tm.chain
        WHERE t.chain = ?
        AND (
            LOWER(t.token_name) LIKE ?
            OR LOWER(t.symbol) LIKE ?
            OR LOWER(t.ca) LIKE ?
        )
        ORDER BY
            CASE
                WHEN LOWER(t.ca) = ? THEN 0
                WHEN LOWER(t.symbol) = ? THEN 1
                WHEN LOWER(t.token_name) = ? THEN 2
                ELSE 3
            END,
            t.last_seen_at DESC
        LIMIT ?
        """,
        [
            chain,
            query_pattern,
            query_pattern,
            query_pattern,
            q.lower(),
            q.lower(),
            q.lower(),
            limit,
        ],
    ).fetchall()

    if local_results:
        sources.append("local")
        for row in local_results:
            results.append(
                SearchResult(
                    ca=row[0],
                    chain=row[1],
                    token_name=row[2],
                    symbol=row[3],
                    source="local",
                    score=row[4],
                    price_usd=row[5],
                    volume_usd_24h=row[6],
                )
            )

    # Search external sources if enabled and API key configured
    if include_external and settings.moralis_api_key and len(results) < limit:
        try:
            moralis_results = await moralis_search_tokens(
                query=q, chain=chain, limit=limit - len(results)
            )

            if moralis_results:
                sources.append("moralis")
                for item in moralis_results:
                    # Skip if already in results
                    ca = item.get("address", "").lower()
                    if any(r.ca == ca for r in results):
                        continue

                    results.append(
                        SearchResult(
                            ca=ca,
                            chain=chain,
                            token_name=item.get("name"),
                            symbol=item.get("symbol"),
                            source="moralis",
                            score=None,
                            price_usd=item.get("price_usd"),
                            volume_usd_24h=item.get("volume_24h"),
                        )
                    )
        except Exception:
            # Silently fail external search, return local results only
            pass

    return SearchResponse(
        results=results[:limit], count=len(results[:limit]), query=q, sources=sources
    )
