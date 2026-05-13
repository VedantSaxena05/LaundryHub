"""
Bag tracking service.

Full state machine (4-scan flow including two-step pickup):

  Enrollment (one-time per student):
    Staff links a bag tag  → tag_type = "bag",     student_id = <id>
    Staff links an ID card → tag_type = "id_card", student_id = <id>

  Operational flow:
    SCAN             TAG SCANNED   FROM STATUS       TO STATUS
    ─────────────    ───────────   ──────────────    ─────────────────
    dropoff          bag tag       pending           dropped
    ready            bag tag       dropped           ready
    pickup_bag       bag tag       ready             awaiting_id_scan
    pickup_id        id_card tag   awaiting_id_scan  collected

  Terminal:
    any → missed  (midnight sweep job, unchanged)

Notes:
  - "dropoff" and "ready" are unchanged from the original 3-scan flow.
  - "pickup_bag" replaces what was previously a single "collected" scan.
    The bag tag is scanned first; the device gets back the bag_id.
  - "pickup_id" requires the device to pass the bag_id it received in
    the pickup_bag response. This guarantees the ID card is confirmed
    against the exact bag that was just picked up — not some random bag.
  - Any student's linked ID card is accepted at pickup_id. The tapper's
    identity is stored in BagStatusLog.pickup_scanned_by_student and
    RFIDScanEvent.pickup_scanned_by_student_id for audit purposes only.
  - Returning 200 always to ESP32 to avoid retry loops.
"""
from datetime import datetime, timezone, date
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.laundry import LaundryBag, BagStatusLog, BagStatusEnum, Slot, SlotStatusEnum
from app.models.rfid import RFIDTag, RFIDScanEvent, ScanTypeEnum, RFIDDevice, TagTypeEnum
from app.models.user import Student
from app.services import notification_service
from app.services.slot_service import assert_dropoff_open, assert_collection_open
from app.utils.exceptions import NotFoundError, BadRequestError


# ── Transitions for bag-tag scans ─────────────────────────────────────────
#  pickup_id is handled separately (different tag type, needs bag_id from device)
BAG_TAG_TRANSITIONS = {
    ScanTypeEnum.dropoff:    (BagStatusEnum.pending, BagStatusEnum.dropped),
    ScanTypeEnum.ready:      (BagStatusEnum.dropped, BagStatusEnum.ready),
    ScanTypeEnum.pickup_bag: (BagStatusEnum.ready,   BagStatusEnum.awaiting_id_scan),
}


def _log_transition(
    db: Session,
    bag: LaundryBag,
    from_status: Optional[BagStatusEnum],
    to_status: BagStatusEnum,
    staff_id: Optional[UUID],
    scan_event_id: Optional[UUID],
    pickup_scanned_by_student: Optional[UUID] = None,
):
    log = BagStatusLog(
        bag_id=bag.id,
        from_status=from_status,
        to_status=to_status,
        changed_by_staff=staff_id,
        scan_event_id=scan_event_id,
        pickup_scanned_by_student=pickup_scanned_by_student,
    )
    db.add(log)


# ── Main scan entry point ─────────────────────────────────────────────────

def process_scan(
    db: Session,
    tag_uid: str,
    device_id: UUID,
    scan_type: str,
    staff_id: UUID,
    bag_id: Optional[UUID] = None,   # required for pickup_id
) -> dict:
    """
    Process a single RFID scan from the ESP32 device.

    Routing:
      scan_type == "pickup_id"  → _process_pickup_id()
      all others                → _process_bag_tag_scan()
    """
    try:
        scan_type_enum = ScanTypeEnum(scan_type)
    except ValueError:
        raise BadRequestError(
            f"Invalid scan_type '{scan_type}'. "
            f"Must be one of: dropoff, ready, pickup_bag, pickup_id"
        )

    # Time-window enforcement
    if scan_type_enum == ScanTypeEnum.dropoff:
        assert_dropoff_open()
    elif scan_type_enum in (ScanTypeEnum.pickup_bag, ScanTypeEnum.pickup_id):
        assert_collection_open()

    # Verify device is active
    device = db.query(RFIDDevice).filter(
        RFIDDevice.id == device_id,
        RFIDDevice.is_active == True,
    ).first()
    if not device:
        raise NotFoundError("Device not registered or inactive")
    device.last_seen_at = datetime.now(timezone.utc)

    # Write audit scan event (always, regardless of outcome)
    scan_event = RFIDScanEvent(
        tag_uid=tag_uid,
        device_id=device_id,
        scanned_by_staff=staff_id,
        scan_type=scan_type_enum,
        bag_id=None,
        pickup_scanned_by_student_id=None,
    )
    db.add(scan_event)
    db.flush()

    if scan_type_enum == ScanTypeEnum.pickup_id:
        return _process_pickup_id(db, scan_event, staff_id, bag_id)

    return _process_bag_tag_scan(db, scan_event, scan_type_enum, staff_id)


