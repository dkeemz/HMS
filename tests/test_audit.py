"""Integration tests for audit endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from tests.conftest import auth_header, create_access_token

PREFIX = "/api/v1/audit"


# ── GET /audit/logs ──────────────────────────────────────────────────────


async def test_search_audit_logs_as_compliance(client: AsyncClient, compliance_user):
    """Compliance Officer can search audit logs."""
    token = create_access_token(
        sub=str(compliance_user.id), email=compliance_user.email
    )
    resp = await client.get(f"{PREFIX}/logs", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "entries" in data
    assert "total" in data


async def test_search_audit_logs_non_compliance_returns_403(
    client: AsyncClient, admin_user,
):
    """Non-Compliance Officer gets 403 on audit logs search."""
    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.get(f"{PREFIX}/logs", headers=auth_header(token))
    assert resp.status_code == 403


# ── GET /audit/logs/list ─────────────────────────────────────────────────


async def test_list_audit_logs(client: AsyncClient, compliance_user):
    """Compliance Officer can list audit logs."""
    token = create_access_token(
        sub=str(compliance_user.id), email=compliance_user.email
    )
    resp = await client.get(f"{PREFIX}/logs/list", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "entries" in data
    assert "total" in data


# ── GET /audit/verify ────────────────────────────────────────────────────


async def test_verify_audit_integrity(client: AsyncClient, auditor_user):
    """System Auditor can verify hash chain integrity."""
    token = create_access_token(sub=str(auditor_user.id), email=auditor_user.email)
    now = datetime.now(UTC)
    resp = await client.get(
        f"{PREFIX}/verify",
        params={
            "start_date": (now - timedelta(days=1)).isoformat(),
            "end_date": now.isoformat(),
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "is_valid" in data
    assert "broken_entry_ids" in data


async def test_verify_audit_non_auditor_returns_403(client: AsyncClient, admin_user):
    """Non-auditor gets 403 on verify endpoint."""
    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    now = datetime.now(UTC)
    resp = await client.get(
        f"{PREFIX}/verify",
        params={
            "start_date": (now - timedelta(days=1)).isoformat(),
            "end_date": now.isoformat(),
        },
        headers=auth_header(token),
    )
    assert resp.status_code == 403


# ── GET /audit/alerts ────────────────────────────────────────────────────


async def test_get_security_alerts(client: AsyncClient, compliance_user):
    """Compliance Officer can get security alerts."""
    token = create_access_token(
        sub=str(compliance_user.id), email=compliance_user.email
    )
    resp = await client.get(f"{PREFIX}/alerts", headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert "alerts" in data
    assert "checked_at" in data


# ── GET /audit/logs/export ───────────────────────────────────────────────


async def test_export_audit_logs_csv(client: AsyncClient, compliance_user):
    """Compliance Officer can export audit logs as CSV."""
    token = create_access_token(
        sub=str(compliance_user.id), email=compliance_user.email
    )
    resp = await client.get(
        f"{PREFIX}/logs/export",
        params={"format": "csv"},
        headers=auth_header(token),
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "text/csv; charset=utf-8"


async def test_export_audit_logs_non_compliance_returns_403(
    client: AsyncClient, admin_user,
):
    """Non-compliance gets 403 on export."""
    token = create_access_token(sub=str(admin_user.id), email=admin_user.email)
    resp = await client.get(
        f"{PREFIX}/logs/export",
        params={"format": "csv"},
        headers=auth_header(token),
    )
    assert resp.status_code == 403
