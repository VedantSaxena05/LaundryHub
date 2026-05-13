from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime


class StudentResponse(BaseModel):
    id: UUID
    registration_number: str
    name: str
    email: EmailStr
    phone_number: str
    block: str
    floor: int
    room_number: str
    language_preference: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class StudentUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    block: Optional[str] = None
    floor: Optional[int] = None
    room_number: Optional[str] = None
    language_preference: Optional[str] = None
    # Android / iOS Capacitor FCM registration token.
    # The mobile app sends this after login and on token rotation.
    fcm_token: Optional[str] = None

    @field_validator("language_preference")
    @classmethod
    def validate_language(cls, v):
        if v is not None and v not in ("en", "ta"):
            raise ValueError("language_preference must be 'en' or 'ta'")
        return v


class StaffResponse(BaseModel):
    id: UUID
    name: str
    employee_id: str
    phone_number: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
