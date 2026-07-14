from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.session import UserSession


def _expires_at() -> datetime:
    return datetime.now(UTC) + timedelta(
        minutes=settings.SESSION_TIMEOUT_MINUTES
    )


async def create_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    device_info: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    device_fingerprint: str | None = None,
    keycloak_session_id: str | None = None,
) -> UserSession:
    """Create a new tracked session with automatic expiry."""
    session = UserSession(
        user_id=user_id,
        device_fingerprint=device_fingerprint,
        device_info=device_info,
        ip_address=ip_address,
        user_agent=user_agent,
        keycloak_session_id=keycloak_session_id,
        is_active=True,
        last_activity_at=datetime.now(UTC),
        expires_at=_expires_at(),
    )
    db.add(session)

    max_sessions = settings.MAX_CONCURRENT_SESSIONS_DEFAULT
    await _enforce_concurrent_limit(db, user_id, max_sessions)

    await db.flush()
    return session


async def check_session_timeout(
    db: AsyncSession, session_id: uuid.UUID
) -> bool:
    """Return True if the session has timed out."""
    result = await db.execute(
        select(UserSession).where(UserSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None or not session.is_active:
        return True
    return datetime.now(UTC) > session.expires_at


async def refresh_session(db: AsyncSession, session_id: uuid.UUID) -> None:
    """Extend the session expiry (called on each authenticated request)."""
    await db.execute(
        update(UserSession)
        .where(UserSession.id == session_id, UserSession.is_active.is_(True))
        .values(
            last_activity_at=datetime.now(UTC),
            expires_at=_expires_at(),
        )
    )
    await db.flush()


async def invalidate_session(db: AsyncSession, session_id: uuid.UUID) -> None:
    """Deactivate a single session."""
    await db.execute(
        update(UserSession)
        .where(UserSession.id == session_id)
        .values(is_active=False)
    )
    await db.flush()


async def invalidate_all_sessions(
    db: AsyncSession, user_id: uuid.UUID
) -> None:
    """Deactivate every session for a user (e.g. on password change)."""
    await db.execute(
        update(UserSession)
        .where(UserSession.user_id == user_id, UserSession.is_active.is_(True))
        .values(is_active=False)
    )
    await db.flush()


async def _enforce_concurrent_limit(
    db: AsyncSession, user_id: uuid.UUID, max_sessions: int
) -> None:
    """Deactivate oldest sessions when the limit is exceeded."""
    result = await db.execute(
        select(UserSession)
        .where(UserSession.user_id == user_id, UserSession.is_active.is_(True))
        .order_by(UserSession.last_activity_at.asc())
    )
    active = list(result.scalars().all())

    if len(active) >= max_sessions:
        to_deactivate = active[: len(active) - max_sessions + 1]
        for s in to_deactivate:
            s.is_active = False
