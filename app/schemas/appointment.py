"""Appointment schemas for Phase 4."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Appointment Type Config ──────────────────────────────────────────────
APPOINTMENT_TYPES = {
    "consultation": 15,
    "follow-up": 10,
    "procedure": 30,
    "emergency": 15,
    "lab": 15,
    "vaccination": 20,
    "other": 15,
}


# ── Request Schemas ──────────────────────────────────────────────────────
class AppointmentCreate(BaseModel):
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    department_id: uuid.UUID | None = None
    appointment_type: str = "consultation"
    scheduled_at: datetime
    duration_minutes: int = 15
    priority: str = "normal"
    room: str | None = None
    notes: str | None = None


class AppointmentUpdate(BaseModel):
    doctor_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    appointment_type: str | None = None
    scheduled_at: datetime | None = None
    duration_minutes: int | None = None
    priority: str | None = None
    room: str | None = None
    notes: str | None = None


class AppointmentReschedule(BaseModel):
    new_scheduled_at: datetime
    reason: str | None = None


class AppointmentCancel(BaseModel):
    reason: str = Field(..., min_length=1, max_length=200)


class WalkInCreate(BaseModel):
    patient_id: uuid.UUID
    department_id: uuid.UUID | None = None
    doctor_id: uuid.UUID | None = None
    appointment_type: str = "emergency"
    priority: str = "normal"
    notes: str | None = None


# ── Response Schemas ─────────────────────────────────────────────────────
class AppointmentResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID
    department_id: uuid.UUID | None = None
    appointment_type: str
    scheduled_at: datetime
    duration_minutes: int
    end_at: datetime
    status: str
    priority: str
    room: str | None = None
    notes: str | None = None
    cancellation_reason: str | None = None
    queue_position: int | None = None
    checked_in_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    # Embedded names for display
    patient_name: str | None = None
    doctor_name: str | None = None
    department_name: str | None = None

    model_config = {"from_attributes": True}


class AppointmentListResponse(BaseModel):
    items: list[AppointmentResponse]
    total: int


# ── Availability Schemas ─────────────────────────────────────────────────
class TimeSlot(BaseModel):
    start: datetime
    end: datetime
    available: bool
    doctor_id: uuid.UUID
    reason: str | None = None


class AvailabilityRequest(BaseModel):
    doctor_id: uuid.UUID
    date: datetime
    duration_minutes: int = 15


class AvailabilityResponse(BaseModel):
    doctor_id: uuid.UUID
    date: str
    slots: list[TimeSlot]


# ── Queue Schemas ────────────────────────────────────────────────────────
class QueuePosition(BaseModel):
    appointment_id: uuid.UUID
    patient_name: str
    position: int
    priority: str
    appointment_type: str
    arrived_at: datetime | None = None
    estimated_wait_minutes: int | None = None
