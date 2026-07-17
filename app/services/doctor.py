from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.doctor_profile import DoctorProfile
from app.models.user import User
from app.schemas.doctor import DoctorProfileCreate, DoctorProfileUpdate
from app.services.audit import AuditService

logger = logging.getLogger(__name__)

VALID_STATUS_TRANSITIONS = {
    "available": {"on-leave", "in-surgery", "on-duty", "unavailable"},
    "on-leave": {"available"},
    "in-surgery": {"available", "on-duty"},
    "on-duty": {"available", "in-surgery"},
    "unavailable": {"available"},
}


class DoctorService:
    """Doctor profile CRUD and availability management."""

    @staticmethod
    async def create_profile(
        db: AsyncSession,
        data: DoctorProfileCreate,
        created_by: uuid.UUID,
    ) -> DoctorProfile:
        """Create a doctor profile linked to an existing user.

        Validates the user exists and does not already have a profile.
        """
        # 1. Validate user exists
        user = await db.get(User, data.user_id)
        if user is None:
            raise ValueError("User not found")

        # 2. Check no existing profile
        existing = await db.execute(
            select(DoctorProfile).where(DoctorProfile.user_id == data.user_id)
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError("User already has a doctor profile")

        # 3. Check license_number uniqueness
        lic = await db.execute(
            select(DoctorProfile).where(DoctorProfile.license_number == data.license_number)
        )
        if lic.scalar_one_or_none() is not None:
            raise ValueError("License number already in use")

        # 4. Create profile
        profile_data = data.model_dump()
        profile = DoctorProfile(**profile_data)
        db.add(profile)
        await db.flush()

        # 5. Audit log
        await AuditService.log_event(
            db,
            user_id=created_by,
            action="doctor_profile_created",
            resource="doctor_profile",
            resource_id=str(profile.id),
            why="New doctor profile registration",
        )
        await db.flush()

        await db.refresh(profile)
        logger.info("Created doctor profile %s for user %s", profile.id, data.user_id)
        return profile

    @staticmethod
    async def get_profile(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> DoctorProfile | None:
        """Get a doctor profile by user_id with eager-loaded user."""
        result = await db.execute(
            select(DoctorProfile)
            .options(selectinload(DoctorProfile.user))
            .where(DoctorProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_doctors(
        db: AsyncSession,
        department_id: uuid.UUID | None = None,
        specialty: str | None = None,
        is_accepting: bool | None = None,
        availability_status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[DoctorProfile], int]:
        """List doctor profiles with optional filters and pagination."""
        conditions = []
        if department_id is not None:
            conditions.append(User.department_id == department_id)
        if specialty is not None:
            conditions.append(DoctorProfile.specialty == specialty)
        if is_accepting is not None:
            conditions.append(DoctorProfile.is_accepting_patients == is_accepting)
        if availability_status is not None:
            conditions.append(DoctorProfile.availability_status == availability_status)

        where_clause = and_(*conditions) if conditions else True

        # Count
        count_q = (
            select(func.count())
            .select_from(DoctorProfile)
            .join(User, DoctorProfile.user_id == User.id)
            .where(where_clause)
        )
        total = (await db.execute(count_q)).scalar_one()

        # Fetch page
        offset = (page - 1) * page_size
        result = await db.execute(
            select(DoctorProfile)
            .options(selectinload(DoctorProfile.user))
            .join(User, DoctorProfile.user_id == User.id)
            .where(where_clause)
            .order_by(DoctorProfile.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        doctors = list(result.scalars().all())
        return doctors, total

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        user_id: uuid.UUID,
        data: DoctorProfileUpdate,
        updated_by: uuid.UUID,
    ) -> DoctorProfile:
        """Update a doctor profile."""
        profile = await DoctorService.get_profile(db, user_id)
        if profile is None:
            raise ValueError("Doctor profile not found")

        update_data = data.model_dump(exclude_unset=True)

        # Check license_number uniqueness if changing
        if "license_number" in update_data and update_data["license_number"] != profile.license_number:
            lic = await db.execute(
                select(DoctorProfile).where(
                    DoctorProfile.license_number == update_data["license_number"]
                )
            )
            if lic.scalar_one_or_none() is not None:
                raise ValueError("License number already in use")

        for field, value in update_data.items():
            setattr(profile, field, value)

        await AuditService.log_event(
            db,
            user_id=updated_by,
            action="doctor_profile_updated",
            resource="doctor_profile",
            resource_id=str(profile.id),
            why="Doctor profile update",
            metadata={"updated_fields": list(update_data.keys())},
        )
        await db.flush()
        await db.refresh(profile)
        return profile

    @staticmethod
    async def update_availability(
        db: AsyncSession,
        user_id: uuid.UUID,
        new_status: str,
        changed_by: uuid.UUID,
    ) -> DoctorProfile:
        """Update availability status with transition validation."""
        profile = await DoctorService.get_profile(db, user_id)
        if profile is None:
            raise ValueError("Doctor profile not found")

        # Validate transition
        current = profile.availability_status
        allowed = VALID_STATUS_TRANSITIONS.get(current, set())
        if new_status not in allowed:
            raise ValueError(
                f"Invalid status transition from '{current}' to '{new_status}'. "
                f"Allowed: {', '.join(sorted(allowed))}"
            )

        old_status = profile.availability_status
        profile.availability_status = new_status
        profile.last_status_change_at = datetime.now(UTC)

        await AuditService.log_event(
            db,
            user_id=changed_by,
            action="availability_changed",
            resource="doctor_profile",
            resource_id=str(profile.id),
            why=f"Availability changed from {old_status} to {new_status}",
            metadata={"old_status": old_status, "new_status": new_status},
        )
        await db.flush()
        await db.refresh(profile)
        logger.info(
            "Availability changed for user %s: %s → %s",
            user_id, old_status, new_status,
        )
        return profile

    @staticmethod
    async def search_doctors(
        db: AsyncSession,
        q: str,
        department_id: uuid.UUID | None = None,
        specialty: str | None = None,
    ) -> list[DoctorProfile]:
        """Search doctors by name, specialty, or department."""
        pattern = f"%{q.strip()}%"

        conditions = [
            or_(
                User.first_name.ilike(pattern),
                User.last_name.ilike(pattern),
                DoctorProfile.specialty.ilike(pattern),
                DoctorProfile.sub_specialty.ilike(pattern),
                DoctorProfile.license_number.ilike(pattern),
            )
        ]
        if department_id is not None:
            conditions.append(User.department_id == department_id)
        if specialty is not None:
            conditions.append(DoctorProfile.specialty == specialty)

        result = await db.execute(
            select(DoctorProfile)
            .options(selectinload(DoctorProfile.user))
            .join(User, DoctorProfile.user_id == User.id)
            .where(and_(*conditions))
            .order_by(DoctorProfile.created_at.desc())
            .limit(50)
        )
        return list(result.scalars().all())
