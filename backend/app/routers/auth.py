from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.user import Student, Staff
from app.schemas.auth import (
    StudentRegisterRequest, StaffRegisterRequest,
    LoginRequest, TokenResponse, RefreshRequest, UserRole,
)
from app.services.auth_service import (
    hash_password, create_access_token, create_refresh_token,
    authenticate_student, authenticate_staff,
    decode_token, get_student_by_id, get_staff_by_id,
)
from app.utils.exceptions import ConflictError, UnauthorizedError

router = APIRouter()


@router.post("/register/student", response_model=TokenResponse, status_code=201)
def register_student(payload: StudentRegisterRequest, db: Session = Depends(get_db)):
    if db.query(Student).filter(Student.email == payload.email).first():
        raise ConflictError("Email already registered")
    if db.query(Student).filter(Student.registration_number == payload.registration_number).first():
        raise ConflictError("Registration number already exists")

    student = Student(
        registration_number=payload.registration_number,
        name=payload.name,
        email=payload.email,
        phone_number=payload.phone_number,
        password_hash=hash_password(payload.password),
        block=payload.block,
        floor=payload.floor,
        room_number=payload.room_number,
        language_preference=payload.language_preference,
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    return TokenResponse(
        access_token=create_access_token(student.id, UserRole.student),
        refresh_token=create_refresh_token(student.id, UserRole.student),
        role=UserRole.student,
    )


@router.post("/register/staff", response_model=TokenResponse, status_code=201)
def register_staff(payload: StaffRegisterRequest, db: Session = Depends(get_db)):
    if db.query(Staff).filter(Staff.employee_id == payload.employee_id).first():
        raise ConflictError("Employee ID already registered")

    staff = Staff(
        name=payload.name,
        employee_id=payload.employee_id,
        phone_number=payload.phone_number,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)

    role = UserRole.admin if payload.role == "admin" else UserRole.staff
    return TokenResponse(
        access_token=create_access_token(staff.id, role),
        refresh_token=create_refresh_token(staff.id, role),
        role=role,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    if payload.role == UserRole.student:
        user = authenticate_student(db, payload.identifier, payload.password)
        role = UserRole.student
    else:
        user = authenticate_staff(db, payload.identifier, payload.password)
        role = UserRole.admin if user.role == "admin" else UserRole.staff

    return TokenResponse(
        access_token=create_access_token(user.id, role),
        refresh_token=create_refresh_token(user.id, role),
        role=role,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    token_data = decode_token(payload.refresh_token)
    user_id = UUID(token_data.sub)
    role = token_data.role

    if role == UserRole.student:
        user = get_student_by_id(db, user_id)
    else:
        user = get_staff_by_id(db, user_id)

    if not user or not user.is_active:
        raise UnauthorizedError("User not found or deactivated")

    return TokenResponse(
        access_token=create_access_token(user.id, role),
        refresh_token=create_refresh_token(user.id, role),
        role=role,
    )