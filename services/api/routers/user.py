"""
User router for protected user-related endpoints.

Provides endpoints for:
- GET /user/favorites - Get user's favorite tokens
- POST /user/favorites - Add token to favorites
- DELETE /user/favorites/{ca} - Remove token from favorites
- GET /user/comparisons - Get user's token comparisons
- POST /user/comparisons - Create new comparison
- DELETE /user/comparisons/{comparison_id} - Delete comparison
- GET /user/alerts - Get user's price alerts
- POST /user/alerts - Create new alert
- PATCH /user/alerts/{alert_id} - Update alert
- DELETE /user/alerts/{alert_id} - Delete alert
"""

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from axiom.core.db import Database
from axiom.core.models import eet_now
from services.api.dependencies import ensure_user_profile, get_database, limiter
from services.api.schemas import (
    AlertListResponse,
    AlertRequest,
    AlertResponse,
    ComparisonListResponse,
    ComparisonRequest,
    ComparisonResponse,
    FavoriteListResponse,
    FavoriteRequest,
    FavoriteResponse,
)

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/favorites", response_model=FavoriteListResponse)
@limiter.limit("100/minute")
async def list_favorites(
    user_id: str = Depends(ensure_user_profile),
    db: Database = Depends(get_database),
) -> FavoriteListResponse:
    """
    Get user's favorite tokens.

    Args:
        user_id: Current user ID from JWT
        db: Database connection

    Returns:
        FavoriteListResponse with list of favorites
    """
    conn = db.connect()
    favorites_data = conn.execute(
        """
        SELECT user_id, ca, chain, favorited_at
        FROM user_favorites
        WHERE user_id = ?
        ORDER BY favorited_at DESC
        """,
        [user_id],
    ).fetchall()

    favorites = [
        FavoriteResponse(user_id=row[0], ca=row[1], chain=row[2], favorited_at=row[3])
        for row in favorites_data
    ]

    return FavoriteListResponse(favorites=favorites, count=len(favorites))