# ── Bag-tag scan path (dropoff / ready / pickup_bag) ─────────────────────

def _process_bag_tag_scan(
    db: Session,
    scan_event: RFIDScanEvent,
    scan_type_enum: ScanTypeEnum,
    staff_id: UUID,
) -> dict:
    tag_uid = scan_event.tag_uid

    # Resolve tag — must be a bag tag
    tag = db.query(RFIDTag).filter(
        RFIDTag.tag_uid == tag_uid,
        RFIDTag.is_active == True,
        RFIDTag.tag_type == TagTypeEnum.bag,
    ).first()

    if not tag or not tag.student_id:
        db.commit()
        return _build_response(
            scan_event, None, None, "unknown_tag",
            "Bag tag not registered or not linked to any student",
        )

    student = db.query(Student).filter(Student.id == tag.student_id).first()
    if not student:
        db.commit()
        return _build_response(scan_event, None, None, "student_not_found",
                               "Student account not found")

    expected_from, expected_to = BAG_TAG_TRANSITIONS[scan_type_enum]

    # --- dropoff: verify booked slot, create bag ---
    if scan_type_enum == ScanTypeEnum.dropoff:
        today_slot = (
            db.query(Slot)
            .filter(
                Slot.student_id == student.id,
                Slot.date == date.today(),
                Slot.status == SlotStatusEnum.booked,
            )
            .first()
        )
        if not today_slot:
            db.commit()
            return _build_response(
                scan_event, student, None, "no_slot_booked",
                f"{student.name} has no booked slot for today — drop-off rejected",
            )
        bag = _get_or_create_bag(db, student, tag)
    else:
        # ready / pickup_bag: find the student's current active bag
        bag = (
            db.query(LaundryBag)
            .filter(
                LaundryBag.student_id == student.id,
                LaundryBag.status.notin_([BagStatusEnum.collected, BagStatusEnum.missed]),
            )
            .order_by(LaundryBag.updated_at.desc())
            .first()
        )

    if not bag:
        db.commit()
        return _build_response(scan_event, student, None, "no_active_bag",
                               f"No active bag found for {student.name}")

    if bag.status != expected_from:
        db.commit()
        return _build_response(
            scan_event, student, bag, "wrong_state",
            f"Bag is '{bag.status.value}'; '{scan_type_enum.value}' requires '{expected_from.value}'",
        )

    old_status = bag.status
    bag.status = expected_to
    bag.updated_at = datetime.now(timezone.utc)
    scan_event.bag_id = bag.id

    _log_transition(db, bag, old_status, expected_to, staff_id, scan_event.id)

    # Mark slot as used on drop-off
    if scan_type_enum == ScanTypeEnum.dropoff and bag.slot_id:
        slot = db.query(Slot).filter(Slot.id == bag.slot_id).first()
        if slot and slot.status == SlotStatusEnum.booked:
            slot.status = SlotStatusEnum.used

    db.commit()
    db.refresh(scan_event)
    db.refresh(bag)

    # FCM notifications
    try:
        if scan_type_enum == ScanTypeEnum.dropoff:
            notification_service.notify_bag_received(db, student, bag_id=bag.id)
        elif scan_type_enum == ScanTypeEnum.ready:
            notification_service.notify_bag_ready(db, student, bag_id=bag.id)
        # pickup_bag: no notification — student is standing at the counter
    except Exception as exc:
        print(f"[notify] failed for scan {scan_event.id}: {exc}")

    msg = f"Bag status updated: {old_status.value} → {expected_to.value}"
    if scan_type_enum == ScanTypeEnum.pickup_bag:
        msg += " — now tap college ID card to confirm pickup"

    return _build_response(scan_event, student, bag, "success", msg)


# ── ID-card scan path (pickup_id) ─────────────────────────────────────────

