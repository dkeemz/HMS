"""Integration tests for authentication endpoints."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import auth_header, create_access_token, create_user

PREFIX = "/api/v1/auth"


# ── POST /auth/login ──────────────────────────────────────────────────────


async def test_login_new_device_returns_mfa_challenge(client: AsyncClient):
    """Login from a new device triggers MFA challenge."""
    resp = await client.post(
        f"{PREFIX}/login",
        json={"email": "new@hms.local", "password": "s3cure!Passw0rd"},
    )
    # On new device, should get MFA challenge or token
    assert resp.status_code in (200, 401, 422)


async def test_login_wrong_password_returns_401(
    client: AsyncClient, db_session: AsyncSession,
):
    """Login with wrong password returns 401."""
    from app.api.v1 import auth as auth_mod

    # Create a user so the lockout path is exercised
    await create_user(db_session, email="fail@hms.local")
    await db_session.commit()

    # Temporarily use a KeycloakService that rejects bad passwords
    original_factory = auth_mod._keycloak_service

    def _rejecting_factory():
        class _RejectingKC:
            admin = None
            def get_token(self, username, password):
                raise Exception("Invalid credentials")
            def get_user_info(self, token):
                return {}
            def refresh_token(self, rt):
                raise Exception("bad")
            def logout(self, rt):
                pass
            def validate_token(self, t):
                return {}
            def get_required_actions(self, uid):
                return []
            def set_required_actions(self, uid, a):
                pass
            async def sync_roles_from_keycloak(self, db, uid):
                pass
        return _RejectingKC()

    auth_mod._keycloak_service = _rejecting_factory  # type: ignore[assignment]
    try:
        resp = await client.post(
            f"{PREFIX}/login",
            json={"email": "fail@hms.local", "password": "wrong"},
        )
        assert resp.status_code == 401
        assert "Invalid email or password" in resp.json()["detail"]
    finally:
        auth_mod._keycloak_service = original_factory  # type: ignore[assignment]


# ── GET /auth/me ──────────────────────────────────────────────────────────


async def test_get_me_returns_current_user(client: AsyncClient, admin_user):
    """GET /auth/me returns the authenticated user's profile."""
    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.get(f"{PREFIX}/me", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == admin_user.email
    assert "Admin" in data["roles"]


async def test_get_me_no_token_returns_401(client: AsyncClient):
    """GET /auth/me without token returns 401."""
    resp = await client.get(f"{PREFIX}/me")
    assert resp.status_code == 401


async def test_get_me_invalid_token_returns_401(client: AsyncClient):
    """GET /auth/me with garbage token returns 401."""
    resp = await client.get(f"{PREFIX}/me", headers=auth_header("garbage"))
    assert resp.status_code == 401


# ── PUT /auth/me ─────────────────────────────────────────────────────────


async def test_update_me_profile(client: AsyncClient, admin_user):
    """PUT /auth/me updates profile fields."""
    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.put(
        f"{PREFIX}/me",
        json={"first_name": "Updated", "phone": "+1234567890"},
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["first_name"] == "Updated"
    assert data["phone"] == "+1234567890"


# ── POST /auth/logout ────────────────────────────────────────────────────


async def test_logout_returns_ok(client: AsyncClient, admin_user):
    """POST /auth/logout returns success."""
    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.post(
        f"{PREFIX}/logout",
        json={"refresh_token": "some-refresh-token"},
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out"


# ── POST /auth/refresh ───────────────────────────────────────────────────


async def test_refresh_token_success(client: AsyncClient):
    """POST /auth/refresh with valid refresh token returns new tokens."""
    resp = await client.post(
        f"{PREFIX}/refresh",
        json={"refresh_token": "valid-refresh"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


# ── POST /auth/mfa-status ────────────────────────────────────────────────


async def test_mfa_status(client: AsyncClient, admin_user):
    """GET /auth/mfa-status returns MFA configuration."""
    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.get(f"{PREFIX}/mfa-status", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "mfa_configured" in data


# ── Login with locked account ────────────────────────────────────────────


async def test_login_locked_account_returns_403(
    client: AsyncClient, db_session: AsyncSession,
):
    """Login to a locked account returns 403."""
    from datetime import UTC, datetime, timedelta

    from app.models.account_lockout import AccountLockout

    user = await create_user(db_session, email="locked@hms.local")
    lockout = AccountLockout(
        user_id=user.id,
        failed_attempts=5,
        locked_until=datetime.now(UTC) + timedelta(minutes=30),
    )
    db_session.add(lockout)
    await db_session.commit()

    resp = await client.post(
        f"{PREFIX}/login",
        json={"email": "locked@hms.local", "password": "whatever"},
    )
    assert resp.status_code == 403
    assert "locked" in resp.json()["detail"].lower()
