from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    session_id: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    status: str
    roles: list[str] = []
    last_login_at: datetime | None = None


class LogoutRequest(BaseModel):
    refresh_token: str


class MFAChallengeResponse(BaseModel):
    session_id: str
    mfa_required: bool
    mfa_methods: list[str] = []
