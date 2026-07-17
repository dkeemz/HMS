from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class VisitCreate(BaseModel):
    department_id: str | None = None
    doctor_id: str | None = None
    reason: Literal[
        "consultation", "follow-up", "procedure", "emergency", "lab", "vaccination", "other"
    ]
    reason_notes: str | None = None
    scheduled_at: datetime | None = None


class VisitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    appointment_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    doctor_id: uuid.UUID | None = None
    reason: str
    reason_notes: str | None = None
    status: str
    scheduled_at: datetime | None = None
    checked_in_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    duration_minutes: int | None = None
    cancellation_reason: str | None = None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class VisitStatusTransition(BaseModel):
    new_status: Literal["checked-in", "in-progress", "completed", "cancelled"]
    reason: str | None = None


class VisitSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    visit_id: uuid.UUID
    doctor_name: str | None = None
    diagnosis: str | None = None
    diagnoses: list | None = None
    prescriptions: list | None = None
    procedures_performed: list | None = None
    lab_orders: list | None = None
    notes: str | None = None
    generated_at: datetime


class VisitReferralCreate(BaseModel):
    referring_doctor_id: str
    destination_department_id: str
    reason: str
    notes: str | None = None


class VisitReferralResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    visit_id: uuid.UUID
    referring_doctor_id: uuid.UUID
    destination_department_id: uuid.UUID
    reason: str
    notes: str | None = None
    status: str
    created_at: datetime
