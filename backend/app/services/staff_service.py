from datetime import date
from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.delay import DelayReport
from app.models.hostel import BlockedDate
from app.models.laundry import LaundryBag, Slot, BagStatusEnum, SlotStatusEnum
from app.models.user import Student
from app.services import notification_service
from app.utils.exceptions import ConflictError, NotFoundError


# ── Delay reports ─────────────────────────────────────────────────────────

def create_delay_report(
    db: Session,
    staff_id: UUID,
    reason: str,
    affected_date: date,
    note: str | None,
) -> DelayReport:
    report = DelayReport(
        reported_by=staff_id,
        reason=reason,
        affected_date=affected_date,
        note=note,
    )
    db.add(report)
    db.flush()

    # Notify all students who have a booked slot on the affected date
    affected_students = (
        db.query(Student)
        .join(Slot, Slot.student_id == Student.id)
        .filter(
            Slot.date == affected_date,
            Slot.status.in_([SlotStatusEnum.booked, SlotStatusEnum.used]),
        )
        .all()
    )
    for student in affected_students:
        notification_service.notify_delay(db, student, reason, affected_date)

    report.notification_sent = len(affected_students) > 0
    db.commit()
    db.refresh(report)
    return report


def list_delay_reports(db: Session) -> List[DelayReport]:
    return db.query(DelayReport).order_by(DelayReport.created_at.desc()).all()


# ── Blocked dates ─────────────────────────────────────────────────────────

def add_blocked_date(db: Session, target_date: date, reason: str, staff_id: UUID) -> BlockedDate:
    existing = db.query(BlockedDate).filter(BlockedDate.date == target_date).first()
    if existing:
        raise ConflictError(f"{target_date} is already blocked")
    bd = BlockedDate(date=target_date, reason=reason, created_by=staff_id)
    db.add(bd)
    db.commit()
    db.refresh(bd)
    return bd


def remove_blocked_date(db: Session, target_date: date) -> None:
    bd = db.query(BlockedDate).filter(BlockedDate.date == target_date).first()
    if not bd:
        raise NotFoundError(f"No blocked date found for {target_date}")
    db.delete(bd)
    db.commit()


def list_blocked_dates(db: Session) -> List[BlockedDate]:
    return db.query(BlockedDate).order_by(BlockedDate.date).all()


# ── Today's operations view ───────────────────────────────────────────────

def get_today_summary(db: Session) -> dict:
    today = date.today()
    total_booked = (
        db.query(Slot)
        .filter(Slot.date == today, Slot.status.in_([SlotStatusEnum.booked, SlotStatusEnum.used]))
        .count()
    )
    bags_dropped = (
        db.query(LaundryBag)
        .filter(LaundryBag.status == BagStatusEnum.dropped)
        .count()
    )
    bags_ready = (
        db.query(LaundryBag)
        .filter(LaundryBag.status == BagStatusEnum.ready)
        .count()
    )
    bags_collected = (
        db.query(LaundryBag)
        .join(Slot, LaundryBag.slot_id == Slot.id)
        .filter(Slot.date == today, LaundryBag.status == BagStatusEnum.collected)
        .count()
    )
    return {
        "date": str(today),
        "total_booked": total_booked,
        "bags_dropped": bags_dropped,
        "bags_ready": bags_ready,
        "bags_collected": bags_collected,
        "bags_pending_collection": bags_ready,
    }