from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BreakGlassRequest(BaseModel):
    patient_id: uuid.UUID
    reason: str = Field(..., min_length=10, max_length=2000)


class BreakGlassDenyRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=2000)


class BreakGlassReviewRequest(BaseModel):
    notes: str = Field(..., min_length=10, max_length=2000)


class BreakGlassAuditEntry(BaseModel):
    id: str
    break_glass_id: str
    action: str
    user_id: str
    details: dict | None = None
    timestamp: datetime | None = None


class BreakGlassResponse(BaseModel):
    id: str
    doctor_id: str
    patient_id: str
    reason: str
    status: str
    approved_by: str | None = None
    approved_at: datetime | None = None
    expires_at: datetime | None = None
    access_started_at: datetime | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    review_notes: str | None = None
    created_at: datetime | None = None


class BreakGlassAccessCheck(BaseModel):
    has_access: bool
    expires_at: datetime | None = None


class BreakGlassAuditResponse(BaseModel):
    entries: list[BreakGlassAuditEntry]


class BreakGlassFrequencyAlert(BaseModel):
    doctor_id: str
    doctor_email: str
    request_count: int
    period_start: datetime
    period_end: datetime


class BreakGlassFrequencyAlertsResponse(BaseModel):
    alerts: list[BreakGlassFrequencyAlert]
    checked_at: str
