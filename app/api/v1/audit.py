from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_role
from app.models.user import User
from app.schemas.audit import (
    AuditLogEntry,
    AuditLogListResponse,
    AuditLogSearchResponse,
    AuditVerifyResponse,
    SecurityAlert,
    SecurityAlertsResponse,
)
from app.services.audit import AuditService

router = APIRouter(prefix="/audit", tags=["audit"])


# ── Search audit logs ──────────────────────────────────────────────────


@router.get("/logs", response_model=AuditLogSearchResponse)
async def search_audit_logs(
    user_id: uuid.UUID | None = Query(None),
    action: str | None = Query(None),
    resource: str | None = Query(None),
    patient_id: uuid.UUID | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    ip_address: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("Compliance Officer")),
):
    """Search audit logs with filters and pagination."""
    logs, total = await AuditService.search_logs(
        db,
        user_id=user_id,
        action=action,
        resource=resource,
        patient_id=patient_id,
        start_date=start_date,
        end_date=end_date,
        ip_address=ip_address,
        page=page,
        page_size=page_size,
    )

    return AuditLogSearchResponse(
        entries=[
            AuditLogEntry(
                id=str(log.id),
                user_id=str(log.user_id) if log.user_id else None,
                action=log.action,
                resource=log.resource,
                resource_id=log.resource_id,
                patient_id=str(log.patient_id) if log.patient_id else None,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                timestamp=log.timestamp,
                metadata=log.extra_data,
                previous_hash=log.previous_hash,
                hash=log.hash,
            )
            for log in logs
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── Export audit logs ──────────────────────────────────────────────────


@router.get("/logs/export", response_class=PlainTextResponse)
async def export_audit_logs(
    format: str = Query("csv", pattern="^(csv|pdf)$"),
    user_id: uuid.UUID | None = Query(None),
    action: str | None = Query(None),
    resource: str | None = Query(None),
    patient_id: uuid.UUID | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("Compliance Officer")),
):
    """Export audit logs to CSV."""
    await AuditService.log_event(
        db,
        user_id=current_user.id,
        action="export",
        resource="audit_log",
        metadata={
            "format": format,
            "filters": {
                "user_id": str(user_id) if user_id else None,
                "action": action,
                "resource": resource,
            },
        },
        patient_id=patient_id,
    )
    await db.commit()

    csv_content = await AuditService.export_logs(
        db,
        format=format,
        user_id=user_id,
        action=action,
        resource=resource,
        patient_id=patient_id,
        start_date=start_date,
        end_date=end_date,
    )

    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
    )


# ── Verify hash chain integrity ───────────────────────────────────────


@router.get("/verify", response_model=AuditVerifyResponse)
async def verify_audit_integrity(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("System Auditor")),
):
    """Verify hash chain integrity for a date range."""
    is_valid, broken_ids = await AuditService.verify_hash_chain(
        db, start_date, end_date
    )

    await AuditService.log_event(
        db,
        user_id=current_user.id,
        action="integrity_check",
        resource="audit_log",
        metadata={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "is_valid": is_valid,
            "broken_count": len(broken_ids),
        },
    )
    await db.commit()

    return AuditVerifyResponse(
        is_valid=is_valid,
        broken_entry_ids=[str(id_) for id_ in broken_ids],
        checked_start=start_date,
        checked_end=end_date,
        verified_by=str(current_user.id),
    )


# ── Security alerts ───────────────────────────────────────────────────


@router.get("/alerts", response_model=SecurityAlertsResponse)
async def get_security_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("Compliance Officer")),
):
    """Get current security alerts from pattern detection."""
    alerts = await AuditService.check_patterns(db)

    return SecurityAlertsResponse(
        alerts=[
            SecurityAlert(
                type=a["type"],
                severity=a["severity"],
                user_id=a.get("user_id"),
                count=a["count"],
                message=a["message"],
                detected_at=datetime.fromisoformat(a["detected_at"]),
            )
            for a in alerts
        ],
        checked_at=datetime.now().isoformat(),
    )


# ── Audit log list ────────────────────────────────────────────────────


@router.get("/logs/list", response_model=AuditLogListResponse)
async def list_audit_logs(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("Compliance Officer")),
):
    """List recent audit logs."""
    logs, total = await AuditService.search_logs(
        db,
        page=1,
        page_size=limit + offset,
    )
    logs = logs[offset : offset + limit]

    return AuditLogListResponse(
        entries=[
            AuditLogEntry(
                id=str(log.id),
                user_id=str(log.user_id) if log.user_id else None,
                action=log.action,
                resource=log.resource,
                resource_id=log.resource_id,
                patient_id=str(log.patient_id) if log.patient_id else None,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                timestamp=log.timestamp,
                metadata=log.extra_data,
                previous_hash=log.previous_hash,
                hash=log.hash,
            )
            for log in logs
        ],
        total=total,
    )