@router.post("/favorites", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("50/minute")
async def add_favorite(
    request: FavoriteRequest,
    user_id: str = Depends(ensure_user_profile),
    db: Database = Depends(get_database),
) -> FavoriteResponse:
    """
    Add token to user's favorites.

    Args:
        request: Favorite request with contract address
        user_id: Current user ID from JWT
        db: Database connection

    Returns:
        FavoriteResponse with created favorite
    """
    conn = db.connect()
    now = eet_now()

    # Check if already favorited
    existing = conn.execute(
        """
        SELECT user_id FROM user_favorites
        WHERE user_id = ? AND ca = ? AND chain = ?
        """,
        [user_id, request.ca.lower(), request.chain],
    ).fetchone()

    if existing:
        # Already favorited, return existing
        favorited_at = conn.execute(
            """
            SELECT favorited_at FROM user_favorites
            WHERE user_id = ? AND ca = ? AND chain = ?
            """,
            [user_id, request.ca.lower(), request.chain],
        ).fetchone()[0]

        return FavoriteResponse(
            user_id=user_id,
            ca=request.ca.lower(),
            chain=request.chain,
            favorited_at=favorited_at,
        )

    # Insert new favorite
    conn.execute(
        """
        INSERT INTO user_favorites (user_id, ca, chain, favorited_at)
        VALUES (?, ?, ?, ?)
        """,
        [user_id, request.ca.lower(), request.chain, now],
    )

    return FavoriteResponse(
        user_id=user_id,
        ca=request.ca.lower(),
        chain=request.chain,
        favorited_at=now,
    )


@router.delete("/favorites/{ca}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("50/minute")
async def remove_favorite(
    ca: str,
    chain: str = "sol",
    user_id: str = Depends(ensure_user_profile),
    db: Database = Depends(get_database),
) -> None:
    """
    Remove token from user's favorites.

    Args:
        ca: Contract address to remove
        chain: Chain identifier
        user_id: Current user ID from JWT
        db: Database connection
    """
    conn = db.connect()
    conn.execute(
        """
        DELETE FROM user_favorites
        WHERE user_id = ? AND ca = ? AND chain = ?
        """,
        [user_id, ca.lower(), chain],
    )


@router.get("/comparisons", response_model=ComparisonListResponse)
@limiter.limit("100/minute")
async def list_comparisons(
    user_id: str = Depends(ensure_user_profile),
    db: Database = Depends(get_database),
) -> ComparisonListResponse:
    """
    Get user's token comparisons.

    Args:
        user_id: Current user ID from JWT
        db: Database connection

    Returns:
        ComparisonListResponse with list of comparisons
    """
    conn = db.connect()
    comparisons_data = conn.execute(
        """
        SELECT comparison_id, user_id, name, token_addresses, chain, created_at, updated_at
        FROM user_comparisons
        WHERE user_id = ?
        ORDER BY updated_at DESC
        """,
        [user_id],
    ).fetchall()

    comparisons = [
        ComparisonResponse(
            comparison_id=row[0],
            user_id=row[1],
            name=row[2],
            token_addresses=json.loads(row[3]) if isinstance(row[3], str) else row[3],
            chain=row[4],
            created_at=row[5],
            updated_at=row[6],
        )
        for row in comparisons_data
    ]

    return ComparisonListResponse(comparisons=comparisons, count=len(comparisons))


@router.post("/comparisons", response_model=ComparisonResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("50/minute")
async def create_comparison(
    request: ComparisonRequest,
    user_id: str = Depends(ensure_user_profile),
    db: Database = Depends(get_database),
) -> ComparisonResponse:
    """
    Create new token comparison.

    Args:
        request: Comparison request with name and token addresses
        user_id: Current user ID from JWT
        db: Database connection

    Returns:
        ComparisonResponse with created comparison
    """
    conn = db.connect()
    now = eet_now()
    comparison_id = str(uuid.uuid4())

    # Normalize addresses to lowercase
    token_addresses = [addr.lower() for addr in request.token_addresses]

    conn.execute(
        """
        INSERT INTO user_comparisons (
            comparison_id, user_id, name, token_addresses, chain, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            comparison_id,
            user_id,
            request.name,
            json.dumps(token_addresses),
            request.chain,
            now,
            now,
        ],
    )

    return ComparisonResponse(
        comparison_id=comparison_id,
        user_id=user_id,
        name=request.name,
        token_addresses=token_addresses,
        chain=request.chain,
        created_at=now,
        updated_at=now,
    )


@router.delete("/comparisons/{comparison_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("50/minute")
async def delete_comparison(
    comparison_id: str,
    user_id: str = Depends(ensure_user_profile),
    db: Database = Depends(get_database),
) -> None:
    """
    Delete token comparison.

    Args:
        comparison_id: Comparison ID to delete
        user_id: Current user ID from JWT
        db: Database connection

    Raises:
        HTTPException: 404 if comparison not found or not owned by user
    """
    conn = db.connect()

    # Check ownership
    existing = conn.execute(
        """
        SELECT comparison_id FROM user_comparisons
        WHERE comparison_id = ? AND user_id = ?
        """,
        [comparison_id, user_id],
    ).fetchone()

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comparison not found",
        )

    conn.execute(
        """
        DELETE FROM user_comparisons
        WHERE comparison_id = ? AND user_id = ?
        """,
        [comparison_id, user_id],
    )


@router.get("/alerts", response_model=AlertListResponse)
@limiter.limit("100/minute")
async def list_alerts(
    user_id: str = Depends(ensure_user_profile),
    db: Database = Depends(get_database),
) -> AlertListResponse:
    """
    Get user's price alerts.

    Args:
        user_id: Current user ID from JWT
        db: Database connection

    Returns:
        AlertListResponse with list of alerts
    """
    conn = db.connect()
    alerts_data = conn.execute(
        """
        SELECT alert_id, user_id, ca, chain, alert_type, threshold, enabled,
               created_at, last_triggered_at
        FROM user_alerts
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        [user_id],
    ).fetchall()

    alerts = [
        AlertResponse(
            alert_id=row[0],
            user_id=row[1],
            ca=row[2],
            chain=row[3],
            alert_type=row[4],
            threshold=row[5],
            enabled=row[6],
            created_at=row[7],
            last_triggered_at=row[8],
        )
        for row in alerts_data
    ]

    return AlertListResponse(alerts=alerts, count=len(alerts))


@router.post("/alerts", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("50/minute")
async def create_alert(
    request: AlertRequest,
    user_id: str = Depends(ensure_user_profile),
    db: Database = Depends(get_database),
) -> AlertResponse:
    """
    Create new price alert.

    Args:
        request: Alert request with monitoring parameters
        user_id: Current user ID from JWT
        db: Database connection

    Returns:
        AlertResponse with created alert
    """
    conn = db.connect()
    now = eet_now()
    alert_id = str(uuid.uuid4())

    conn.execute(
        """
        INSERT INTO user_alerts (
            alert_id, user_id, ca, chain, alert_type, threshold, enabled,
            created_at, last_triggered_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            alert_id,
            user_id,
            request.ca.lower(),
            request.chain,
            request.alert_type,
            request.threshold,
            request.enabled,
            now,
            None,
        ],
    )

    return AlertResponse(
        alert_id=alert_id,
        user_id=user_id,
        ca=request.ca.lower(),
        chain=request.chain,
        alert_type=request.alert_type,
        threshold=request.threshold,
        enabled=request.enabled,
        created_at=now,
        last_triggered_at=None,
    )


@router.patch("/alerts/{alert_id}", response_model=AlertResponse)
@limiter.limit("50/minute")
async def update_alert(
    alert_id: str,
    request: AlertRequest,
    user_id: str = Depends(ensure_user_profile),
    db: Database = Depends(get_database),
) -> AlertResponse:
    """
    Update price alert.

    Args:
        alert_id: Alert ID to update
        request: Alert request with updated parameters
        user_id: Current user ID from JWT
        db: Database connection

    Returns:
        AlertResponse with updated alert

    Raises:
        HTTPException: 404 if alert not found or not owned by user
    """
    conn = db.connect()

    # Check ownership and get existing alert
    existing = conn.execute(
        """
        SELECT created_at, last_triggered_at FROM user_alerts
        WHERE alert_id = ? AND user_id = ?
        """,
        [alert_id, user_id],
    ).fetchone()

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    created_at, last_triggered_at = existing

    # Update alert
    conn.execute(
        """
        UPDATE user_alerts
        SET ca = ?, chain = ?, alert_type = ?, threshold = ?, enabled = ?
        WHERE alert_id = ? AND user_id = ?
        """,
        [
            request.ca.lower(),
            request.chain,
            request.alert_type,
            request.threshold,
            request.enabled,
            alert_id,
            user_id,
        ],
    )

    return AlertResponse(
        alert_id=alert_id,
        user_id=user_id,
        ca=request.ca.lower(),
        chain=request.chain,
        alert_type=request.alert_type,
        threshold=request.threshold,
        enabled=request.enabled,
        created_at=created_at,
        last_triggered_at=last_triggered_at,
    )


@router.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("50/minute")
async def delete_alert(
    alert_id: str,
    user_id: str = Depends(ensure_user_profile),
    db: Database = Depends(get_database),
) -> None:
    """
    Delete price alert.

    Args:
        alert_id: Alert ID to delete
        user_id: Current user ID from JWT
        db: Database connection

    Raises:
        HTTPException: 404 if alert not found or not owned by user
    """
    conn = db.connect()

    # Check ownership
    existing = conn.execute(
        """
        SELECT alert_id FROM user_alerts
        WHERE alert_id = ? AND user_id = ?
        """,
        [alert_id, user_id],
    ).fetchone()

    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    conn.execute(
        """
        DELETE FROM user_alerts
        WHERE alert_id = ? AND user_id = ?
        """,
        [alert_id, user_id],
    )
