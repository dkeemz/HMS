from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.session import check_session_timeout, refresh_session

logger = logging.getLogger(__name__)

# Paths that bypass session checks (public / auth / docs).
_EXEMPT_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/api/v1/auth")


class SessionTimeoutMiddleware(BaseHTTPMiddleware):
    """Enforce the 15-minute inactivity timeout on authenticated requests.

    The middleware inspects the ``X-Session-ID`` header (set by the frontend
    after login).  If the session has expired it returns 401; otherwise the
    session's ``last_activity_at`` is refreshed and the request proceeds.
    """

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        path = request.url.path

        # Skip session checks for exempt paths.
        if any(path.startswith(p) for p in _EXEMPT_PREFIXES):
            return await call_next(request)

        session_id = request.headers.get("X-Session-ID")
        if session_id is None:
            return await call_next(request)

        try:

            from app.core.database import async_session

            async with async_session() as db:
                import uuid

                try:
                    sid = uuid.UUID(session_id)
                except ValueError:
                    return JSONResponse(
                        {"detail": "Invalid session ID"},
                        status_code=401,
                    )

                timed_out = await check_session_timeout(db, sid)
                if timed_out:
                    return JSONResponse(
                        {
                            "detail": "Session expired due to inactivity",
                            "code": "SESSION_TIMEOUT",
                        },
                        status_code=401,
                    )

                await refresh_session(db, sid)
                await db.commit()
        except Exception:
            logger.exception("Session check failed — allowing request through")

        return await call_next(request)
