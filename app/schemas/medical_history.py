from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class AllergyCreate(BaseModel):
    name: str
    severity: str
    reaction: Optional[str] = None
    onset_date: Optional[date] = None
    status: str = "active"
    icd10_code: Optional[str] = None
    cross_reactivity_flags: Optional[str] = None
    verification_status: str = "unverified"
    source: str

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"mild", "moderate", "severe", "life-threatening"}
        if v not in allowed:
            raise ValueError(f"Severity must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"active", "corrected", "resolved"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("verification_status")
    @classmethod
    def validate_verification_status(cls, v: str) -> str:
        allowed = {"unverified", "confirmed", "ruled-out"}
        if v not in allowed:
            raise ValueError(f"Verification status must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        allowed = {"patient-reported", "clinical", "imported"}
        if v not in allowed:
            raise ValueError(f"Source must be one of: {', '.join(sorted(allowed))}")
        return v


class AllergyUpdate(BaseModel):
    name: Optional[str] = None
    severity: Optional[str] = None
    reaction: Optional[str] = None
    onset_date: Optional[date] = None
    status: Optional[str] = None
    icd10_code: Optional[str] = None
    cross_reactivity_flags: Optional[str] = None
    verification_status: Optional[str] = None

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"mild", "moderate", "severe", "life-threatening"}
            if v not in allowed:
                raise ValueError(f"Severity must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"active", "corrected", "resolved"}
            if v not in allowed:
                raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        return v


class AllergyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    name: str
    severity: str
    reaction: Optional[str] = None
    onset_date: Optional[date] = None
    status: str
    icd10_code: Optional[str] = None
    cross_reactivity_flags: Optional[str] = None
    verification_status: str
    source: str
    corrected_by: Optional[uuid.UUID] = None
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class ConditionCreate(BaseModel):
    name: str
    clinical_status: str = "active"
    verification_status: str = "unconfirmed"
    severity: Optional[str] = None
    onset_date: Optional[date] = None
    abatement_date: Optional[date] = None
    icd10_code: Optional[str] = None
    notes: Optional[str] = None
    source: str

    @field_validator("clinical_status")
    @classmethod
    def validate_clinical_status(cls, v: str) -> str:
        allowed = {"active", "recurrence", "remission", "resolved"}
        if v not in allowed:
            raise ValueError(f"Clinical status must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("verification_status")
    @classmethod
    def validate_verification_status(cls, v: str) -> str:
        allowed = {"unconfirmed", "provisional", "differential", "confirmed"}
        if v not in allowed:
            raise ValueError(f"Verification status must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"mild", "moderate", "severe"}
            if v not in allowed:
                raise ValueError(f"Severity must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        allowed = {"patient-reported", "clinical", "imported"}
        if v not in allowed:
            raise ValueError(f"Source must be one of: {', '.join(sorted(allowed))}")
        return v


class ConditionUpdate(BaseModel):
    name: Optional[str] = None
    clinical_status: Optional[str] = None
    verification_status: Optional[str] = None
    severity: Optional[str] = None
    onset_date: Optional[date] = None
    abatement_date: Optional[date] = None
    icd10_code: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("clinical_status")
    @classmethod
    def validate_clinical_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            allowed = {"active", "recurrence", "remission", "resolved"}
            if v not in allowed:
                raise ValueError(f"Clinical status must be one of: {', '.join(sorted(allowed))}")
        return v


class ConditionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    name: str
    clinical_status: str
    verification_status: str
    severity: Optional[str] = None
    onset_date: Optional[date] = None
    abatement_date: Optional[date] = None
    icd10_code: Optional[str] = None
    notes: Optional[str] = None
    source: str
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class SurgeryCreate(BaseModel):
    name: str
    procedure_date: date
    surgeon: Optional[str] = None
    facility: Optional[str] = None
    outcome: Optional[str] = None
    complications: Optional[str] = None
    notes: Optional[str] = None
    source: str

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        allowed = {"patient-reported", "clinical", "imported"}
        if v not in allowed:
            raise ValueError(f"Source must be one of: {', '.join(sorted(allowed))}")
        return v


class SurgeryUpdate(BaseModel):
    name: Optional[str] = None
    procedure_date: Optional[date] = None
    surgeon: Optional[str] = None
    facility: Optional[str] = None
    outcome: Optional[str] = None
    complications: Optional[str] = None
    notes: Optional[str] = None


class SurgeryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    name: str
    procedure_date: date
    surgeon: Optional[str] = None
    facility: Optional[str] = None
    outcome: Optional[str] = None
    complications: Optional[str] = None
    notes: Optional[str] = None
    source: str
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime


class FamilyHistoryCreate(BaseModel):
    condition_name: str
    relationship_type: str
    onset_age: Optional[int] = None
    icd10_code: Optional[str] = None
    is_hereditary: bool = False
    status: str = "living"
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"living", "deceased"}
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(sorted(allowed))}")
        return v


class FamilyHistoryUpdate(BaseModel):
    condition_name: Optional[str] = None
    relationship_type: Optional[str] = None
    onset_age: Optional[int] = None
    icd10_code: Optional[str] = None
    is_hereditary: Optional[bool] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class FamilyHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    patient_id: uuid.UUID
    condition_name: str
    relationship_type: str
    onset_age: Optional[int] = None
    icd10_code: Optional[str] = None
    is_hereditary: bool
    status: str
    notes: Optional[str] = None
    created_at: datetime