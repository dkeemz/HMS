from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ProblemCreate(BaseModel):
    patient_id: uuid.UUID
    problem_name: str
    icd_code: str | None = None
    icd_version: str = "10"
    status: str = "active"
    onset_date: date | None = None
    resolved_date: date | None = None
    laterality: str | None = None
    chronicity: str | None = None
    notes: str | None = None


class ProblemUpdate(BaseModel):
    problem_name: str | None = None
    icd_code: str | None = None
    icd_version: str | None = None
    status: str | None = None
    onset_date: date | None = None
    resolved_date: date | None = None
    laterality: str | None = None
    chronicity: str | None = None
    notes: str | None = None


class ProblemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    problem_name: str
    icd_code: str | None
    icd_version: str
    status: str
    onset_date: date | None
    resolved_date: date | None
    laterality: str | None
    chronicity: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
