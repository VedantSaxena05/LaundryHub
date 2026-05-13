from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class BagResponse(BaseModel):
    id: UUID
    student_id: UUID
    rfid_tag_id: Optional[UUID] = None
    status: str
    slot_id: Optional[UUID] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class BagStatusLogResponse(BaseModel):
    id: UUID
    bag_id: UUID
    from_status: Optional[str] = None
    to_status: str
    changed_by_staff: Optional[UUID] = None
    scan_event_id: Optional[UUID] = None
    # Populated only for the awaiting_id_scan → collected transition
    pickup_scanned_by_student: Optional[UUID] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


# Human-readable labels for each bag status
BAG_STATUS_LABELS = {
    "pending":          "Waiting for drop-off",
    "dropped":          "Received at laundry",
    "washing":          "Being washed",
    "ready":            "Ready for collection",
    "awaiting_id_scan": "Bag scanned — tap college ID card to collect",
    "collected":        "Collected",
    "missed":           "Missed / expired",
}

# Which scan_type advances from each status — used by UI for hints
NEXT_SCAN_FOR_STATUS = {
    "pending":          "dropoff",
    "dropped":          "ready",
    "ready":            "pickup_bag",
    "awaiting_id_scan": "pickup_id",
}
