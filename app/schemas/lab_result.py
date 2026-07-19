"""Lab Result schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class LabResultCreate(BaseModel):
    visit_id: uuid.UUID
    patient_id: uuid.UUID
    test_name: str
    category: str = "chemistry"
    clinical_question: str | None = None

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        allowed = {
            "hematology", "chemistry", "urinalysis", "microbiology",
            "pathology", "immunology", "endocrinology", "other",
        }
        if v not in allowed:
            raise ValueError(f"category must be one of: {', '.join(sorted(allowed))}")
        return v


class LabResultUpdate(BaseModel):
    result_value: str | None = None
    result_unit: str | None = None
    reference_range: str | None = None
    abnormal_flag: str | None = None
    notes: str | None = None
    status: str | None = None

    @field_validator("abnormal_flag")
    @classmethod
    def validate_flag(cls, v: str | None) -> str | None:
        if v is not None:
            allowed = {"normal", "high", "low", "critical_high", "critical_low"}
            if v not in allowed:
                raise ValueError(f"abnormal_flag must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str | None) -> str | None:
        if v is not None:
            allowed = {"ordered", "in_progress", "completed", "cancelled"}
            if v not in allowed:
                raise ValueError(f"status must be one of: {', '.join(sorted(allowed))}")
        return v


class LabResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    visit_id: uuid.UUID
    patient_id: uuid.UUID
    ordered_by: uuid.UUID
    completed_by: uuid.UUID | None
    test_name: str
    category: str
    clinical_question: str | None
    result_value: str | None
    result_unit: str | None
    reference_range: str | None
    abnormal_flag: str
    notes: str | None
    status: str
    ordered_at: datetime
    completed_at: datetime | None
    created_at: datetime
