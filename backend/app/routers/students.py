from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.schemas.user import StudentResponse, StudentUpdateRequest
from app.schemas.auth import UserRole
from app.models.user import Student
from app.utils.dependencies import get_current_user, require_admin
from app.utils.exceptions import ForbiddenError, NotFoundError

router = APIRouter()


@router.get("/me", response_model=StudentResponse)
def get_me(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the authenticated student's own profile."""
    if current_user._jwt_role != UserRole.student:
        raise ForbiddenError("Students only")
    return current_user


@router.patch("/me", response_model=StudentResponse)
def update_me(
    payload: StudentUpdateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Student updates their own profile (name, room, language, FCM token, etc.)."""
    if current_user._jwt_role != UserRole.student:
        raise ForbiddenError("Students only")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: UUID,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: look up any student by ID."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise NotFoundError("Student not found")
    return student


@router.delete("/{student_id}", status_code=204)
def deactivate_student(
    student_id: UUID,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: soft-delete (deactivate) a student account."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise NotFoundError("Student not found")
    student.is_active = False
    db.commit()
