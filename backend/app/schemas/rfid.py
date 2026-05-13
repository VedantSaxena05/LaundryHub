from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class RFIDScanRequest(BaseModel):
    """
    Payload the ESP32 POSTs to /rfid/scan on every card swipe.

    For pickup_id scans the device MUST include the bag_id it received
    from the preceding pickup_bag scan response. This ties the ID card
    confirmation to the specific bag that was just scanned.
    """
    tag_uid: str
    device_id: UUID
    scan_type: str      # dropoff | ready | pickup_bag | pickup_id
    # Required only when scan_type == "pickup_id"
    bag_id: Optional[UUID] = None


class RFIDLinkRequest(BaseModel):
    """Staff scans a bag tag and links it to a student."""
    tag_uid: str
    student_id: UUID


class IDCardLinkRequest(BaseModel):
    """
    Staff scans a student's college ID card and links its RFID UID to the student.
    A student may have at most one active ID card tag at a time.
    """
    tag_uid: str
    student_id: UUID


class RFIDTagResponse(BaseModel):
    id: UUID
    tag_uid: str
    tag_type: str           # "bag" | "id_card"
    student_id: Optional[UUID] = None
    linked_by: Optional[UUID] = None
    linked_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RFIDScanEventResponse(BaseModel):
    id: UUID
    tag_uid: str
    device_id: UUID
    scanned_by_staff: UUID
    scan_type: str
    bag_id: Optional[UUID] = None
    pickup_scanned_by_student_id: Optional[UUID] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class DeviceRegisterRequest(BaseModel):
    device_name: str
    location_tag: str   # dropoff | shelf | pickup


class DeviceResponse(BaseModel):
    id: UUID
    device_name: str
    location_tag: str
    configured_by: Optional[UUID] = None
    last_seen_at: datetime
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
