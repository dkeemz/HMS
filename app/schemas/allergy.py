from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AllergyCreate(BaseModel):
    patient_id: uuid.UUID
    allergen: str
    allergen_category: str | None = None
    reaction: str | None = None
    severity: str = "moderate"
    status: str = "active"
    notes: str | None = None


class AllergyUpdate(BaseModel):
    allergen: str | None = None
    allergen_category: str | None = None
    reaction: str | None = None
    severity: str | None = None
    status: str | None = None
    notes: str | None = None


class AllergyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    allergen: str
    allergen_category: str | None
    reaction: str | None
    severity: str
    status: str
    recorded_date: datetime
    resolved_date: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
