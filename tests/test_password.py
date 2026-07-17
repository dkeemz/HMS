"""Integration tests for password management endpoints."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_header, create_access_token, create_user

PREFIX = "/api/v1/password"


# ── POST /password/validate ──────────────────────────────────────────────


async def test_validate_strong_password(client: AsyncClient):
    """Strong password passes validation."""
    resp = await client.post(
        f"{PREFIX}/validate",
        json={"password": "S3cure!Passw0rd#2024"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True


async def test_validate_weak_password(client: AsyncClient):
    """Weak password fails validation."""
    resp = await client.post(
        f"{PREFIX}/validate",
        json={"password": "short"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False
    assert len(data["errors"]) > 0


async def test_validate_password_missing_uppercase(client: AsyncClient):
    """Password without uppercase fails."""
    resp = await client.post(
        f"{PREFIX}/validate",
        json={"password": "nouppercase123!@#"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is False


async def test_validate_password_missing_digit(client: AsyncClient):
    """Password without digit fails."""
    resp = await client.post(
        f"{PREFIX}/validate",
        json={"password": "NoDigitHere!!abc"},
    )
    assert resp.status_code == 200
    assert resp.json()["valid"] is False


# ── POST /password/reset-request ─────────────────────────────────────────


async def test_reset_request_nonexistent_email_returns_ok(client: AsyncClient):
    """Reset request for unknown email returns same message (no leak)."""
    resp = await client.post(
        f"{PREFIX}/reset-request",
        json={"email": "nonexistent@hms.local"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "reset link" in data["message"].lower()


async def test_reset_request_existing_user(
    client: AsyncClient, db_session: AsyncSession,
):
    """Reset request for existing user returns success and creates token."""
    await create_user(db_session, email="resetme@hms.local")
    await db_session.commit()

    resp = await client.post(
        f"{PREFIX}/reset-request",
        json={"email": "resetme@hms.local"},
    )
    assert resp.status_code == 200
    assert "reset link" in resp.json()["message"].lower()


# ── POST /password/reset-confirm ─────────────────────────────────────────


async def test_reset_confirm_invalid_token(client: AsyncClient):
    """Reset confirm with invalid token returns 400."""
    resp = await client.post(
        f"{PREFIX}/reset-confirm",
        json={"token": "nonexistent-token", "new_password": "N3w!Passw0rd#2024"},
    )
    assert resp.status_code == 400
    assert "invalid" in resp.json()["detail"].lower()


async def test_reset_confirm_weak_password(
    client: AsyncClient, db_session: AsyncSession,
):
    """Reset confirm with weak password returns 400."""
    from app.services.password_policy import PasswordPolicyService

    user = await create_user(db_session, email="weakreset@hms.local")
    token = await PasswordPolicyService.generate_reset_token(db_session, user.id)
    await db_session.commit()

    resp = await client.post(
        f"{PREFIX}/reset-confirm",
        json={"token": token, "new_password": "weak"},
    )
    assert resp.status_code == 400


# ── POST /password/change ────────────────────────────────────────────────


async def test_change_password_wrong_current(client: AsyncClient, admin_user):
    """Change password with wrong current password returns 401."""
    from app.api.v1 import password as pw_mod
    from tests.conftest import MockKeycloakService

    class _RejectingKC(MockKeycloakService):
        def get_token(self, username, password):
            raise Exception("Invalid credentials")

    original = pw_mod.KeycloakService
    pw_mod.dependency_overrides = {}
    # Use the test_app dependency override instead
    from tests.conftest import test_app
    test_app.dependency_overrides[original] = _RejectingKC

    try:
        token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
        resp = await client.post(
            f"{PREFIX}/change",
            json={"current_password": "wrong", "new_password": "N3w!Passw0rd#2024"},
            headers=auth_header(token),
        )
        assert resp.status_code == 401
    finally:
        from tests.conftest import _mock_keycloak_service
        test_app.dependency_overrides[original] = _mock_keycloak_service
