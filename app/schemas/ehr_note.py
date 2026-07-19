"""EHR Clinical Note schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class EhrNoteCreate(BaseModel):
    visit_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID | None = None
    subjective: str = ""
    objective: str = ""
    assessment: str = ""
    plan: str = ""
    note_type: str = "consultation"

    @field_validator("note_type")
    @classmethod
    def validate_note_type(cls, v: str) -> str:
        allowed = {"consultation", "follow_up", "procedure", "discharge"}
        if v not in allowed:
            raise ValueError(f"note_type must be one of: {', '.join(sorted(allowed))}")
        return v


class EhrNoteUpdate(BaseModel):
    subjective: str | None = None
    objective: str | None = None
    assessment: str | None = None
    plan: str | None = None
    note_type: str | None = None
    amendment_reason: str | None = None

    @field_validator("note_type")
    @classmethod
    def validate_note_type(cls, v: str | None) -> str | None:
        if v is not None:
            allowed = {"consultation", "follow_up", "procedure", "discharge"}
            if v not in allowed:
                raise ValueError(f"note_type must be one of: {', '.join(sorted(allowed))}")
        return v


class EhrNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    visit_id: uuid.UUID
    patient_id: uuid.UUID
    doctor_id: uuid.UUID | None
    encounter_date: datetime
    subjective: str
    objective: str
    assessment: str
    plan: str
    note_type: str
    status: str
    signed_at: datetime | None
    amended_at: datetime | None
    created_at: datetime
