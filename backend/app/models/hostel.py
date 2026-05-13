import uuid
from sqlalchemy import Column, String, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class BlockedDate(Base):
    __tablename__ = "blocked_dates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, nullable=False, unique=True, index=True)
    reason = Column(String, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True)