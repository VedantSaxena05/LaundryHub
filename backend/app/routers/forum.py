from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.schemas.forum import (
    ForumPostCreateRequest, ForumPostUpdateRequest, ForumPostResponse,
    ForumReplyCreateRequest, ForumReplyResponse,
)
from app.schemas.auth import UserRole
from app.services import forum_service
from app.utils.dependencies import get_current_user, require_admin
from app.utils.exceptions import ForbiddenError

router = APIRouter()


# ── Posts ─────────────────────────────────────────────────────────────────

@router.post("", response_model=ForumPostResponse, status_code=201)
def create_post(
    payload: ForumPostCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user._jwt_role != UserRole.student:
        raise ForbiddenError("Students only")
    return forum_service.create_post(
        db=db,
        author_id=current_user.id,
        category=payload.category,
        title=payload.title,
        body=payload.body,
        is_anonymous=payload.is_anonymous,
        swap_from_date=payload.swap_from_date,
        swap_to_date=payload.swap_to_date,
    )


@router.get("", response_model=List[ForumPostResponse])
def list_posts(
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return forum_service.list_posts(db, category=category, page=page, page_size=page_size)


@router.get("/{post_id}", response_model=ForumPostResponse)
def get_post(
    post_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return forum_service.get_post(db, post_id)


@router.patch("/{post_id}", response_model=ForumPostResponse)
def update_post(
    post_id: UUID,
    payload: ForumPostUpdateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user._jwt_role != UserRole.student:
        raise ForbiddenError("Students only")
    return forum_service.update_post(db, post_id, current_user.id, payload.title, payload.body)


@router.delete("/{post_id}", status_code=204)
def delete_post(
    post_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_admin = current_user._jwt_role == UserRole.admin
    author_id = current_user.id if not is_admin else None
    forum_service.delete_post(db, post_id, author_id, is_admin=is_admin)


@router.post("/{post_id}/pin", response_model=ForumPostResponse)
def toggle_pin(
    post_id: UUID,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: toggle pinned status on a post."""
    return forum_service.pin_post(db, post_id)


@router.post("/{post_id}/upvote")
def upvote_post(
    post_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user._jwt_role != UserRole.student:
        raise ForbiddenError("Students only")
    return forum_service.upvote_post(db, current_user.id, post_id)


# ── Replies ───────────────────────────────────────────────────────────────

@router.post("/{post_id}/replies", response_model=ForumReplyResponse, status_code=201)
def create_reply(
    post_id: UUID,
    payload: ForumReplyCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user._jwt_role != UserRole.student:
        raise ForbiddenError("Students only")
    return forum_service.create_reply(
        db=db,
        post_id=post_id,
        author_id=current_user.id,
        body=payload.body,
        is_anonymous=payload.is_anonymous,
        parent_reply_id=payload.parent_reply_id,
    )


@router.get("/{post_id}/replies", response_model=List[ForumReplyResponse])
def list_replies(
    post_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return forum_service.list_replies(db, post_id)


@router.post("/replies/{reply_id}/upvote")
def upvote_reply(
    reply_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user._jwt_role != UserRole.student:
        raise ForbiddenError("Students only")
    return forum_service.upvote_reply(db, current_user.id, reply_id)
