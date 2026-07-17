from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    code: str = Field(..., min_length=1, max_length=20)
    description: str | None = None
    parent_id: uuid.UUID | None = None
    head_id: uuid.UUID | None = None
    display_order: int = 0


class DepartmentUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    code: str | None = Field(None, min_length=1, max_length=20)
    description: str | None = None
    parent_id: uuid.UUID | None = None
    head_id: uuid.UUID | None = None
    display_order: int | None = None
    is_active: bool | None = None


class DepartmentResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    description: str | None = None
    parent_id: uuid.UUID | None = None
    head_id: uuid.UUID | None = None
    display_order: int
    is_active: bool
    children_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DepartmentTreeResponse(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    description: str | None = None
    parent_id: uuid.UUID | None = None
    head_id: uuid.UUID | None = None
    display_order: int
    is_active: bool
    children: list[DepartmentTreeResponse] = []

    model_config = ConfigDict(from_attributes=True)
