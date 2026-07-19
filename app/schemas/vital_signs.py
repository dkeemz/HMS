"""Vital Signs schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class VitalSignCreate(BaseModel):
    visit_id: uuid.UUID
    patient_id: uuid.UUID
    systolic_bp: int | None = None
    diastolic_bp: int | None = None
    heart_rate: int | None = None
    respiratory_rate: int | None = None
    temperature: Decimal | None = None
    weight_kg: Decimal | None = None
    height_cm: Decimal | None = None
    spo2: int | None = None
    pain_level: int | None = None
    notes: str | None = None

    @field_validator("systolic_bp", "diastolic_bp", "heart_rate", "respiratory_rate", "spo2", "pain_level")
    @classmethod
    def validate_positive(cls, v: int | None) -> int | None:
        if v is not None and v < 0:
            raise ValueError("Value must be non-negative")
        return v

    @field_validator("pain_level")
    @classmethod
    def validate_pain(cls, v: int | None) -> int | None:
        if v is not None and (v < 0 or v > 10):
            raise ValueError("Pain level must be 0-10")
        return v

    @field_validator("spo2")
    @classmethod
    def validate_spo2(cls, v: int | None) -> int | None:
        if v is not None and (v < 0 or v > 100):
            raise ValueError("SpO2 must be 0-100")
        return v


class VitalSignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    visit_id: uuid.UUID
    patient_id: uuid.UUID
    recorded_by: uuid.UUID | None
    recorded_at: datetime
    systolic_bp: int | None
    diastolic_bp: int | None
    heart_rate: int | None
    respiratory_rate: int | None
    temperature: Decimal | None
    weight_kg: Decimal | None
    height_cm: Decimal | None
    spo2: int | None
    pain_level: int | None
    notes: str | None
    created_at: datetime