def _process_pickup_id(
    db: Session,
    scan_event: RFIDScanEvent,
    staff_id: UUID,
    bag_id: Optional[UUID],
) -> dict:
    """
    Step 2 of pickup: student taps college ID card.

    The device MUST supply the bag_id returned from the preceding
    pickup_bag scan. This ensures the ID confirmation is bound to the
    specific bag that was just retrieved — not any arbitrary bag.

    The ID card holder does NOT have to be the bag owner. Any student
    with a linked ID card is accepted. The tapper's student ID is
    recorded in the audit log only.
    """
    if not bag_id:
        db.commit()
        return _build_response(
            scan_event, None, None, "missing_bag_id",
            "bag_id is required for pickup_id scans — include the bag_id "
            "from the preceding pickup_bag scan response",
        )

    # Resolve the bag
    bag = db.query(LaundryBag).filter(LaundryBag.id == bag_id).first()
    if not bag:
        db.commit()
        return _build_response(scan_event, None, None, "bag_not_found",
                               "Bag not found for the supplied bag_id")

    if bag.status != BagStatusEnum.awaiting_id_scan:
        db.commit()
        bag_owner_check = db.query(Student).filter(Student.id == bag.student_id).first()
        return _build_response(
            scan_event, bag_owner_check, bag, "wrong_state",
            f"Bag is '{bag.status.value}'; pickup_id requires 'awaiting_id_scan'",
        )

    bag_owner = db.query(Student).filter(Student.id == bag.student_id).first()

    # Resolve the scanned ID card tag
    id_tag = db.query(RFIDTag).filter(
        RFIDTag.tag_uid == scan_event.tag_uid,
        RFIDTag.is_active == True,
        RFIDTag.tag_type == TagTypeEnum.id_card,
    ).first()

    if not id_tag:
        db.commit()
        return _build_response(
            scan_event, bag_owner, bag, "unknown_id_card",
            "College ID card not registered — please enroll the ID card first",
        )

    if not id_tag.student_id:
        db.commit()
        return _build_response(
            scan_event, bag_owner, bag, "id_card_not_linked",
            "ID card is not linked to any student account",
        )

    tapper = db.query(Student).filter(Student.id == id_tag.student_id).first()

    # Apply transition: awaiting_id_scan → collected
    old_status = bag.status
    bag.status = BagStatusEnum.collected
    bag.updated_at = datetime.now(timezone.utc)
    scan_event.bag_id = bag.id
    scan_event.pickup_scanned_by_student_id = id_tag.student_id

    _log_transition(
        db, bag,
        old_status, BagStatusEnum.collected,
        staff_id, scan_event.id,
        pickup_scanned_by_student=id_tag.student_id,
    )

    db.commit()
    db.refresh(scan_event)
    db.refresh(bag)

    tapper_name = tapper.name if tapper else "Unknown"
    owner_name = bag_owner.name if bag_owner else "Unknown"

    if tapper and bag_owner and tapper.id == bag_owner.id:
        collector_note = f"Collected by {tapper_name} (bag owner)"
    else:
        collector_note = (
            f"Collected on behalf of {owner_name} — "
            f"ID card tapped by {tapper_name}"
        )

    return _build_response(
        scan_event, bag_owner, bag, "success",
        f"Bag status updated: {old_status.value} → collected. {collector_note}",
        pickup_tapped_by=tapper,
    )


# ── Response builder ──────────────────────────────────────────────────────

def _build_response(
    scan_event: RFIDScanEvent,
    student: Optional[Student],
    bag: Optional[LaundryBag],
    result: str,
    message: str,
    pickup_tapped_by: Optional[Student] = None,
) -> dict:
    return {
        "scan_event_id": scan_event.id,
        "tag_uid": scan_event.tag_uid,
        "device_id": scan_event.device_id,
        "scan_type": scan_event.scan_type.value
                     if hasattr(scan_event.scan_type, "value")
                     else scan_event.scan_type,
        "timestamp": scan_event.timestamp,
        "result": result,
        "message": message,
        "student_name": student.name if student else None,
        "student_id": student.id if student else None,
        "bag_id": bag.id if bag else None,
        "bag_status": bag.status.value if bag else None,
        # who actually tapped the ID card (may differ from bag owner)
        "pickup_tapped_by_student_id": pickup_tapped_by.id if pickup_tapped_by else None,
        "pickup_tapped_by_student_name": pickup_tapped_by.name if pickup_tapped_by else None,
    }


# ── Bag helpers ───────────────────────────────────────────────────────────

def _get_or_create_bag(db: Session, student: Student, tag: RFIDTag) -> LaundryBag:
    bag = (
        db.query(LaundryBag)
        .filter(
            LaundryBag.student_id == student.id,
            LaundryBag.status.notin_([BagStatusEnum.collected, BagStatusEnum.missed]),
        )
        .order_by(LaundryBag.updated_at.desc())
        .first()
    )
    if not bag:
        slot = (
            db.query(Slot)
            .filter(
                Slot.student_id == student.id,
                Slot.date == date.today(),
                Slot.status == SlotStatusEnum.booked,
            )
            .first()
        )
        bag = LaundryBag(
            student_id=student.id,
            rfid_tag_id=tag.id,
            status=BagStatusEnum.pending,
            slot_id=slot.id if slot else None,
        )
        db.add(bag)
        db.flush()
    else:
        if not bag.rfid_tag_id:
            bag.rfid_tag_id = tag.id
    return bag


