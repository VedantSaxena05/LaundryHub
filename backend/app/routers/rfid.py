from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from app.database import get_db
from app.schemas.rfid import (
    RFIDScanRequest, RFIDScanEventResponse,
    RFIDLinkRequest, IDCardLinkRequest, RFIDTagResponse,
)
from app.services import bag_service, rfid_service
from app.utils.dependencies import require_staff, require_admin

router = APIRouter()


# ── Enriched scan response ────────────────────────────────────────────────

class ScanResponse(BaseModel):
    scan_event_id: UUID
    tag_uid: str
    device_id: UUID
    scan_type: str
    timestamp: datetime
    result: str     # see result codes below
    message: str
    student_name: Optional[str] = None
    student_id: Optional[UUID] = None
    bag_id: Optional[UUID] = None
    bag_status: Optional[str] = None
    # Populated on pickup_id scans — who tapped their ID card
    pickup_tapped_by_student_id: Optional[UUID] = None
    pickup_tapped_by_student_name: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Scan endpoint (ESP32 → backend) ──────────────────────────────────────

@router.post("/scan", response_model=ScanResponse)
def scan_tag(
    payload: RFIDScanRequest,
    current_user=Depends(require_staff),
    db: Session = Depends(get_db),
):
    """
    Called by the ESP32 on every card swipe.

    scan_type values:
      dropoff    — Student's bag tag scanned at drop-off counter (10:00–14:00)
      ready      — Bag tag scanned by staff when washed & placed on shelf
      pickup_bag — Bag tag scanned at pickup counter (14:00–18:00); Step 1 of 2
      pickup_id  — Student's ID card scanned at pickup counter; Step 2 of 2
                   MUST include bag_id from the pickup_bag response

    Always returns HTTP 200. Check `result` field for outcome:
      success              — transition applied
      wrong_state          — bag in wrong state for this scan_type
      unknown_tag          — bag tag UID not enrolled
      unknown_id_card      — ID card UID not enrolled
      id_card_not_linked   — ID card not linked to a student
      no_active_bag        — no active bag found for student
      no_slot_booked       — student has no slot booked for today
      missing_bag_id       — bag_id not supplied for pickup_id scan
      bag_not_found        — bag_id not found in DB
      student_not_found    — tag linked to deleted student account
    """
    return bag_service.process_scan(
        db=db,
        tag_uid=payload.tag_uid,
        device_id=payload.device_id,
        scan_type=payload.scan_type,
        staff_id=current_user.id,
        bag_id=payload.bag_id,
    )


# ── Tag enrollment ────────────────────────────────────────────────────────

@router.post("/link-bag-tag", response_model=RFIDTagResponse, status_code=201)
def link_bag_tag(
    payload: RFIDLinkRequest,
    current_user=Depends(require_staff),
    db: Session = Depends(get_db),
):
    """
    Enroll a bag RFID tag and link it to a student.
    Done once per student when their bag tag is issued.
    Raises 400 if the tag is already linked to a different student.
    """
    return bag_service.link_bag_tag_to_student(
        db=db,
        tag_uid=payload.tag_uid,
        student_id=payload.student_id,
        staff_id=current_user.id,
    )


@router.post("/link-id-card", response_model=RFIDTagResponse, status_code=201)
def link_id_card(
    payload: IDCardLinkRequest,
    current_user=Depends(require_staff),
    db: Session = Depends(get_db),
):
    """
    Enroll a student's college ID card RFID UID and link it to their account.
    Done once per student at registration/enrollment time.

    One active ID card per student is enforced. If the student already
    has a different ID card linked, the old one is deactivated automatically.

    The ID card is used only at the pickup counter (pickup_id scan) to
    confirm who collected the bag. Any student's enrolled ID card is accepted
    — it does not have to be the bag owner.
    """
    return bag_service.link_id_card_to_student(
        db=db,
        tag_uid=payload.tag_uid,
        student_id=payload.student_id,
        staff_id=current_user.id,
    )


# ── Kept for backward compatibility ──────────────────────────────────────

@router.post("/link", response_model=RFIDTagResponse, status_code=201)
def link_tag(
    payload: RFIDLinkRequest,
    current_user=Depends(require_staff),
    db: Session = Depends(get_db),
):
    """
    Legacy endpoint — links a bag tag. Prefer /link-bag-tag for new integrations.
    """
    return bag_service.link_tag_to_student(
        db=db,
        tag_uid=payload.tag_uid,
        student_id=payload.student_id,
        staff_id=current_user.id,
    )


@router.post("/unlink/{tag_uid}", response_model=RFIDTagResponse)
def unlink_tag(
    tag_uid: str,
    current_user=Depends(require_staff),
    db: Session = Depends(get_db),
):
    """
    Deactivate a tag and remove its student association.
    Works for both bag tags and ID card tags.
    """
    return bag_service.unlink_tag(db=db, tag_uid=tag_uid, staff_id=current_user.id)


@router.get("/tags", response_model=List[RFIDTagResponse])
def list_tags(
    current_user=Depends(require_staff),
    db: Session = Depends(get_db),
):
    """List all registered RFID tags (both bag tags and ID card tags)."""
    return rfid_service.list_tags(db)


@router.get("/tags/{tag_uid}", response_model=RFIDTagResponse)
def get_tag(
    tag_uid: str,
    current_user=Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Look up any tag by its UID string."""
    return rfid_service.get_tag_by_uid(db, tag_uid)


@router.delete("/tags/{tag_uid}", status_code=204)
def deactivate_tag(
    tag_uid: str,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: soft-delete an RFID tag."""
    rfid_service.deactivate_tag(db, tag_uid)


@router.get("/scan-log", response_model=List[RFIDScanEventResponse])
def scan_log(
    limit: int = 100,
    current_user=Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Return the most recent scan audit log entries."""
    return rfid_service.list_scan_events(db, limit=limit)
