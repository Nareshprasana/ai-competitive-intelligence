"""Transport schemas for authentication and organization administration."""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.security.auth import Role

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_email(value: str) -> str:
    normalized = value.lower()
    if not _EMAIL_PATTERN.fullmatch(normalized):
        raise ValueError("A valid email address is required.")
    return normalized


class Credentials(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)


class InvitationAcceptance(Credentials):
    token: str = Field(min_length=32, max_length=128)
    password: str = Field(min_length=12, max_length=256)


class ExistingUserInvitationAcceptance(BaseModel):
    token: str = Field(min_length=32, max_length=128)


class InvitationRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(min_length=3, max_length=320)
    role: Role

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)


class OrganizationRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    organization_id: str = Field(min_length=2, max_length=128, pattern=r"^[a-zA-Z0-9_-]+$")
    name: str = Field(min_length=1, max_length=255)
    owner_email: str = Field(min_length=3, max_length=320)

    @field_validator("owner_email")
    @classmethod
    def normalize_owner_email(cls, value: str) -> str:
        return _normalize_email(value)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    csrf_token: str


class InvitationResponse(BaseModel):
    organization_id: str
    email: str
    role: Role
    token: str
    expires_at: str


class OrganizationCreatedResponse(BaseModel):
    organization_id: str
    name: str
    owner_invitation: InvitationResponse


__all__ = [
    "Credentials",
    "ExistingUserInvitationAcceptance",
    "InvitationAcceptance",
    "InvitationRequest",
    "InvitationResponse",
    "OrganizationRequest",
    "OrganizationCreatedResponse",
    "TokenResponse",
]
