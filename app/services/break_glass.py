from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.break_glass import BreakGlassAccess
from app.models.break_glass_audit import BreakGlassAudit
from app.models.role import Role
from app.models.user import User
from app.models.user_role import UserRole

logger = logging.getLogger(__name__)


class BreakGlassService:
    """Break-glass emergency access workflow service."""

    ACCESS_DURATION_HOURS = 1
    COMPLIANCE_REVIEW_HOURS = 24
    MAX_REQUESTS_PER_WEEK = 3

    # ── Request access ────────────────────────────────────────────────────

    @staticmethod
    async def request_access(
        db: AsyncSession,
        doctor_id: uuid.UUID,
        patient_id: uuid.UUID,
        reason: str,
    ) -> BreakGlassAccess:
        """Doctor requests emergency access to a patient.

        Checks frequency limits, creates a pending request, writes an audit
        trail entry, and notifies admins + compliance officer + dept head.
        """
        # Check frequency limit
        await BreakGlassService._check_frequency_limit(db, doctor_id)

        # Check for an existing pending request for the same patient
        existing = await db.execute(
            select(BreakGlassAccess).where(
                and_(
                    BreakGlassAccess.doctor_id == doctor_id,
                    BreakGlassAccess.patient_id == patient_id,
                    BreakGlassAccess.status == "pending",
                )
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError(
                "A pending break-glass request already exists for this patient"
            )

        bg = BreakGlassAccess(
            doctor_id=doctor_id,
            patient_id=patient_id,
            reason=reason,
            status="pending",
        )
        db.add(bg)
        await db.flush()

        # Audit trail entry
        await BreakGlassService._create_audit_entry(
            db,
            break_glass_id=bg.id,
            action="requested",
            user_id=doctor_id,
            details={
                "patient_id": str(patient_id),
                "reason": reason,
            },
        )

        await db.flush()

        # Notify admins, compliance officers, and dept heads
        await BreakGlassService._notify_request_created(db, bg)

        logger.info(
            "Break-glass request created: doctor=%s patient=%s reason=%s",
            doctor_id,
            patient_id,
            reason[:80],
        )

        return bg

    # ── Approve access ────────────────────────────────────────────────────

    @staticmethod
    async def approve_access(
        db: AsyncSession,
        break_glass_id: uuid.UUID,
        approved_by: uuid.UUID,
    ) -> BreakGlassAccess:
        """Admin approves a break-glass request.

        Sets the access window to 1 hour from now.
        """
        bg = await db.get(BreakGlassAccess, break_glass_id)
        if bg is None:
            raise ValueError("Break-glass request not found")
        if bg.status != "pending":
            raise ValueError(
                f"Cannot approve request with status '{bg.status}'"
            )

        now = datetime.now(UTC)
        bg.status = "approved"
        bg.approved_by = approved_by
        bg.approved_at = now
        bg.expires_at = now + timedelta(hours=BreakGlassService.ACCESS_DURATION_HOURS)

        await BreakGlassService._create_audit_entry(
            db,
            break_glass_id=bg.id,
            action="approved",
            user_id=approved_by,
            details={
                "expires_at": bg.expires_at.isoformat(),
                "access_duration_hours": BreakGlassService.ACCESS_DURATION_HOURS,
            },
        )

        await db.flush()

        # Notify the requesting doctor
        await BreakGlassService._notify_access_approved(db, bg)

        logger.info(
            "Break-glass request approved: id=%s approved_by=%s expires=%s",
            break_glass_id,
            approved_by,
            bg.expires_at,
        )

        return bg

    # ── Deny access ───────────────────────────────────────────────────────

    @staticmethod
    async def deny_access(
        db: AsyncSession,
        break_glass_id: uuid.UUID,
        denied_by: uuid.UUID,
        reason: str,
    ) -> BreakGlassAccess:
        """Admin denies a break-glass request."""
        bg = await db.get(BreakGlassAccess, break_glass_id)
        if bg is None:
            raise ValueError("Break-glass request not found")
        if bg.status != "pending":
            raise ValueError(
                f"Cannot deny request with status '{bg.status}'"
            )

        bg.status = "denied"
        bg.approved_by = denied_by
        bg.approved_at = datetime.now(UTC)

        await BreakGlassService._create_audit_entry(
            db,
            break_glass_id=bg.id,
            action="denied",
            user_id=denied_by,
            details={"deny_reason": reason},
        )

        await db.flush()

        await BreakGlassService._notify_access_denied(db, bg, reason)

        logger.info(
            "Break-glass request denied: id=%s denied_by=%s",
            break_glass_id,
            denied_by,
        )

        return bg

    # ── Check access ──────────────────────────────────────────────────────

    @staticmethod
    async def check_access(
        db: AsyncSession,
        doctor_id: uuid.UUID,
        patient_id: uuid.UUID,
    ) -> tuple[bool, datetime | None]:
        """Check if a doctor has valid break-glass access to a patient.

        Returns (has_access, expires_at).
        """
        now = datetime.now(UTC)
        result = await db.execute(
            select(BreakGlassAccess).where(
                and_(
                    BreakGlassAccess.doctor_id == doctor_id,
                    BreakGlassAccess.patient_id == patient_id,
                    BreakGlassAccess.status == "approved",
                    BreakGlassAccess.expires_at > now,
                )
            )
        )
        bg = result.scalar_one_or_none()

        if bg is None:
            return False, None

        # Record access event
        await BreakGlassService._create_audit_entry(
            db,
            break_glass_id=bg.id,
            action="accessed",
            user_id=doctor_id,
            details={"patient_id": str(patient_id)},
        )
        await db.flush()

        return True, bg.expires_at

    # ── Record resource access ────────────────────────────────────────────

    @staticmethod
    async def record_access(
        db: AsyncSession,
        break_glass_id: uuid.UUID,
        resource: str,
        resource_id: str,
    ) -> None:
        """Record that a doctor accessed a resource during break-glass."""
        bg = await db.get(BreakGlassAccess, break_glass_id)
        if bg is None or bg.status != "approved":
            raise ValueError("Invalid break-glass session")

        now = datetime.now(UTC)
        if bg.expires_at and bg.expires_at < now:
            raise ValueError("Break-glass access has expired")

        if bg.access_started_at is None:
            bg.access_started_at = now

        await BreakGlassService._create_audit_entry(
            db,
            break_glass_id=bg.id,
            action="accessed",
            user_id=bg.doctor_id,
            details={
                "resource": resource,
                "resource_id": resource_id,
                "patient_id": str(bg.patient_id),
            },
        )

        await db.flush()

    # ── Compliance review ─────────────────────────────────────────────────

    @staticmethod
    async def review_access(
        db: AsyncSession,
        break_glass_id: uuid.UUID,
        reviewed_by: uuid.UUID,
        notes: str,
    ) -> BreakGlassAccess:
        """Compliance officer reviews break-glass access (within 24 hours).

        Must be completed within COMPLIANCE_REVIEW_HOURS of request creation.
        """
        bg = await db.get(BreakGlassAccess, break_glass_id)
        if bg is None:
            raise ValueError("Break-glass request not found")

        # Check that review is within 24-hour window
        if bg.created_at:
            now = datetime.now(UTC)
            deadline = bg.created_at + timedelta(
                hours=BreakGlassService.COMPLIANCE_REVIEW_HOURS
            )
            if now > deadline:
                raise ValueError(
                    "Compliance review deadline has passed — "
                    "further break-glass requests by this user are blocked"
                )

        bg.reviewed_by = reviewed_by
        bg.reviewed_at = datetime.now(UTC)
        bg.review_notes = notes

        await BreakGlassService._create_audit_entry(
            db,
            break_glass_id=bg.id,
            action="reviewed",
            user_id=reviewed_by,
            details={"notes": notes},
        )

        await db.flush()

        logger.info(
            "Break-glass access reviewed: id=%s reviewed_by=%s",
            break_glass_id,
            reviewed_by,
        )

        return bg

    # ── Expire access ─────────────────────────────────────────────────────

    @staticmethod
    async def check_expired_access(db: AsyncSession) -> int:
        """Mark expired break-glass access.  Run periodically via a scheduler.

        Returns the number of entries expired.
        """
        now = datetime.now(UTC)
        result = await db.execute(
            select(BreakGlassAccess).where(
                and_(
                    BreakGlassAccess.status == "approved",
                    BreakGlassAccess.expires_at <= now,
                )
            )
        )
        expired = result.scalars().all()

        for bg in expired:
            bg.status = "expired"
            await BreakGlassService._create_audit_entry(
                db,
                break_glass_id=bg.id,
                action="expired",
                user_id=bg.doctor_id,
                details={
                    "expires_at": bg.expires_at.isoformat()
                    if bg.expires_at
                    else None,
                    "access_started_at": bg.access_started_at.isoformat()
                    if bg.access_started_at
                    else None,
                },
            )

        if expired:
            await db.flush()
            logger.info(
                "Expired %d break-glass access entries", len(expired),
            )

        return len(expired)

    # ── Frequency alerts ──────────────────────────────────────────────────

    @staticmethod
    async def check_frequency_alerts(
        db: AsyncSession,
    ) -> list[dict]:
        """Check for doctors with > MAX_REQUESTS_PER_WEEK break-glass requests.

        Also blocks further requests if a 24-hour compliance review was missed.
        """
        now = datetime.now(UTC)
        week_ago = now - timedelta(days=7)

        # Doctors with > 3 requests in the past week
        result = await db.execute(
            select(
                BreakGlassAccess.doctor_id,
                func.count().label("request_count"),
            )
            .where(
                and_(
                    BreakGlassAccess.created_at >= week_ago,
                    BreakGlassAccess.status.in_(
                        ["pending", "approved", "expired"]
                    ),
                )
            )
            .group_by(BreakGlassAccess.doctor_id)
            .having(func.count() > BreakGlassService.MAX_REQUESTS_PER_WEEK)
        )

        alerts: list[dict] = []
        for doctor_id, count in result.all():
            user = await db.get(User, doctor_id)
            if user is None:
                continue
            alerts.append({
                "doctor_id": str(doctor_id),
                "doctor_email": user.email,
                "request_count": count,
                "period_start": week_ago.isoformat(),
                "period_end": now.isoformat(),
            })

        return alerts

    # ── Pending review check (24h compliance) ─────────────────────────────

    @staticmethod
    async def check_pending_reviews(db: AsyncSession) -> list[dict]:
        """Find break-glass requests that were approved but never reviewed
        within the 24-hour compliance window.
        """
        now = datetime.now(UTC)
        deadline = now - timedelta(hours=BreakGlassService.COMPLIANCE_REVIEW_HOURS)

        result = await db.execute(
            select(BreakGlassAccess).where(
                and_(
                    BreakGlassAccess.status.in_(["approved", "expired"]),
                    BreakGlassAccess.reviewed_by.is_(None),
                    BreakGlassAccess.created_at < deadline,
                )
            )
        )
        return [
            {
                "id": str(bg.id),
                "doctor_id": str(bg.doctor_id),
                "patient_id": str(bg.patient_id),
                "created_at": bg.created_at.isoformat() if bg.created_at else None,
                "expires_at": bg.expires_at.isoformat() if bg.expires_at else None,
                "status": bg.status,
            }
            for bg in result.scalars().all()
        ]

    # ── History / audit trail ─────────────────────────────────────────────

    @staticmethod
    async def get_history(
        db: AsyncSession,
        doctor_id: uuid.UUID | None = None,
        patient_id: uuid.UUID | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[BreakGlassAccess], int]:
        """Get break-glass history with filters."""
        conditions = []
        if doctor_id is not None:
            conditions.append(BreakGlassAccess.doctor_id == doctor_id)
        if patient_id is not None:
            conditions.append(BreakGlassAccess.patient_id == patient_id)
        if status is not None:
            conditions.append(BreakGlassAccess.status == status)

        where_clause = and_(*conditions) if conditions else True

        count_result = await db.execute(
            select(func.count()).select_from(BreakGlassAccess).where(where_clause)
        )
        total = count_result.scalar_one()

        result = await db.execute(
            select(BreakGlassAccess)
            .where(where_clause)
            .order_by(BreakGlassAccess.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    # ── Internal helpers ──────────────────────────────────────────────────

    @staticmethod
    async def _check_frequency_limit(
        db: AsyncSession, doctor_id: uuid.UUID,
    ) -> None:
        """Raise ValueError if the doctor exceeded the weekly request limit."""
        now = datetime.now(UTC)
        week_ago = now - timedelta(days=7)

        result = await db.execute(
            select(func.count())
            .select_from(BreakGlassAccess)
            .where(
                and_(
                    BreakGlassAccess.doctor_id == doctor_id,
                    BreakGlassAccess.created_at >= week_ago,
                    BreakGlassAccess.status.in_(
                        ["pending", "approved", "expired"]
                    ),
                )
            )
        )
        count = result.scalar_one()

        if count >= BreakGlassService.MAX_REQUESTS_PER_WEEK:
            raise ValueError(
                f"Frequency limit exceeded: {count} requests in the past week "
                f"(max {BreakGlassService.MAX_REQUESTS_PER_WEEK})"
            )

    @staticmethod
    async def _create_audit_entry(
        db: AsyncSession,
        break_glass_id: uuid.UUID,
        action: str,
        user_id: uuid.UUID,
        details: dict | None = None,
    ) -> BreakGlassAudit:
        """Create a break-glass audit trail entry."""
        entry = BreakGlassAudit(
            break_glass_id=break_glass_id,
            action=action,
            user_id=user_id,
            details=details,
        )
        db.add(entry)
        return entry

    # ── Notifications ─────────────────────────────────────────────────────

    @staticmethod
    async def _notify_request_created(
        db: AsyncSession, bg: BreakGlassAccess,
    ) -> None:
        """Notify admin + compliance officer + dept head of a new request."""
        from app.services.notifications import NotificationService

        doctor = await db.get(User, bg.doctor_id)
        doctor_name = (
            f"{doctor.first_name} {doctor.last_name}" if doctor else "Unknown"
        )

        notification_details = {
            "break_glass_id": str(bg.id),
            "doctor_id": str(bg.doctor_id),
            "doctor_name": doctor_name,
            "patient_id": str(bg.patient_id),
            "reason": bg.reason,
        }

        # Notify admins
        admin_emails = await BreakGlassService._get_role_emails(db, "Admin")
        for email in admin_emails:
            await NotificationService.send_break_glass_request_notification(
                email, notification_details,
            )

        # Notify compliance officers
        co_emails = await BreakGlassService._get_role_emails(
            db, "Compliance Officer"
        )
        for email in co_emails:
            await NotificationService.send_break_glass_request_notification(
                email, notification_details,
            )

        # Notify department heads
        dept_head_emails = await BreakGlassService._get_role_emails(
            db, "Department Head"
        )
        for email in dept_head_emails:
            await NotificationService.send_break_glass_request_notification(
                email, notification_details,
            )

    @staticmethod
    async def _notify_access_approved(
        db: AsyncSession, bg: BreakGlassAccess,
    ) -> None:
        """Notify the requesting doctor that access was approved."""
        from app.services.notifications import NotificationService

        doctor = await db.get(User, bg.doctor_id)
        if doctor:
            await NotificationService.send_break_glass_approved_notification(
                doctor.email,
                {
                    "break_glass_id": str(bg.id),
                    "patient_id": str(bg.patient_id),
                    "expires_at": bg.expires_at.isoformat()
                    if bg.expires_at
                    else None,
                },
            )

    @staticmethod
    async def _notify_access_denied(
        db: AsyncSession, bg: BreakGlassAccess, reason: str,
    ) -> None:
        """Notify the requesting doctor that access was denied."""
        from app.services.notifications import NotificationService

        doctor = await db.get(User, bg.doctor_id)
        if doctor:
            await NotificationService.send_break_glass_denied_notification(
                doctor.email,
                {
                    "break_glass_id": str(bg.id),
                    "patient_id": str(bg.patient_id),
                    "deny_reason": reason,
                },
            )

    @staticmethod
    async def _get_role_emails(
        db: AsyncSession, role_name: str,
    ) -> list[str]:
        """Get email addresses for all users with a given role."""
        result = await db.execute(
            select(User.email)
            .join(UserRole, UserRole.user_id == User.id)
            .join(Role, Role.id == UserRole.role_id)
            .where(
                and_(
                    Role.name == role_name,
                    UserRole.status == "approved",
                )
            )
            .distinct()
        )
        return [row[0] for row in result.all()]
