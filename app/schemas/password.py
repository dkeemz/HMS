from __future__ import annotations

from pydantic import BaseModel, Field


class PasswordValidateRequest(BaseModel):
    password: str = Field(..., min_length=1, description="Password to validate")


class PasswordValidateResponse(BaseModel):
    valid: bool
    message: str
    errors: list[str] = []


class PasswordResetRequest(BaseModel):
    email: str = Field(..., description="Email address for password reset")


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., min_length=1, description="Reset token from email")
    new_password: str = Field(..., min_length=1, description="New password")


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=1, description="New password")


class PasswordChangeResponse(BaseModel):
    message: str


class PasswordResetResponse(BaseModel):
    message: str
