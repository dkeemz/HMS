"""Diagnosis schemas."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator


class DiagnosisCreate(BaseModel):
    visit_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID | None = None
    icd_code: str
    icd_version: str = "10"
    description: str
    diagnosis_type: str = "primary"
    onset_date: date | None = None
    notes: str | None = None

    @field_validator("diagnosis_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"primary", "secondary", "differential"}
        if v not in allowed:
            raise ValueError(f"diagnosis_type must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("icd_version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        if v not in ("10", "11"):
            raise ValueError("icd_version must be '10' or '11'")
        return v


class DiagnosisUpdate(BaseModel):
    icd_code: str | None = None
    description: str | None = None
    diagnosis_type: str | None = None
    status: str | None = None
    resolved_date: date | None = None
    notes: str | None = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None:
            allowed = {"active", "resolved", "ruled_out"}
            if v not in allowed:
                raise ValueError(f"status must be one of: {', '.join(sorted(allowed))}")
        return v


class DiagnosisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    visit_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID | None
    icd_code: str
    icd_version: str
    description: str
    diagnosis_type: str
    status: str
    onset_date: date | None
    resolved_date: date | None
    notes: str | None
    created_at: datetime
