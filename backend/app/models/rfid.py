import uuid
import enum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.database import Base


class DeviceLocationEnum(str, enum.Enum):
    dropoff = "dropoff"
    shelf = "shelf"
    pickup = "pickup"           # NEW: reader at the bag-pickup counter


class ScanTypeEnum(str, enum.Enum):
    dropoff = "dropoff"         # bag tag scanned at drop-off
    ready = "ready"             # bag tag scanned when washed & shelved
    pickup_bag = "pickup_bag"   # NEW step-1: bag tag scanned at pickup counter
    pickup_id = "pickup_id"     # NEW step-2: student ID card scanned to confirm


class TagTypeEnum(str, enum.Enum):
    bag = "bag"           # RFID sticker attached to laundry bag
    id_card = "id_card"   # RFID chip inside student college ID card


class RFIDTag(Base):
    __tablename__ = "rfid_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tag_uid = Column(String, unique=True, nullable=False, index=True)
    # "bag" or "id_card" — set at enrollment time
    tag_type = Column(SAEnum(TagTypeEnum), nullable=False, default=TagTypeEnum.bag)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=True)
    linked_by = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True)
    linked_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RFIDDevice(Base):
    __tablename__ = "rfid_devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_name = Column(String, nullable=False)
    location_tag = Column(SAEnum(DeviceLocationEnum), nullable=False)
    configured_by = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=True)
    last_seen_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RFIDScanEvent(Base):
    """Append-only audit log. Every scan is written here regardless of outcome."""
    __tablename__ = "rfid_scan_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tag_uid = Column(String, nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey("rfid_devices.id"), nullable=False)
    scanned_by_staff = Column(UUID(as_uuid=True), ForeignKey("staff.id"), nullable=False)
    scan_type = Column(SAEnum(ScanTypeEnum), nullable=False)
    bag_id = Column(UUID(as_uuid=True), ForeignKey("laundry_bags.id"), nullable=True)
    # NEW: for pickup_id scans — which student tapped their ID card.
    # Any student's linked ID card is accepted; this is a log-only field.
    pickup_scanned_by_student_id = Column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=True
    )
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
