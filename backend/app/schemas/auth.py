from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    student = "student"
    staff = "staff"
    admin = "admin"


# ── Registration ──────────────────────────────────────────────────────────

class StudentRegisterRequest(BaseModel):
    registration_number: str
    name: str
    email: EmailStr
    phone_number: str
    password: str
    block: str
    floor: int
    room_number: str
    language_preference: str = "en"

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v):
        if not v.isdigit() or len(v) != 10:
            raise ValueError("phone_number must be exactly 10 digits")
        return v

    @field_validator("language_preference")
    @classmethod
    def validate_lang(cls, v):
        if v not in ("en", "ta"):
            raise ValueError("language_preference must be 'en' or 'ta'")
        return v


class StaffRegisterRequest(BaseModel):
    name: str
    employee_id: str
    phone_number: str
    password: str
    role: str = "staff"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v not in ("staff", "admin"):
            raise ValueError("role must be 'staff' or 'admin'")
        return v


# ── Login ─────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Works for both students (email) and staff (employee_id)."""
    identifier: str      # email for students, employee_id for staff
    password: str
    role: UserRole       # client declares which role it is logging in as


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: UserRole


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str             # user UUID as string
    role: UserRole
    exp: Optional[int] = None