from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from typing import Optional


class ForumPostCreateRequest(BaseModel):
    category: str
    title: str
    body: str
    is_anonymous: bool = False
    # Only for slot_swaps category
    swap_from_date: Optional[date] = None
    swap_to_date: Optional[date] = None


class ForumPostUpdateRequest(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None


class ForumPostResponse(BaseModel):
    id: UUID
    author_id: UUID
    category: str
    title: str
    body: str
    is_anonymous: bool
    is_pinned: bool
    upvote_count: int
    swap_from_date: Optional[date] = None
    swap_to_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ForumReplyCreateRequest(BaseModel):
    body: str
    is_anonymous: bool = False
    parent_reply_id: Optional[UUID] = None


class ForumReplyResponse(BaseModel):
    id: UUID
    post_id: UUID
    parent_reply_id: Optional[UUID] = None
    author_id: UUID
    body: str
    is_anonymous: bool
    upvote_count: int
    created_at: datetime

    model_config = {"from_attributes": True}