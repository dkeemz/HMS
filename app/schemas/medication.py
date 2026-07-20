from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class MedicationCreate(BaseModel):
    patient_id: uuid.UUID
    medication_name: str
    generic_name: str | None = None
    strength: str | None = None
    dosage_form: str | None = None
    frequency: str | None = None
    route: str | None = None
    duration: str | None = None
    quantity: int | None = None
    refills: int | None = None
    status: str = "active"
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None


class MedicationUpdate(BaseModel):
    medication_name: str | None = None
    generic_name: str | None = None
    strength: str | None = None
    dosage_form: str | None = None
    frequency: str | None = None
    route: str | None = None
    duration: str | None = None
    quantity: int | None = None
    refills: int | None = None
    status: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None


class MedicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    prescribed_by: uuid.UUID | None
    medication_name: str
    generic_name: str | None
    strength: str | None
    dosage_form: str | None
    frequency: str | None
    route: str | None
    duration: str | None
    quantity: int | None
    refills: int | None
    status: str
    start_date: date | None
    end_date: date | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
