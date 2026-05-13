"""
Admin router — analytics, user management, and system controls.
All endpoints require the 'admin' role.
"""
from datetime import date
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.laundry import LaundryBag, Slot, BagStatusEnum, SlotStatusEnum
from app.models.notification import NotificationLog
from app.models.user import Student, Staff
from app.schemas.user import StudentResponse, StaffResponse
from app.utils.dependencies import require_admin
from app.utils.exceptions import NotFoundError
from app.config import HOSTEL_BLOCKS, settings
from app.services.slot_service import count_block_daily_bookings

router = APIRouter()


# ── User management ───────────────────────────────────────────────────────

@router.get("/students", response_model=List[StudentResponse])
def list_students(
    active_only: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(Student)
    if active_only:
        q = q.filter(Student.is_active == True)
    offset = (page - 1) * page_size
    return q.order_by(Student.created_at.desc()).offset(offset).limit(page_size).all()


@router.get("/staff", response_model=List[StaffResponse])
def list_staff(
    active_only: bool = Query(True),
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(Staff)
    if active_only:
        q = q.filter(Staff.is_active == True)
    return q.order_by(Staff.created_at.desc()).all()


@router.patch("/staff/{staff_id}/deactivate", response_model=StaffResponse)
def deactivate_staff(
    staff_id: UUID,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise NotFoundError("Staff member not found")
    staff.is_active = False
    db.commit()
    db.refresh(staff)
    return staff


# ── Analytics ─────────────────────────────────────────────────────────────

@router.get("/analytics/slots")
def slot_analytics(
    from_date: date = Query(..., description="YYYY-MM-DD"),
    to_date: date = Query(..., description="YYYY-MM-DD"),
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Slot booking stats for a date range, broken down by block."""
    total = db.query(Slot).filter(
        Slot.date >= from_date, Slot.date <= to_date
    ).count()
    used = db.query(Slot).filter(
        Slot.date >= from_date, Slot.date <= to_date,
        Slot.status == SlotStatusEnum.used,
    ).count()
    cancelled = db.query(Slot).filter(
        Slot.date >= from_date, Slot.date <= to_date,
        Slot.status == SlotStatusEnum.cancelled,
    ).count()
    missed = db.query(Slot).filter(
        Slot.date >= from_date, Slot.date <= to_date,
        Slot.status == SlotStatusEnum.missed,
    ).count()

    # Per-block breakdown
    per_block = {}
    for block in HOSTEL_BLOCKS:
        block_total = (
            db.query(Slot)
            .join(Student, Student.id == Slot.student_id)
            .filter(
                Slot.date >= from_date,
                Slot.date <= to_date,
                Student.block == block,
            )
            .count()
        )
        block_used = (
            db.query(Slot)
            .join(Student, Student.id == Slot.student_id)
            .filter(
                Slot.date >= from_date,
                Slot.date <= to_date,
                Student.block == block,
                Slot.status == SlotStatusEnum.used,
            )
            .count()
        )
        per_block[block] = {
            "limit_per_day": settings.get_block_limit(block),
            "total_booked": block_total,
            "used": block_used,
        }

    return {
        "from_date": str(from_date),
        "to_date": str(to_date),
        "total_booked": total,
        "used": used,
        "cancelled": cancelled,
        "missed": missed,
        "utilisation_rate": round(used / total, 4) if total else 0.0,
        "by_block": per_block,
    }


@router.get("/analytics/bags")
def bag_analytics(
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Current counts of bags in each state."""
    counts = {}
    for status in BagStatusEnum:
        counts[status.value] = db.query(LaundryBag).filter(
            LaundryBag.status == status
        ).count()
    return counts


@router.get("/analytics/notifications")
def notification_analytics(
    from_date: date = Query(..., description="YYYY-MM-DD"),
    to_date: date = Query(..., description="YYYY-MM-DD"),
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """FCM delivery success rate for a date range."""
    logs = db.query(NotificationLog).filter(
        NotificationLog.sent_at >= from_date,
        NotificationLog.sent_at <= to_date,
    ).all()
    total = len(logs)
    success = sum(1 for l in logs if l.fcm_success)
    by_event: dict = {}
    for log in logs:
        ev = log.event_type.value
        by_event.setdefault(ev, {"total": 0, "success": 0})
        by_event[ev]["total"] += 1
        if log.fcm_success:
            by_event[ev]["success"] += 1
    return {
        "from_date": str(from_date),
        "to_date": str(to_date),
        "total_sent": total,
        "fcm_success": success,
        "fcm_failure": total - success,
        "success_rate": round(success / total, 4) if total else 0.0,
        "by_event_type": by_event,
    }


@router.delete("/students/{student_id}/slots/used", summary="Admin: clear used slot bookings for a student")
def clear_used_slots_for_student(
    student_id: UUID,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Clears (deletes) all slots with status 'used' for the given student.
    This frees up their booking history so their monthly quota reflects
    only active/pending bookings. Useful for resetting a student's record
    after a dispute, data-entry error, or exceptional circumstance.

    Returns the number of used slots removed.
    """
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise NotFoundError("Student not found")

    used_slots = (
        db.query(Slot)
        .filter(
            Slot.student_id == student_id,
            Slot.status == SlotStatusEnum.used,
        )
        .all()
    )
    count = len(used_slots)
    for slot in used_slots:
        db.delete(slot)
    db.commit()
    return {
        "message": f"Cleared {count} used slot(s) for student {student_id}.",
        "student_id": str(student_id),
        "cleared_count": count,
    }


@router.get("/analytics/overview")
def overview(
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """High-level system health snapshot."""
    total_students = db.query(Student).filter(Student.is_active == True).count()
    total_staff = db.query(Staff).filter(Staff.is_active == True).count()
    today = date.today()
    slots_today = db.query(Slot).filter(Slot.date == today).count()
    bags_in_flight = db.query(LaundryBag).filter(
        LaundryBag.status.notin_([BagStatusEnum.collected, BagStatusEnum.missed])
    ).count()

    # Per-block capacity usage today
    block_usage = {
        block: {
            "booked": count_block_daily_bookings(db, today, block),
            "limit": settings.get_block_limit(block),
        }
        for block in HOSTEL_BLOCKS
    }

    return {
        "active_students": total_students,
        "active_staff": total_staff,
        "slots_booked_today": slots_today,
        "bags_in_flight": bags_in_flight,
        "block_usage_today": block_usage,
    }