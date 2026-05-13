import uuid
import enum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base
from app.models.user import LanguageEnum


class NotificationEventEnum(str, enum.Enum):
    bag_received = "bag_received"
    bag_ready = "bag_ready"
    delay = "delay"
    reminder = "reminder"
    uncollected_warning = "uncollected_warning"
    slot_cancelled = "slot_cancelled"
    slot_missed = "slot_missed"


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True)
    event_type = Column(SAEnum(NotificationEventEnum), nullable=False)
    language = Column(SAEnum(LanguageEnum), nullable=False)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    fcm_success = Column(Boolean, nullable=False)