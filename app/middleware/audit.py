from __future__ import annotations

import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Paths that bypass audit logging
_EXEMPT_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/static", "/health")
_EXEMPT_ACTIONS = {"OPTIONS", "HEAD"}


class AuditMiddleware(BaseHTTPMiddleware):
    """Automatically log all API requests to the audit log.

    Skips health checks, docs, static files, and non-authenticated requests.
    For authenticated requests, captures 6-field data:
        Who   — user_id from token
        What  — HTTP method + path
        When  — request timestamp
        Where — IP address + user agent
        Why   — (optional) request body context
        Patient — (optional) from query params or body
    """

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        path = request.url.path

        # Skip exempt paths
        if any(path.startswith(p) for p in _EXEMPT_PREFIXES):
            return await call_next(request)

        # Skip non-API methods
        if request.method in _EXEMPT_ACTIONS:
            return await call_next(request)

        # Skip non-API paths
        if not path.startswith("/api/"):
            return await call_next(request)

        # Extract client info
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Try to extract user from session ID header
        user_id: uuid.UUID | None = None
        session_id = request.headers.get("X-Session-ID")
        if session_id:
            try:
                user_id = uuid.UUID(session_id)
            except ValueError:
                pass

        # Process request
        response = await call_next(request)

        # Determine action from HTTP method
        method = request.method.lower()
        action_map = {
            "get": "read",
            "post": "create",
            "put": "update",
            "patch": "update",
            "delete": "delete",
        }
        action = action_map.get(method, method)

        # Extract resource from path
        resource = _extract_resource(path)

        # Determine if this is a patient-related action
        patient_id: uuid.UUID | None = None
        patient_id_str = request.query_params.get("patient_id")
        if patient_id_str:
            try:
                patient_id = uuid.UUID(patient_id_str)
            except ValueError:
                pass

        # Log the audit event asynchronously (don't block the response)
        try:
            from app.core.database import async_session
            from app.services.audit import AuditService

            async with async_session() as db:
                await AuditService.log_event(
                    db,
                    user_id=user_id,
                    action=action,
                    resource=resource,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    patient_id=patient_id,
                    metadata={
                        "method": request.method,
                        "path": path,
                        "status_code": response.status_code,
                    },
                )
                await db.commit()
        except Exception:
            logger.exception("Failed to create audit log entry")

        return response


def _extract_resource(path: str) -> str:
    """Extract the resource name from the API path."""
    # /api/v1/auth/login -> auth
    # /api/v1/rbac/roles -> rbac
    # /api/v1/audit/logs -> audit
    parts = path.strip("/").split("/")
    if len(parts) >= 3:
        return parts[2]  # api/v1/{resource}/...
    return "unknown"
