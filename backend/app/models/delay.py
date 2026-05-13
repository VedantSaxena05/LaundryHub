import uuid
import enum
from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class DelayReasonEnum(str, enum.Enum):
    power_cut = "power_cut"
    water_shortage = "water_shortage"
    machine_repair = "machine_repair"
    too_many_clothes = "too_many_clothes"
    staff_shortage = "staff_shortage"


class DelayReport(Base):
    __tablename__ = "delay_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reported_by = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=False)
    reason = Column(SAEnum(DelayReasonEnum), nullable=False)
    affected_date = Column(Date, nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    notification_sent = Column(Boolean, default=False)