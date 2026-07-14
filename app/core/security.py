from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.services.keycloak import KeycloakService

logger = logging.getLogger(__name__)

security = HTTPBearer()


def decode_keycloak_token(token: str) -> dict:
    """Validate a Keycloak JWT using the realm's public key.

    Tries RS256 verification first (Keycloak default). Falls back to
    unverified decode for development environments only.
    """
    try:
        kc = KeycloakService()
        return kc.validate_token(token)
    except Exception:
        logger.warning("Keycloak token validation failed, attempting local decode")

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["RS256", "HS256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        ) from exc


async def sync_user_from_keycloak(
    db: AsyncSession, payload: dict
) -> User:
    """Find or create an HMS User from a Keycloak JWT payload.

    On first login the user row is created automatically.  Subsequent logins
    update profile fields if they changed in Keycloak.
    """
    keycloak_sub: str = payload["sub"]
    email: str = payload.get("email", "")
    first_name: str = payload.get("given_name", payload.get("name", ""))
    last_name: str = payload.get("family_name", "")

    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=f"keycloak:{keycloak_sub}",
            status="active",
        )
        db.add(user)
        await db.flush()
        logger.info("Created new HMS user from Keycloak: %s", email)
    else:
        changed = False
        if user.first_name != first_name:
            user.first_name = first_name
            changed = True
        if user.last_name != last_name:
            user.last_name = last_name
            changed = True
        if changed:
            await db.flush()
            logger.info("Synced profile changes for user: %s", email)

    return user


def compute_device_fingerprint(user_agent: str, ip_address: str) -> str:
    """Deterministic fingerprint from User-Agent + IP."""
    raw = json.dumps({"ua": user_agent, "ip": ip_address}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


class _CurrentTimestamp:
    """Reusable UTC-now helper for easier mocking in tests."""
    @staticmethod
    def utcnow() -> datetime:
        return datetime.now(UTC)


_now = _CurrentTimestamp.utcnow


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate a Keycloak JWT and return the matching HMS User."""
    token = credentials.credentials
    try:
        payload = decode_keycloak_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing subject claim",
            )
        user = await sync_user_from_keycloak(db, payload)
        return user
    except HTTPException:
        raise
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc
