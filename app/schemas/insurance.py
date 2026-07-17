from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class InsuranceProviderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    provider_type: str
    short_code: str
    website: str | None = None
    is_active: bool = True


class InsurancePolicyCreate(BaseModel):
    provider_id: str
    policy_number: str
    policy_type: Literal["primary", "secondary", "dependent"]
    coverage_type: Literal["NHIS", "HMO", "Private", "Corporate", "Military", "Tertiary"]
    start_date: date
    end_date: date | None = None
    coverage_limit: float | None = None
    copay_percentage: float | None = None
    coinsurance_percentage: float | None = None
    notes: str | None = None


class InsurancePolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    provider_id: uuid.UUID
    policy_number: str
    policy_type: str
    coverage_type: str
    status: str
    start_date: date
    end_date: date | None = None
    coverage_limit: float | None = None
    copay_percentage: float | None = None
    coinsurance_percentage: float | None = None
    card_image_url: str | None = None
    dependent_patient_id: uuid.UUID | None = None
    verified_at: datetime | None = None
    verified_by: uuid.UUID | None = None
    activated_at: datetime | None = None
    expired_at: datetime | None = None
    notes: str | None = None
    created_at: datetime | None = None


class InsuranceStatusTransition(BaseModel):
    new_status: Literal["verified", "active", "expired"]
    reason: str | None = None
