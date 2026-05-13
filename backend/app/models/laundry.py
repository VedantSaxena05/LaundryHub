import uuid
import enum
from sqlalchemy import (
    Column, Integer, DateTime, Date, ForeignKey,
    Enum as SAEnum, UniqueConstraint, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class BagStatusEnum(str, enum.Enum):
    pending = "pending"
    dropped = "dropped"
    washing = "washing"
    ready = "ready"
    # NEW: bag tag scanned at pickup counter; waiting for student ID card tap
    awaiting_id_scan = "awaiting_id_scan"
    collected = "collected"
    missed = "missed"


class SlotStatusEnum(str, enum.Enum):
    booked = "booked"
    used = "used"
    cancelled = "cancelled"
    missed = "missed"


class Slot(Base):
    __tablename__ = "slots"
    __table_args__ = (
        UniqueConstraint("student_id", "date", name="uq_student_date"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    status = Column(SAEnum(SlotStatusEnum), nullable=False, default=SlotStatusEnum.booked)
    month_index = Column(Integer, nullable=False)
    submission_window_minutes = Column(Integer, nullable=True)
    submission_window_start = Column(DateTime(timezone=True), nullable=True)
    submission_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    cancelled_at = Column(DateTime(timezone=True), nullable=True)


class LaundryBag(Base):
    __tablename__ = "laundry_bags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True)
    rfid_tag_id = Column(UUID(as_uuid=True), ForeignKey("rfid_tags.id"), nullable=True)
    status = Column(SAEnum(BagStatusEnum), nullable=False, default=BagStatusEnum.pending)
    slot_id = Column(UUID(as_uuid=True), ForeignKey("slots.id"), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class BagStatusLog(Base):
    __tablename__ = "bag_status_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bag_id = Column(UUID(as_uuid=True), ForeignKey("laundry_bags.id"), nullable=False, index=True)
    from_status = Column(SAEnum(BagStatusEnum), nullable=True)
    to_status = Column(SAEnum(BagStatusEnum), nullable=False)
    changed_by_staff = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True)
    scan_event_id = Column(UUID(as_uuid=True), ForeignKey("rfid_scan_events.id"), nullable=True)
    # NEW: student who tapped their ID card during pickup confirmation.
    # Populated only on the awaiting_id_scan → collected transition.
    # Any student's valid linked ID card is accepted — this is a log-only field.
    pickup_scanned_by_student = Column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=True
    )
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
