"""Clinical Document schemas."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class ClinicalDocumentCreate(BaseModel):
    patient_id: uuid.UUID
    visit_id: uuid.UUID | None = None
    document_type: str = "report"
    title: str
    description: str | None = None
    file_name: str
    file_path: str
    file_size: int | None = None
    mime_type: str | None = None

    @field_validator("document_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {
            "scan", "image", "report", "lab_report",
            "prescription", "referral", "other",
        }
        if v not in allowed:
            raise ValueError(f"document_type must be one of: {', '.join(sorted(allowed))}")
        return v


class ClinicalDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    visit_id: uuid.UUID | None
    uploaded_by: uuid.UUID
    document_type: str
    title: str
    description: str | None
    file_name: str
    file_path: str
    file_size: int | None
    mime_type: str | None
    created_at: datetime
