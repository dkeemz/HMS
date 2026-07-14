from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

# ── Role schemas ─────────────────────────────────────────────────────────


class RoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(None, max_length=255)
    permission_ids: list[uuid.UUID] = []


class RoleResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    is_system: bool = False
    permission_count: int = 0
    created_at: datetime | None = None


class RoleListResponse(BaseModel):
    roles: list[RoleResponse]


# ── Permission schemas ───────────────────────────────────────────────────


class PermissionResponse(BaseModel):
    id: str
    resource: str
    action: str
    description: str | None = None


class PermissionListResponse(BaseModel):
    permissions: list[PermissionResponse]


# ── UserRole schemas ─────────────────────────────────────────────────────


class UserRoleAssign(BaseModel):
    role_id: uuid.UUID


class UserRoleResponse(BaseModel):
    id: str
    user_id: str
    role_id: str
    role_name: str = ""
    status: str = "approved"
    assigned_by: str | None = None
    assigned_at: datetime | None = None
    expires_at: datetime | None = None


# ── Permission override schemas ──────────────────────────────────────────


class PermissionOverrideRequest(BaseModel):
    permission_id: uuid.UUID


class PermissionOverrideResponse(BaseModel):
    id: str
    user_id: str
    permission_id: str
    granted: bool
    granted_by: str
    created_at: datetime | None = None


# ── Temporary elevation schemas ──────────────────────────────────────────


class TemporaryElevationRequest(BaseModel):
    role_id: uuid.UUID
    duration_hours: int = Field(..., ge=1, le=72)


class TemporaryElevationResponse(BaseModel):
    id: str
    user_id: str
    role_id: str
    expires_at: datetime
    elevated_by: str
    created_at: datetime | None = None


# ── Approval schemas ─────────────────────────────────────────────────────


class ApprovalDecision(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$")


class ApprovalResponse(BaseModel):
    id: str
    user_role_id: str
    status: str
    requested_by: str
    approved_by: str | None = None
    created_at: datetime | None = None
    resolved_at: datetime | None = None


# ── Effective permission schemas ─────────────────────────────────────────


class EffectivePermission(BaseModel):
    resource: str
    action: str
    permission_id: str
    source: str


class EffectivePermissionsResponse(BaseModel):
    user_id: str
    permissions: list[EffectivePermission]


# ── Audit schemas ────────────────────────────────────────────────────────


class AuditLogEntry(BaseModel):
    id: str
    user_id: str | None = None
    action: str
    resource: str
    resource_id: str | None = None
    extra_data: dict | None = None
    timestamp: datetime | None = None


class AuditLogResponse(BaseModel):
    entries: list[AuditLogEntry]


# ── Permission matrix ────────────────────────────────────────────────────


class PermissionMatrixRole(BaseModel):
    role_id: str
    role_name: str
    permission_ids: list[str]


class PermissionMatrixResponse(BaseModel):
    permissions: list[PermissionResponse]
    roles: list[PermissionMatrixRole]
