from pydantic import BaseModel, computed_field
from uuid import UUID
from datetime import datetime
from typing import Optional


class LostFoundCreateRequest(BaseModel):
    post_type: str              # lost | found
    item_description: str
    color: Optional[str] = None
    photo_url: Optional[str] = None
    last_seen_location: Optional[str] = None


class LostFoundResponse(BaseModel):
    id: UUID
    posted_by: UUID
    post_type: str
    item_description: str
    color: Optional[str] = None
    photo_url: Optional[str] = None
    last_seen_location: Optional[str] = None
    is_resolved: bool
    created_at: datetime

    @computed_field
    @property
    def resolved(self) -> bool:
        return self.is_resolved

    model_config = {"from_attributes": True}


class LostFoundMatchResponse(BaseModel):
    id: UUID
    lost_post_id: UUID
    found_post_id: UUID
    match_score: float
    notified: bool
    created_at: datetime

    model_config = {"from_attributes": True}