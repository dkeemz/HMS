from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ── Doctor Profile schemas ───────────────────────────────────────────────


class DoctorProfileCreate(BaseModel):
    user_id: uuid.UUID
    specialty: str = Field(..., min_length=1, max_length=100)
    sub_specialty: str | None = Field(None, max_length=100)
    license_number: str = Field(..., min_length=1, max_length=50)
    qualifications: list[dict] | None = None
    consultation_hours: dict | None = None
    bio: str | None = None
    years_of_experience: int | None = Field(None, ge=0)
    consultation_fee: float | None = Field(None, ge=0)
    is_accepting_patients: bool = True


class DoctorProfileUpdate(BaseModel):
    specialty: str | None = Field(None, min_length=1, max_length=100)
    sub_specialty: str | None = Field(None, max_length=100)
    license_number: str | None = Field(None, min_length=1, max_length=50)
    qualifications: list[dict] | None = None
    consultation_hours: dict | None = None
    bio: str | None = None
    years_of_experience: int | None = Field(None, ge=0)
    consultation_fee: float | None = Field(None, ge=0)
    photo_url: str | None = Field(None, max_length=500)
    is_accepting_patients: bool | None = None


class AvailabilityUpdate(BaseModel):
    availability_status: Literal[
        "available", "on-leave", "in-surgery", "on-duty", "unavailable"
    ]


class DoctorUserNested(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    phone: str | None = None
    department_id: uuid.UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class DoctorProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    specialty: str
    sub_specialty: str | None = None
    license_number: str
    qualifications: list[dict] | None = None
    consultation_hours: dict | None = None
    bio: str | None = None
    years_of_experience: int | None = None
    consultation_fee: float | None = None
    photo_url: str | None = None
    is_accepting_patients: bool
    availability_status: str
    last_status_change_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    user: DoctorUserNested | None = None

    model_config = ConfigDict(from_attributes=True)
