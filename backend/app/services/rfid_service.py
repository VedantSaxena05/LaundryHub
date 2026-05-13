from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.rfid import RFIDDevice, RFIDTag, RFIDScanEvent
from app.schemas.rfid import DeviceRegisterRequest
from app.utils.exceptions import NotFoundError


# ── Device management ─────────────────────────────────────────────────────

def register_device(db: Session, payload: DeviceRegisterRequest, configured_by: UUID) -> RFIDDevice:
    device = RFIDDevice(
        device_name=payload.device_name,
        location_tag=payload.location_tag,
        configured_by=configured_by,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def list_devices(db: Session) -> List[RFIDDevice]:
    return db.query(RFIDDevice).order_by(RFIDDevice.created_at.desc()).all()


def get_device(db: Session, device_id: UUID) -> RFIDDevice:
    device = db.query(RFIDDevice).filter(RFIDDevice.id == device_id).first()
    if not device:
        raise NotFoundError("Device not found")
    return device


def deactivate_device(db: Session, device_id: UUID) -> None:
    device = db.query(RFIDDevice).filter(RFIDDevice.id == device_id).first()
    if not device:
        raise NotFoundError("Device not found")
    device.is_active = False
    db.commit()


# ── Tag management ────────────────────────────────────────────────────────

def list_tags(db: Session) -> List[RFIDTag]:
    return db.query(RFIDTag).order_by(RFIDTag.created_at.desc()).all()


def get_tag_by_uid(db: Session, tag_uid: str) -> RFIDTag:
    tag = db.query(RFIDTag).filter(RFIDTag.tag_uid == tag_uid).first()
    if not tag:
        raise NotFoundError("Tag not found")
    return tag


def deactivate_tag(db: Session, tag_uid: str) -> None:
    tag = db.query(RFIDTag).filter(RFIDTag.tag_uid == tag_uid).first()
    if not tag:
        raise NotFoundError("Tag not found")
    tag.is_active = False
    db.commit()


# ── Scan event log ────────────────────────────────────────────────────────

def list_scan_events(db: Session, limit: int = 100) -> List[RFIDScanEvent]:
    return (
        db.query(RFIDScanEvent)
        .order_by(RFIDScanEvent.timestamp.desc())
        .limit(limit)
        .all()
    )