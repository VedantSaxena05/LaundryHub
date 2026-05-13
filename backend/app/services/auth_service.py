from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import Student, Staff
from app.schemas.auth import TokenPayload, UserRole
from app.utils.exceptions import UnauthorizedError


# ── Password helpers (direct bcrypt, no passlib) ──────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── Token creation ────────────────────────────────────────────────────────

def _make_token(subject: str, role: UserRole, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": subject, "role": role.value, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: UUID, role: UserRole) -> str:
    return _make_token(
        str(user_id),
        role,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: UUID, role: UserRole) -> str:
    return _make_token(
        str(user_id),
        role,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


# ── Token decoding ────────────────────────────────────────────────────────

def decode_token(token: str) -> TokenPayload:
    try:
        raw = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return TokenPayload(sub=raw["sub"], role=raw["role"], exp=raw.get("exp"))
    except JWTError:
        raise UnauthorizedError("Invalid or expired token")


# ── DB lookups ────────────────────────────────────────────────────────────

def get_student_by_email(db: Session, email: str) -> Optional[Student]:
    return db.query(Student).filter(Student.email == email).first()


def get_student_by_id(db: Session, student_id: UUID) -> Optional[Student]:
    return db.query(Student).filter(Student.id == student_id).first()


def get_staff_by_employee_id(db: Session, employee_id: str) -> Optional[Staff]:
    return db.query(Staff).filter(Staff.employee_id == employee_id).first()


def get_staff_by_id(db: Session, staff_id: UUID) -> Optional[Staff]:
    return db.query(Staff).filter(Staff.id == staff_id).first()


# ── Authenticate (login) ──────────────────────────────────────────────────

def authenticate_student(db: Session, email: str, password: str) -> Student:
    student = get_student_by_email(db, email)
    if not student or not verify_password(password, student.password_hash):
        raise UnauthorizedError("Invalid credentials")
    if not student.is_active:
        raise UnauthorizedError("Account is deactivated")
    return student


def authenticate_staff(db: Session, employee_id: str, password: str) -> Staff:
    staff = get_staff_by_employee_id(db, employee_id)
    if not staff or not verify_password(password, staff.password_hash):
        raise UnauthorizedError("Invalid credentials")
    if not staff.is_active:
        raise UnauthorizedError("Account is deactivated")
    return staff