import uuid
import enum
from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, Date,
    ForeignKey, Text, Enum as SAEnum, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class ForumCategoryEnum(str, enum.Enum):
    general = "general"
    tips = "tips"
    complaints = "complaints"
    announcements = "announcements"
    slot_swaps = "slot_swaps"
    maintenance = "maintenance"


class ForumPost(Base):
    __tablename__ = "forum_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True)
    category = Column(SAEnum(ForumCategoryEnum), nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    is_anonymous = Column(Boolean, default=False)
    is_pinned = Column(Boolean, default=False)
    upvote_count = Column(Integer, default=0)
    # Slot-swap specific fields (null for other categories)
    swap_from_date = Column(Date, nullable=True)
    swap_to_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class ForumReply(Base):
    __tablename__ = "forum_replies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("forum_posts.id"), nullable=False, index=True)
    parent_reply_id = Column(UUID(as_uuid=True), ForeignKey("forum_replies.id"), nullable=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    body = Column(Text, nullable=False)
    is_anonymous = Column(Boolean, default=False)
    upvote_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ForumUpvote(Base):
    __tablename__ = "forum_upvotes"
    __table_args__ = (
        UniqueConstraint("student_id", "post_id", name="uq_upvote_post"),
        UniqueConstraint("student_id", "reply_id", name="uq_upvote_reply"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    post_id = Column(UUID(as_uuid=True), ForeignKey("forum_posts.id"), nullable=True)
    reply_id = Column(UUID(as_uuid=True), ForeignKey("forum_replies.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())