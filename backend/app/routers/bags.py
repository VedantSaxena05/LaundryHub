from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.schemas.bag import BagResponse, BagStatusLogResponse
from app.schemas.auth import UserRole
from app.services import bag_service
from app.utils.dependencies import get_current_user, require_staff
from app.utils.exceptions import ForbiddenError

router = APIRouter()


@router.get("/my", response_model=BagResponse)
def my_current_bag(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Student: get their active (non-collected) bag status."""
    if current_user._jwt_role != UserRole.student:
        raise ForbiddenError("Students only")
    bag = bag_service.get_bag_status(db, current_user.id)
    if not bag:
        from app.utils.exceptions import NotFoundError
        raise NotFoundError("No active bag found")
    return bag


@router.get("/my/history", response_model=List[BagResponse])
def my_bag_history(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Student: get full history of all their bags."""
    if current_user._jwt_role != UserRole.student:
        raise ForbiddenError("Students only")
    return bag_service.get_bag_history(db, current_user.id)


@router.get("/{bag_id}/logs", response_model=List[BagStatusLogResponse])
def bag_logs(
    bag_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the state-transition audit log for a specific bag.
    Students can only view their own bags; staff/admin can view any.
    """
    # Staff can see all; students need ownership check
    if current_user._jwt_role == UserRole.student:
        history = bag_service.get_bag_history(db, current_user.id)
        bag_ids = {b.id for b in history}
        if bag_id not in bag_ids:
            raise ForbiddenError("Access denied to this bag")
    return bag_service.get_status_logs(db, bag_id)


@router.get("/student/{student_id}", response_model=List[BagResponse])
def student_bags(
    student_id: UUID,
    current_user=Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Staff/admin: view all bags for a given student."""
    return bag_service.get_bag_history(db, student_id)
