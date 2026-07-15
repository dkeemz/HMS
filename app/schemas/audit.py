from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AuditLogEntry(BaseModel):
    id: str
    user_id: str | None = None
    action: str
    resource: str
    resource_id: str | None = None
    patient_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    timestamp: datetime | None = None
    metadata: dict | None = None
    previous_hash: str | None = None
    hash: str | None = None


class AuditLogSearchResponse(BaseModel):
    entries: list[AuditLogEntry]
    total: int
    page: int
    page_size: int


class AuditLogListResponse(BaseModel):
    entries: list[AuditLogEntry]
    total: int


class AuditLogExportResponse(BaseModel):
    content: str
    format: str


class AuditVerifyRequest(BaseModel):
    start_date: datetime
    end_date: datetime


class AuditVerifyResponse(BaseModel):
    is_valid: bool
    broken_entry_ids: list[str]
    checked_start: datetime
    checked_end: datetime
    verified_by: str


class SecurityAlert(BaseModel):
    type: str
    severity: str
    user_id: str | None = None
    count: int
    message: str
    detected_at: datetime


class SecurityAlertsResponse(BaseModel):
    alerts: list[SecurityAlert]
    checked_at: str
