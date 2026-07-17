from __future__ import annotations

import csv
import hashlib
import io
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Central audit logging service with 6-field capture and hash chain integrity."""

    # ── Core logging ─────────────────────────────────────────────────────

    @staticmethod
    async def log_event(
        db: AsyncSession,
        user_id: uuid.UUID | None,
        action: str,
        resource: str,
        resource_id: str | None = None,
        metadata: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        patient_id: uuid.UUID | None = None,
        why: str | None = None,
    ) -> AuditLog:
        """Log an audit event with 6-field capture and hash chain.

        6-field capture:
            Who   — user_id
            What  — action + resource
            When  — timestamp (server default)
            Where — ip_address + user_agent
            Why   — metadata["why"] or why parameter
            Patient — patient_id
        """
        # Get the last audit log entry for hash chain
        prev_result = await db.execute(
            select(AuditLog.hash)
            .order_by(AuditLog.timestamp.desc())
            .limit(1)
        )
        prev_hash = prev_result.scalar_one_or_none() or ""

        now = datetime.now(UTC)

        # Build metadata with "why" field
        final_metadata = dict(metadata) if metadata else {}
        if why:
            final_metadata["why"] = why

        # Compute SHA-256 hash of (prev_hash + user_id + action + resource + timestamp)
        payload = json.dumps(
            {
                "prev_hash": prev_hash,
                "user_id": str(user_id) if user_id else "",
                "action": action,
                "resource": resource,
                "resource_id": resource_id or "",
                "timestamp": now.isoformat(),
            },
            sort_keys=True,
        )
        entry_hash = hashlib.sha256(payload.encode()).hexdigest()

        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            extra_data=final_metadata if final_metadata else None,
            ip_address=ip_address,
            user_agent=user_agent,
            previous_hash=prev_hash,
            hash=entry_hash,
            patient_id=patient_id,
        )
        db.add(log_entry)
        return log_entry

    # ── Hash chain verification ──────────────────────────────────────────

    @staticmethod
    async def verify_hash_chain(
        db: AsyncSession,
        start_date: datetime,
        end_date: datetime,
    ) -> tuple[bool, list[uuid.UUID]]:
        """Verify hash chain integrity for a date range.

        Returns (is_valid, list_of_broken_entry_ids).
        """
        result = await db.execute(
            select(AuditLog)
            .where(
                and_(
                    AuditLog.timestamp >= start_date,
                    AuditLog.timestamp <= end_date,
                )
            )
            .order_by(AuditLog.timestamp.asc())
        )
        entries = list(result.scalars().all())

        if not entries:
            return True, []

        is_valid = True
        broken_ids: list[uuid.UUID] = []
        prev_hash = ""

        for entry in entries:
            # Check previous_hash linkage
            if entry.previous_hash != prev_hash:
                is_valid = False
                broken_ids.append(entry.id)
                prev_hash = entry.hash
                continue

            # Recompute hash and compare
            payload = json.dumps(
                {
                    "prev_hash": entry.previous_hash or "",
                    "user_id": str(entry.user_id) if entry.user_id else "",
                    "action": entry.action,
                    "resource": entry.resource,
                    "resource_id": entry.resource_id or "",
                    "timestamp": entry.timestamp.isoformat(),
                },
                sort_keys=True,
            )
            expected_hash = hashlib.sha256(payload.encode()).hexdigest()
            if expected_hash != entry.hash:
                is_valid = False
                broken_ids.append(entry.id)

            prev_hash = entry.hash

        return is_valid, broken_ids

    # ── Search and filter ────────────────────────────────────────────────

    @staticmethod
    async def search_logs(
        db: AsyncSession,
        user_id: uuid.UUID | None = None,
        action: str | None = None,
        resource: str | None = None,
        patient_id: uuid.UUID | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        ip_address: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Search audit logs with filters and pagination."""
        conditions = []
        if user_id is not None:
            conditions.append(AuditLog.user_id == user_id)
        if action is not None:
            conditions.append(AuditLog.action == action)
        if resource is not None:
            conditions.append(AuditLog.resource == resource)
        if patient_id is not None:
            conditions.append(AuditLog.patient_id == patient_id)
        if start_date is not None:
            conditions.append(AuditLog.timestamp >= start_date)
        if end_date is not None:
            conditions.append(AuditLog.timestamp <= end_date)
        if ip_address is not None:
            conditions.append(AuditLog.ip_address == ip_address)

        where_clause = and_(*conditions) if conditions else True

        # Count total
        count_result = await db.execute(
            select(func.count()).select_from(AuditLog).where(where_clause)
        )
        total = count_result.scalar_one()

        # Fetch page
        offset = (page - 1) * page_size
        result = await db.execute(
            select(AuditLog)
            .where(where_clause)
            .order_by(AuditLog.timestamp.desc())
            .limit(page_size)
            .offset(offset)
        )
        logs = list(result.scalars().all())

        return logs, total

    # ── Export ───────────────────────────────────────────────────────────

    @staticmethod
    async def export_logs(
        db: AsyncSession,
        format: str = "csv",
        **filters: object,
    ) -> str:
        """Export audit logs to CSV or PDF.

        Returns the file content as a string (CSV) or file path (PDF).
        """
        # Remove pagination params from filters
        filters.pop("page", None)
        filters.pop("page_size", None)

        logs, _ = await AuditService.search_logs(db, page_size=10000, **filters)  # type: ignore[arg-type]

        if format == "csv":
            return AuditService._export_csv(logs)

        if format == "pdf":
            raise HTTPException(
                status_code=501,
                detail="PDF export is not yet implemented. Use CSV format.",
            )

        raise HTTPException(
            status_code=400,
            detail=f"Unsupported export format: {format}. Use 'csv' or 'pdf'.",
        )

    @staticmethod
    def _export_csv(logs: list[AuditLog]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id", "user_id", "action", "resource", "resource_id",
            "patient_id", "ip_address", "user_agent", "timestamp",
            "previous_hash", "hash", "metadata",
        ])
        for log in logs:
            writer.writerow([
                str(log.id),
                str(log.user_id) if log.user_id else "",
                log.action,
                log.resource,
                log.resource_id or "",
                str(log.patient_id) if log.patient_id else "",
                log.ip_address or "",
                log.user_agent or "",
                log.timestamp.isoformat() if log.timestamp else "",
                log.previous_hash or "",
                log.hash,
                json.dumps(log.extra_data) if log.extra_data else "",
            ])
        return output.getvalue()

    # ── Pattern-based alerting ───────────────────────────────────────────

    @staticmethod
    async def check_patterns(db: AsyncSession) -> list[dict]:
        """Check for suspicious patterns (failed logins, off-hours, bulk exports)."""
        alerts: list[dict] = []
        now = datetime.now(UTC)

        # 1. 5+ failed logins in 5 minutes
        five_min_ago = now - timedelta(minutes=5)
        result = await db.execute(
            select(AuditLog.user_id, func.count().label("cnt"))
            .where(
                and_(
                    AuditLog.action == "login_failed",
                    AuditLog.timestamp >= five_min_ago,
                )
            )
            .group_by(AuditLog.user_id)
            .having(func.count() >= 5)
        )
        for user_id, count in result.all():
            alerts.append({
                "type": "brute_force",
                "severity": "critical",
                "user_id": str(user_id),
                "count": count,
                "message": (
                    f"{count} failed login attempts in 5 minutes "
                    f"for user {user_id}"
                ),
                "detected_at": now.isoformat(),
            })

        # 2. Activity outside normal hours (10pm - 6am)
        if now.hour >= 22 or now.hour < 6:
            one_hour_ago = now - timedelta(hours=1)
            result = await db.execute(
                select(AuditLog.user_id, func.count().label("cnt"))
                .where(
                    and_(
                        AuditLog.timestamp >= one_hour_ago,
                        AuditLog.action.notin_(["session_refresh", "heartbeat"]),
                    )
                )
                .group_by(AuditLog.user_id)
                .having(func.count() >= 3)
            )
            for user_id, count in result.all():
                alerts.append({
                    "type": "off_hours_activity",
                    "severity": "warning",
                    "user_id": str(user_id),
                    "count": count,
                    "message": f"{count} actions during off-hours for user {user_id}",
                    "detected_at": now.isoformat(),
                })

        # 3. Bulk data exports (>100 records in 1 hour)
        one_hour_ago = now - timedelta(hours=1)
        result = await db.execute(
            select(AuditLog.user_id, func.count().label("cnt"))
            .where(
                and_(
                    AuditLog.action == "export",
                    AuditLog.timestamp >= one_hour_ago,
                )
            )
            .group_by(AuditLog.user_id)
            .having(func.count() > 100)
        )
        for user_id, count in result.all():
            alerts.append({
                "type": "bulk_export",
                "severity": "high",
                "user_id": str(user_id),
                "count": count,
                "message": f"{count} export operations in 1 hour by user {user_id}",
                "detected_at": now.isoformat(),
            })

        return alerts

    # ── Retention cleanup ────────────────────────────────────────────────

    @staticmethod
    async def cleanup_old_logs(
        db: AsyncSession,
        retention_years: int = 6,
    ) -> int:
        """Delete audit logs older than retention period. Returns count deleted."""
        cutoff = datetime.now(UTC) - timedelta(days=retention_years * 365)
        result = await db.execute(
            select(func.count()).select_from(AuditLog).where(
                AuditLog.timestamp < cutoff
            )
        )
        count = result.scalar_one()

        if count > 0:
            await db.execute(
                delete(AuditLog).where(AuditLog.timestamp < cutoff)
            )
            await db.flush()
            logger.info(
                "Cleaned up %d audit log entries older than %d years",
                count,
                retention_years,
            )

        return count
