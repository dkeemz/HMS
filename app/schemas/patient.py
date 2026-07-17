from __future__ import annotations

import re
import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ── Nested sub-schemas ────────────────────────────────────────────────────

class EmergencyContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    phone: str = Field(..., pattern=r"^(\+234|0)[789]\d{9}$")
    relationship: str = Field(..., min_length=1, max_length=50)


class NextOfKinCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    phone: str = Field(..., pattern=r"^(\+234|0)[789]\d{9}$")
    relationship: str = Field(..., min_length=1, max_length=50)
    address: str | None = None


class EmergencyContactResponse(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    relationship: str

    model_config = ConfigDict(from_attributes=True)


class NextOfKinResponse(BaseModel):
    id: uuid.UUID
    name: str
    phone: str
    relationship: str
    address: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ── Patient schemas ───────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    gender: Literal["Male", "Female"]
    phone: str = Field(..., pattern=r"^(\+234|0)[789]\d{9}$")
    email: EmailStr | None = None
    blood_group: str | None = None
    nin: str | None = Field(None, pattern=r"^\d{11}$")
    preferred_language: str | None = None
    address_street: str = Field(..., min_length=1, max_length=255)
    address_city: str = Field(..., min_length=1, max_length=100)
    address_state: str = Field(..., min_length=1, max_length=100)
    address_lga: str | None = None
    address_postal_code: str | None = None
    address_landmark: str | None = None
    emergency_contacts: list[EmergencyContactCreate] = Field(
        ..., min_length=1, max_length=3
    )
    next_of_kin: NextOfKinCreate


class PatientUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, pattern=r"^(\+234|0)[789]\d{9}$")
    email: EmailStr | None = None
    blood_group: str | None = None
    preferred_language: str | None = None
    address_street: str | None = Field(None, min_length=1, max_length=255)
    address_city: str | None = Field(None, min_length=1, max_length=100)
    address_state: str | None = Field(None, min_length=1, max_length=100)
    address_lga: str | None = None
    address_postal_code: str | None = None
    address_landmark: str | None = None
    status: Literal["active", "inactive", "deceased"] | None = None


class PatientResponse(BaseModel):
    id: uuid.UUID
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    phone: str
    email: str | None = None
    blood_group: str | None = None
    nin: str | None = None
    preferred_language: str | None = None
    status: str
    address_street: str
    address_city: str
    address_state: str
    address_lga: str | None = None
    address_postal_code: str | None = None
    address_landmark: str | None = None
    created_at: datetime
    emergency_contacts: list[EmergencyContactResponse] = []
    next_of_kin: list[NextOfKinResponse] = []

    model_config = ConfigDict(from_attributes=True)
