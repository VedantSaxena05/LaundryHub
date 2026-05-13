import uuid
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
import enum


class LanguageEnum(str, enum.Enum):
    en = "en"
    ta = "ta"


class StaffRoleEnum(str, enum.Enum):
    staff = "staff"
    admin = "admin"


class Student(Base):
    __tablename__ = "students"

    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    registration_number  = Column(String, unique=True, nullable=False, index=True)
    name                 = Column(String, nullable=False)
    email                = Column(String, unique=True, nullable=False, index=True)
    phone_number         = Column(String, nullable=False)
    password_hash        = Column(String, nullable=False)
    block                = Column(String, nullable=False)
    floor                = Column(Integer, nullable=False)
    room_number          = Column(String, nullable=False)
    language_preference  = Column(SAEnum(LanguageEnum), nullable=False, default=LanguageEnum.en)
    # Android / iOS Capacitor FCM registration token.
    # Updated by the app on login and on FCM token rotation.
    fcm_token            = Column(String, nullable=True)
    is_active            = Column(Boolean, default=True)
    created_at           = Column(DateTime(timezone=True), server_default=func.now())


class Staff(Base):
    __tablename__ = "staff"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name          = Column(String, nullable=False)
    employee_id   = Column(String, unique=True, nullable=False, index=True)
    phone_number  = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role          = Column(SAEnum(StaffRoleEnum), nullable=False, default=StaffRoleEnum.staff)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
