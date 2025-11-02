"""
Dependency injection for FastAPI routes.

Provides database connection, authentication, caching, and other dependencies.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwk, jwt
from jose.utils import base64url_decode
from slowapi import Limiter
from slowapi.util import get_remote_address

from axiom.core.db import Database
from services.api.config import settings

JWKS_CACHE_TTL = timedelta(hours=1)
JWKS_CACHE: dict[str, Any] = {"keys": [], "expires_at": datetime.min.replace(tzinfo=timezone.utc)}


def get_database() -> Database:
    """
    Get database connection dependency.

    Yields:
        Database instance
    """
    db = Database(db_path=settings.database_path)
    try:
        db.connect()
        yield db
    finally:
        db.close()


limiter = Limiter(key_func=get_remote_address)


async def _fetch_jwks(force_refresh: bool = False) -> list[dict[str, Any]]:
    """Fetch JWKS keys from Supabase with caching."""
    if not settings.supabase_jwks_url:
        return []

    now = datetime.now(timezone.utc)
    if (
        not force_refresh
        and JWKS_CACHE["keys"]
        and JWKS_CACHE["expires_at"]
        and JWKS_CACHE["expires_at"] > now
    ):
        return JWKS_CACHE["keys"]

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(settings.supabase_jwks_url)
        response.raise_for_status()
        jwks = response.json()

    keys = jwks.get("keys", [])
    JWKS_CACHE["keys"] = keys
    JWKS_CACHE["expires_at"] = now + JWKS_CACHE_TTL
    return keys


def _validate_claims(claims: dict[str, Any]) -> None:
    """Validate essential JWT claims."""
    now = datetime.now(timezone.utc)

    exp = claims.get("exp")
    if exp is not None:
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
        if now >= expires_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

    if settings.jwt_audience:
        aud = claims.get("aud")
        if isinstance(aud, str):
            audiences = [aud]
        elif isinstance(aud, list):
            audiences = aud
        else:
            audiences = []

        if settings.jwt_audience not in audiences:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token audience",
                headers={"WWW-Authenticate": "Bearer"},
            )


async def _verify_with_jwks(token: str) -> dict[str, Any]:
    """Verify JWT using Supabase JWKS."""
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token header: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    kid = header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing key identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    keys = await _fetch_jwks()
    key = next((item for item in keys if item.get("kid") == kid), None)

    if key is None:
        # Force refresh cache once
        keys = await _fetch_jwks(force_refresh=True)
        key = next((item for item in keys if item.get("kid") == kid), None)

    if key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signing key not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    segments = token.split(".")
    if len(segments) != 3:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid JWT structure",
            headers={"WWW-Authenticate": "Bearer"},
        )

    signing_input = "".join((segments[0], ".", segments[1]))
    signature = base64url_decode(segments[2].encode("utf-8"))

    public_key = jwk.construct(key)
    if not public_key.verify(signing_input.encode("utf-8"), signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token signature",
            headers={"WWW-Authenticate": "Bearer"},
        )

    claims = jwt.get_unverified_claims(token)
    _validate_claims(claims)
    return claims


async def verify_jwt_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Verify Supabase JWT token from Authorization header.

    Args:
        authorization: Authorization header value

    Returns:
        Decoded JWT payload with user information

    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    try:
        if settings.supabase_jwks_url:
            payload = await _verify_with_jwks(token)
        elif settings.supabase_jwt_secret:
            decode_kwargs: dict[str, Any] = {
                "algorithms": [settings.jwt_algorithm],
            }
            if settings.jwt_audience:
                decode_kwargs["audience"] = settings.jwt_audience

            payload = jwt.decode(token, settings.supabase_jwt_secret, **decode_kwargs)
            _validate_claims(payload)
        else:
            # Fallback for development only (no signature verification)
            payload = jwt.decode(token, options={"verify_signature": False})
            _validate_claims(payload)

        return payload

    except (JWTError, httpx.HTTPError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user(token_payload: dict = Depends(verify_jwt_token)) -> dict:
    """
    Get current authenticated user from JWT token.

    Args:
        token_payload: Decoded JWT payload

    Returns:
        User information dict with user_id and email

    Raises:
        HTTPException: If user information is missing
    """
    user_id = token_payload.get("sub")
    email = token_payload.get("email")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
        )

    return {
        "user_id": user_id,
        "email": email,
        "role": token_payload.get("role"),
    }


async def ensure_user_profile(
    db: Database = Depends(get_database), user: dict = Depends(get_current_user)
) -> str:
    """
    Ensure user profile exists in database and return user_id.

    Args:
        db: Database connection
        user: Current user information

    Returns:
        User ID string
    """
    user_id = user["user_id"]
    email = user.get("email")

    # Check if user profile exists, if not create it
    conn = db.connect()
    existing = conn.execute(
        "SELECT user_id FROM user_profiles WHERE user_id = ?", [user_id]
    ).fetchone()

    if not existing:
        # Create user profile
        conn.execute(
            """
            INSERT INTO user_profiles (user_id, email, created_at, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            [user_id, email],
        )

    return user_id
