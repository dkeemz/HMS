from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.insurance_policy import InsurancePolicy
from app.models.patient import InsuranceProvider
from app.schemas.insurance import InsurancePolicyCreate
from app.services.audit import AuditService


class InsuranceService:
    """Insurance policy lifecycle management with state machine."""

    VALID_TRANSITIONS = {
        "pending": ["verified", "expired"],
        "verified": ["active", "expired"],
        "active": ["expired"],
        "expired": [],
    }

    @staticmethod
    async def create_policy(
        db: AsyncSession,
        patient_id: uuid.UUID,
        data: InsurancePolicyCreate,
        created_by: uuid.UUID,
    ) -> InsurancePolicy:
        policy = InsurancePolicy(
            patient_id=patient_id,
            provider_id=uuid.UUID(data.provider_id),
            policy_number=data.policy_number,
            policy_type=data.policy_type,
            coverage_type=data.coverage_type,
            status="pending",
            start_date=data.start_date,
            end_date=data.end_date,
            coverage_limit=data.coverage_limit,
            copay_percentage=data.copay_percentage,
            coinsurance_percentage=data.coinsurance_percentage,
            notes=data.notes,
        )
        db.add(policy)
        await db.flush()

        await AuditService.log_event(
            db,
            user_id=created_by,
            action="insurance_policy_created",
            resource="insurance_policy",
            resource_id=str(policy.id),
            patient_id=patient_id,
            metadata={"policy_type": data.policy_type, "coverage_type": data.coverage_type},
            why="Insurance policy created",
        )
        await db.flush()
        return policy

    @staticmethod
    async def get_policies_for_patient(
        db: AsyncSession, patient_id: uuid.UUID
    ) -> list[InsurancePolicy]:
        result = await db.execute(
            select(InsurancePolicy)
            .where(InsurancePolicy.patient_id == patient_id)
            .order_by(InsurancePolicy.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_policy(
        db: AsyncSession, policy_id: uuid.UUID
    ) -> InsurancePolicy | None:
        result = await db.execute(
            select(InsurancePolicy).where(InsurancePolicy.id == policy_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def transition_status(
        db: AsyncSession,
        policy_id: uuid.UUID,
        new_status: str,
        changed_by: uuid.UUID,
        reason: str | None = None,
    ) -> InsurancePolicy:
        policy = await InsuranceService.get_policy(db, policy_id)
        if policy is None:
            raise ValueError("Policy not found")

        allowed = InsuranceService.VALID_TRANSITIONS.get(policy.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Invalid transition: {policy.status} -> {new_status}. "
                f"Allowed: {allowed}"
            )

        old_status = policy.status
        policy.status = new_status
        now = datetime.now()

        if new_status == "verified":
            policy.verified_at = now
            policy.verified_by = changed_by
        elif new_status == "active":
            policy.activated_at = now
        elif new_status == "expired":
            policy.expired_at = now

        await AuditService.log_event(
            db,
            user_id=changed_by,
            action="insurance_status_transition",
            resource="insurance_policy",
            resource_id=str(policy.id),
            patient_id=policy.patient_id,
            metadata={
                "old_status": old_status,
                "new_status": new_status,
                "reason": reason,
            },
            why=f"Insurance policy status changed from {old_status} to {new_status}",
        )
        await db.flush()
        return policy

    @staticmethod
    async def get_expired_policies(
        db: AsyncSession,
    ) -> list[InsurancePolicy]:
        today = date.today()
        result = await db.execute(
            select(InsurancePolicy).where(
                InsurancePolicy.status != "expired",
                InsurancePolicy.end_date.isnot(None),
                InsurancePolicy.end_date < today,
            )
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_providers(db: AsyncSession) -> list[InsuranceProvider]:
        result = await db.execute(
            select(InsuranceProvider).where(InsuranceProvider.is_active.is_(True))
        )
        return list(result.scalars().all())