# ── Tag enrollment ────────────────────────────────────────────────────────

def link_bag_tag_to_student(
    db: Session,
    tag_uid: str,
    student_id: UUID,
    staff_id: UUID,
) -> RFIDTag:
    """
    Link a bag RFID tag UID to a student.
    Creates the tag record if it doesn't exist.
    Raises BadRequestError if already linked to a different student.
    """
    tag = db.query(RFIDTag).filter(RFIDTag.tag_uid == tag_uid).first()
    if not tag:
        tag = RFIDTag(tag_uid=tag_uid, tag_type=TagTypeEnum.bag)
        db.add(tag)
        db.flush()

    if tag.student_id and tag.student_id != student_id:
        raise BadRequestError("Bag tag is already linked to another student")

    tag.student_id = student_id
    tag.tag_type = TagTypeEnum.bag
    tag.linked_by = staff_id
    tag.linked_at = datetime.now(timezone.utc)
    tag.is_active = True
    db.commit()
    db.refresh(tag)
    return tag


def link_id_card_to_student(
    db: Session,
    tag_uid: str,
    student_id: UUID,
    staff_id: UUID,
) -> RFIDTag:
    """
    Link a student's college ID card RFID UID to their account.
    Only one active ID card tag is allowed per student; any existing
    active ID card tag for this student is deactivated first.
    """
    # Deactivate any existing active ID card for this student
    existing = db.query(RFIDTag).filter(
        RFIDTag.student_id == student_id,
        RFIDTag.tag_type == TagTypeEnum.id_card,
        RFIDTag.is_active == True,
    ).first()
    if existing and existing.tag_uid != tag_uid:
        existing.is_active = False

    tag = db.query(RFIDTag).filter(RFIDTag.tag_uid == tag_uid).first()
    if not tag:
        tag = RFIDTag(tag_uid=tag_uid, tag_type=TagTypeEnum.id_card)
        db.add(tag)
        db.flush()

    if tag.student_id and tag.student_id != student_id:
        raise BadRequestError("This ID card is already linked to another student")

    tag.student_id = student_id
    tag.tag_type = TagTypeEnum.id_card
    tag.linked_by = staff_id
    tag.linked_at = datetime.now(timezone.utc)
    tag.is_active = True
    db.commit()
    db.refresh(tag)
    return tag


# ── Original link_tag_to_student kept for backward compat ────────────────

def link_tag_to_student(
    db: Session,
    tag_uid: str,
    student_id: UUID,
    staff_id: UUID,
) -> RFIDTag:
    """Backward-compat wrapper — defaults to bag tag type."""
    return link_bag_tag_to_student(db, tag_uid, student_id, staff_id)


def unlink_tag(db: Session, tag_uid: str, staff_id: UUID) -> RFIDTag:
    """Deactivate a tag and remove student association. Works for both tag types."""
    tag = db.query(RFIDTag).filter(RFIDTag.tag_uid == tag_uid).first()
    if not tag:
        raise NotFoundError("Tag not found")
    tag.student_id = None
    tag.linked_by = staff_id
    tag.linked_at = datetime.now(timezone.utc)
    tag.is_active = False
    db.commit()
    db.refresh(tag)
    return tag


# ── Bag queries ───────────────────────────────────────────────────────────

def get_bag_status(db: Session, student_id: UUID) -> Optional[LaundryBag]:
    return (
        db.query(LaundryBag)
        .filter(
            LaundryBag.student_id == student_id,
            LaundryBag.status.notin_([BagStatusEnum.collected, BagStatusEnum.missed]),
        )
        .order_by(LaundryBag.updated_at.desc())
        .first()
    )


def get_bag_history(db: Session, student_id: UUID) -> list[LaundryBag]:
    return (
        db.query(LaundryBag)
        .filter(LaundryBag.student_id == student_id)
        .order_by(LaundryBag.updated_at.desc())
        .all()
    )


def get_status_logs(db: Session, bag_id: UUID) -> list[BagStatusLog]:
    return (
        db.query(BagStatusLog)
        .filter(BagStatusLog.bag_id == bag_id)
        .order_by(BagStatusLog.timestamp.asc())
        .all()
    )
