import uuid
import enum
from sqlalchemy import Column, String, Boolean, Float, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class PostTypeEnum(str, enum.Enum):
    lost = "lost"
    found = "found"


class LostFoundPost(Base):
    __tablename__ = "lost_found_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    posted_by = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True)
    post_type = Column(SAEnum(PostTypeEnum), nullable=False)
    item_description = Column(Text, nullable=False)
    color = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    last_seen_location = Column(String, nullable=True)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LostFoundMatch(Base):
    __tablename__ = "lost_found_matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    lost_post_id = Column(UUID(as_uuid=True), ForeignKey("lost_found_posts.id"), nullable=False)
    found_post_id = Column(UUID(as_uuid=True), ForeignKey("lost_found_posts.id"), nullable=False)
    match_score = Column(Float, nullable=False)
    notified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())