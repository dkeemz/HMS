from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.schemas.break_glass import (
    BreakGlassAccessCheck,
    BreakGlassAuditEntry,
    BreakGlassAuditResponse,
    BreakGlassDenyRequest,
    BreakGlassFrequencyAlert,
    BreakGlassFrequencyAlertsResponse,
    BreakGlassRequest,
    BreakGlassResponse,
    BreakGlassReviewRequest,
)
from app.services.break_glass import BreakGlassService

router = APIRouter(prefix="/break-glass", tags=["break-glass"])


def _to_response(bg) -> BreakGlassResponse:
    return BreakGlassResponse(
        id=str(bg.id),
        doctor_id=str(bg.doctor_id),
        patient_id=str(bg.patient_id),
        reason=bg.reason,
        status=bg.status,
        approved_by=str(bg.approved_by) if bg.approved_by else None,
        approved_at=bg.approved_at,
        expires_at=bg.expires_at,
        access_started_at=bg.access_started_at,
        reviewed_by=str(bg.reviewed_by) if bg.reviewed_by else None,
        reviewed_at=bg.reviewed_at,
        review_notes=bg.review_notes,
        created_at=bg.created_at,
    )


# ── Request access ────────────────────────────────────────────────────────


@router.post(
    "/request",
    response_model=BreakGlassResponse,
    status_code=status.HTTP_201_CREATED,
)
async def request_break_glass(
    body: BreakGlassRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Request emergency break-glass access to a patient."""

    # Only doctors can request break-glass
    await _require_doctor(current_user, db)

    try:
        bg = await BreakGlassService.request_access(
            db,
            doctor_id=current_user.id,
            patient_id=body.patient_id,
            reason=body.reason,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return _to_response(bg)


# ── Pending requests ──────────────────────────────────────────────────────


@router.get("/pending", response_model=list[BreakGlassResponse])
async def get_pending_requests(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get pending break-glass requests (admin only)."""
    await _require_admin(current_user, db)

    requests, _ = await BreakGlassService.get_history(
        db, status="pending",
    )
    return [_to_response(bg) for bg in requests]


# ── Approve ───────────────────────────────────────────────────────────────


@router.post(
    "/{break_glass_id}/approve",
    response_model=BreakGlassResponse,
)
async def approve_break_glass(
    break_glass_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Approve a pending break-glass request (admin only)."""
    await _require_admin(current_user, db)

    try:
        bg = await BreakGlassService.approve_access(
            db,
            break_glass_id=break_glass_id,
            approved_by=current_user.id,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return _to_response(bg)


# ── Deny ──────────────────────────────────────────────────────────────────


@router.post(
    "/{break_glass_id}/deny",
    response_model=BreakGlassResponse,
)
async def deny_break_glass(
    break_glass_id: uuid.UUID,
    body: BreakGlassDenyRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Deny a pending break-glass request (admin only)."""
    await _require_admin(current_user, db)

    try:
        bg = await BreakGlassService.deny_access(
            db,
            break_glass_id=break_glass_id,
            denied_by=current_user.id,
            reason=body.reason,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return _to_response(bg)


# ── Check access ──────────────────────────────────────────────────────────


@router.get(
    "/check/{patient_id}",
    response_model=BreakGlassAccessCheck,
)
async def check_break_glass_access(
    patient_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Check if the current doctor has valid break-glass access to a patient."""
    await _require_doctor(current_user, db)

    has_access, expires_at = await BreakGlassService.check_access(
        db, doctor_id=current_user.id, patient_id=patient_id,
    )

    return BreakGlassAccessCheck(
        has_access=has_access,
        expires_at=expires_at,
    )


# ── Compliance review ─────────────────────────────────────────────────────


@router.post(
    "/{break_glass_id}/review",
    response_model=BreakGlassResponse,
)
async def review_break_glass(
    break_glass_id: uuid.UUID,
    body: BreakGlassReviewRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Compliance officer reviews break-glass access."""
    await _require_compliance_officer(current_user, db)

    try:
        bg = await BreakGlassService.review_access(
            db,
            break_glass_id=break_glass_id,
            reviewed_by=current_user.id,
            notes=body.notes,
        )
        await db.commit()
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return _to_response(bg)


# ── Frequency alerts ──────────────────────────────────────────────────────


@router.get("/alerts", response_model=BreakGlassFrequencyAlertsResponse)
async def get_frequency_alerts(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get doctors with excessive break-glass requests (compliance officer)."""
    await _require_compliance_officer(current_user, db)

    alerts = await BreakGlassService.check_frequency_alerts(db)

    return BreakGlassFrequencyAlertsResponse(
        alerts=[
            BreakGlassFrequencyAlert(**a) for a in alerts
        ],
        checked_at=datetime.now(UTC).isoformat(),
    )


# ── Pending reviews (24h compliance) ──────────────────────────────────────


@router.get("/pending-reviews")
async def get_pending_reviews(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get break-glass requests pending compliance review (compliance officer)."""
    await _require_compliance_officer(current_user, db)

    reviews = await BreakGlassService.check_pending_reviews(db)
    return reviews


# ── History ───────────────────────────────────────────────────────────────


@router.get("/history", response_model=list[BreakGlassResponse])
async def get_break_glass_history(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    doctor_id: uuid.UUID | None = Query(None),
    patient_id: uuid.UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get break-glass access history (admin/compliance officer)."""
    await _require_admin_or_compliance(current_user, db)

    entries, _ = await BreakGlassService.get_history(
        db,
        doctor_id=doctor_id,
        patient_id=patient_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )
    return [_to_response(bg) for bg in entries]


# ── Audit trail ───────────────────────────────────────────────────────────


@router.get(
    "/{break_glass_id}/audit",
    response_model=BreakGlassAuditResponse,
)
async def get_break_glass_audit(
    break_glass_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Get full audit trail for a break-glass request."""
    from sqlalchemy import select

    from app.models.break_glass_audit import BreakGlassAudit

    result = await db.execute(
        select(BreakGlassAudit)
        .where(BreakGlassAudit.break_glass_id == break_glass_id)
        .order_by(BreakGlassAudit.timestamp.asc())
    )
    entries = result.scalars().all()

    return BreakGlassAuditResponse(
        entries=[
            BreakGlassAuditEntry(
                id=str(e.id),
                break_glass_id=str(e.break_glass_id),
                action=e.action,
                user_id=str(e.user_id),
                details=e.details,
                timestamp=e.timestamp,
            )
            for e in entries
        ]
    )


# ── Expire check (scheduler) ──────────────────────────────────────────────


@router.post("/expire-check", status_code=status.HTTP_200_OK)
async def expire_check(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Trigger expired access check (admin or cron job)."""
    await _require_admin(current_user, db)

    count = await BreakGlassService.check_expired_access(db)
    await db.commit()
    return {"expired_count": count}


# ── Role check helpers ────────────────────────────────────────────────────

from datetime import UTC, datetime  # noqa: E402


async def _require_doctor(current_user, db: AsyncSession) -> None:
    from app.core.deps import require_role

    try:
        await require_role("doctor")(
            current_user=current_user, db=db,
        )
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only doctors can request break-glass access",
        )


async def _require_admin(current_user, db: AsyncSession) -> None:
    from sqlalchemy import select as _select

    from app.models.role import Role
    from app.models.user_role import UserRole

    result = await db.execute(
        _select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == current_user.id)
    )
    user_roles = {row[0] for row in result.all()}

    if "Admin" not in user_roles and "System Administrator" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required",
        )


async def _require_compliance_officer(current_user, db: AsyncSession) -> None:
    from sqlalchemy import select as _select

    from app.models.role import Role
    from app.models.user_role import UserRole

    result = await db.execute(
        _select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == current_user.id)
    )
    user_roles = {row[0] for row in result.all()}

    if "Compliance Officer" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compliance Officer role required",
        )


async def _require_admin_or_compliance(
    current_user, db: AsyncSession,
) -> None:
    from sqlalchemy import select as _select

    from app.models.role import Role
    from app.models.user_role import UserRole

    result = await db.execute(
        _select(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == current_user.id)
    )
    user_roles = {row[0] for row in result.all()}

    allowed = {"Admin", "System Administrator", "Compliance Officer"}
    if not user_roles.intersection(allowed):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Compliance Officer role required",
        )
