from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.schemas.lost_found import LostFoundCreateRequest, LostFoundResponse, LostFoundMatchResponse
from app.schemas.auth import UserRole
from app.services import lost_found_service
from app.utils.dependencies import get_current_user, require_admin
from app.utils.exceptions import ForbiddenError

router = APIRouter()


@router.post("", response_model=LostFoundResponse, status_code=201)
def create_post(
    payload: LostFoundCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a lost or found post.
    The Jaccard match engine runs automatically on creation.
    """
    if current_user._jwt_role != UserRole.student:
        raise ForbiddenError("Students only")
    return lost_found_service.create_post(
        db=db,
        student_id=current_user.id,
        post_type=payload.post_type,
        item_description=payload.item_description,
        color=payload.color,
        photo_url=payload.photo_url,
        last_seen_location=payload.last_seen_location,
    )


@router.get("", response_model=List[LostFoundResponse])
def list_posts(
    post_type: Optional[str] = Query(None, description="lost | found"),
    resolved: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return lost_found_service.list_posts(db, post_type=post_type, resolved=resolved, page=page, page_size=page_size)


@router.get("/{post_id}", response_model=LostFoundResponse)
def get_post(
    post_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return lost_found_service.get_post(db, post_id)


@router.post("/{post_id}/resolve", response_model=LostFoundResponse)
def resolve_post(
    post_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a post as resolved (original poster only)."""
    if current_user._jwt_role != UserRole.student:
        raise ForbiddenError("Students only")
    return lost_found_service.resolve_post(db, post_id, current_user.id)


@router.get("/{post_id}/matches", response_model=List[LostFoundMatchResponse])
def get_matches(
    post_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all keyword-matched counterpart posts for a given lost/found post."""
    return lost_found_service.list_matches(db, post_id)


@router.post("/admin/rescan")
def admin_rescan(
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: re-run the full Jaccard match scan across all unresolved posts."""
    new_matches = lost_found_service.run_full_match_scan(db)
    return {"new_matches_created": new_matches}
