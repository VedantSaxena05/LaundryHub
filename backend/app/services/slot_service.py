"""
Slot booking business logic.

Rules enforced here (all at the service/SQL layer, NOT just app logic):
  1. BLOCK daily limit  — each block (A–E) has its own max bookings per calendar day,
                          configured via BLOCK_SLOT_LIMITS in settings.
  2. MONTHLY_SLOT_QUOTA_PER_STUDENT — max slots per student per calendar month (default 4).
  3. A student cannot book the same date twice  (DB unique constraint + service check).
  4. The requested date must not be a blocked/holiday date.
  5. Drop-off is only accepted between DROPOFF_START_HOUR and DROPOFF_END_HOUR (10:00–19:00).
     Collection is open between COLLECTION_START_HOUR and COLLECTION_END_HOUR (11:00–19:00).
     Bookings themselves can be made at any time of day; only the physical operations
     are time-gated (enforced at the bag-drop/collection endpoints).
"""

from datetime import date, datetime, timezone, timedelta, time
from calendar import monthrange
from typing import List
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings, HOSTEL_BLOCKS, DROPOFF_START_HOUR, DROPOFF_END_HOUR
from app.config import COLLECTION_START_HOUR, COLLECTION_END_HOUR
from app.models.hostel import BlockedDate
from app.models.laundry import Slot, SlotStatusEnum
from app.models.user import Student
from app.schemas.slot import BlockAvailabilityResponse, DailyAvailabilityResponse
from app.utils.exceptions import BadRequestError, ConflictError, NotFoundError


# ── Time window helpers ───────────────────────────────────────────────────

def _fmt_hour(h: int) -> str:
    return f"{h:02d}:00"


from datetime import timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))

def is_dropoff_open(now=None):
    ist_now = (now or datetime.now(timezone.utc)).astimezone(IST)
    return 10 <= ist_now.hour < 19

def is_collection_open(now=None):
    ist_now = (now or datetime.now(timezone.utc)).astimezone(IST)
    return 11 <= ist_now.hour < 19


def assert_dropoff_open() -> None:
    """Raise BadRequestError if the drop-off window is not currently open."""
    if not is_dropoff_open():
        raise BadRequestError(
            f"Drop-off is only accepted between "
            f"{_fmt_hour(DROPOFF_START_HOUR)} and {_fmt_hour(DROPOFF_END_HOUR)}."
        )


def assert_collection_open() -> None:
    """Raise BadRequestError if the collection window is not currently open."""
    if not is_collection_open():
        raise BadRequestError(
            f"Collection is only available between "
            f"{_fmt_hour(COLLECTION_START_HOUR)} and {_fmt_hour(COLLECTION_END_HOUR)}."
        )


# ── Availability helpers ──────────────────────────────────────────────────

def count_block_daily_bookings(db: Session, target_date: date, block: str) -> int:
    """Total active (booked/used) slots for a specific block on a given date."""
    return (
        db.query(func.count(Slot.id))
        .join(Student, Student.id == Slot.student_id)
        .filter(
            Slot.date == target_date,
            Slot.status.in_([SlotStatusEnum.booked, SlotStatusEnum.used]),
            Student.block == block.upper(),
        )
        .scalar()
        or 0
    )


def get_block_availability(
    db: Session, target_date: date, block: str
) -> BlockAvailabilityResponse:
    block = block.upper()
    booked = count_block_daily_bookings(db, target_date, block)
    limit = settings.get_block_limit(block)
    return BlockAvailabilityResponse(
        date=target_date,
        block=block,
        block_limit=limit,
        booked_count=booked,
        remaining=max(0, limit - booked),
        is_available=booked < limit,
        dropoff_window=f"{_fmt_hour(DROPOFF_START_HOUR)} – {_fmt_hour(DROPOFF_END_HOUR)}",
        collection_window=f"{_fmt_hour(COLLECTION_START_HOUR)} – {_fmt_hour(COLLECTION_END_HOUR)}",
    )


def get_daily_availability(db: Session, target_date: date) -> DailyAvailabilityResponse:
    """Availability for all blocks on a given date."""
    return DailyAvailabilityResponse(
        date=target_date,
        blocks=[get_block_availability(db, target_date, b) for b in HOSTEL_BLOCKS],
    )


def count_monthly_bookings(db: Session, student_id: UUID, year: int, month: int) -> int:
    """Active slots for one student in a given month."""
    month_start = date(year, month, 1)
    month_end = date(year, month, monthrange(year, month)[1])
    return (
        db.query(func.count(Slot.id))
        .filter(
            Slot.student_id == student_id,
            Slot.date >= month_start,
            Slot.date <= month_end,
            Slot.status.in_([SlotStatusEnum.booked, SlotStatusEnum.used]),
        )
        .scalar()
        or 0
    )


def next_month_index(db: Session, student_id: UUID, year: int, month: int) -> int:
    """Returns the next available month_index (1–N) for a student this month."""
    used_indices = (
        db.query(Slot.month_index)
        .filter(
            Slot.student_id == student_id,
            func.extract("year", Slot.date) == year,
            func.extract("month", Slot.date) == month,
            Slot.status.in_([SlotStatusEnum.booked, SlotStatusEnum.used]),
        )
        .all()
    )
    used = {row[0] for row in used_indices}
    for i in range(1, settings.MONTHLY_SLOT_QUOTA_PER_STUDENT + 1):
        if i not in used:
            return i
    raise BadRequestError(
        f"Monthly quota reached ({settings.MONTHLY_SLOT_QUOTA_PER_STUDENT} slots per month)"
    )


# ── Date validation ───────────────────────────────────────────────────────

def is_date_blocked(db: Session, target_date: date) -> bool:
    return db.query(BlockedDate).filter(BlockedDate.date == target_date).first() is not None


# ── Core booking / cancellation ───────────────────────────────────────────

def book_slot(
    db: Session,
    student: Student,
    target_date: date,
    submission_start_time: str = "10:00",
    submission_window_minutes: int = 30,
) -> Slot:
    # 1. Blocked date?
    if is_date_blocked(db, target_date):
        raise BadRequestError("This date is blocked (holiday / maintenance)")

    # 2. Per-block daily capacity check
    block = student.block.upper()
    block_count = count_block_daily_bookings(db, target_date, block)
    block_limit = settings.get_block_limit(block)
    if block_count >= block_limit:
        raise BadRequestError(
            f"Block {block} is fully booked for {target_date} "
            f"(limit: {block_limit}). Please choose another date."
        )

    # 3. Monthly quota per student
    monthly = count_monthly_bookings(db, student.id, target_date.year, target_date.month)
    if monthly >= settings.MONTHLY_SLOT_QUOTA_PER_STUDENT:
        raise BadRequestError(
            f"You have used all {settings.MONTHLY_SLOT_QUOTA_PER_STUDENT} "
            "slots for this month."
        )

    # 4. Duplicate booking check (also enforced by DB unique constraint)
    existing = (
        db.query(Slot)
        .filter(
            Slot.student_id == student.id,
            Slot.date == target_date,
        )
        .first()
    )
    if existing:
        if existing.status != SlotStatusEnum.cancelled:
            raise ConflictError("You already have a booking for this date")
        # Reuse the cancelled row to avoid violating the unique constraint
        existing.status = SlotStatusEnum.booked
        existing.cancelled_at = None
        existing.month_index = next_month_index(db, student.id, target_date.year, target_date.month)
        existing.submission_window_minutes = submission_window_minutes
        existing.submission_window_start, existing.submission_expires_at = _compute_expiry(
            target_date, submission_start_time, submission_window_minutes
        )
        db.commit()
        db.refresh(existing)
        return existing

    month_index = next_month_index(db, student.id, target_date.year, target_date.month)

    _window_start, _expires_at = _compute_expiry(target_date, submission_start_time, submission_window_minutes)
    slot = Slot(
        student_id=student.id,
        date=target_date,
        status=SlotStatusEnum.booked,
        month_index=month_index,
        submission_window_minutes=submission_window_minutes,
        submission_window_start=_window_start,
        submission_expires_at=_expires_at,
    )
    db.add(slot)
    db.commit()
    db.refresh(slot)
    return slot


def cancel_slot(db: Session, student: Student, slot_id: UUID) -> Slot:
    slot = db.query(Slot).filter(Slot.id == slot_id, Slot.student_id == student.id).first()
    if not slot:
        raise NotFoundError("Slot not found")
    if slot.status != SlotStatusEnum.booked:
        raise BadRequestError(f"Cannot cancel a slot with status '{slot.status}'")

    slot.status = SlotStatusEnum.cancelled
    slot.cancelled_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(slot)
    return slot


def get_student_slots(db: Session, student_id: UUID) -> List[Slot]:
    return (
        db.query(Slot)
        .filter(Slot.student_id == student_id)
        .order_by(Slot.date.desc())
        .all()
    )


# ── Submission window helpers ─────────────────────────────────────────────

def _compute_expiry(
    target_date: date,
    start_time_str: str,
    window_minutes: int,
) -> tuple[datetime, datetime]:
    """
    Returns (window_start_utc, submission_expires_at_utc).
    start_time_str is "HH:MM" (validated by schema to be within 10:00–19:00).
    """
    h, m = start_time_str.split(":")
    window_start = datetime(
        target_date.year, target_date.month, target_date.day,
        int(h), int(m), 0, tzinfo=timezone.utc
    )
    expires_at = window_start + timedelta(minutes=window_minutes)
    return window_start, expires_at


def expire_lapsed_slots(db: Session) -> int:
    """
    Sweep all booked slots whose submission_expires_at has passed without a
    drop-off (i.e. the slot is still 'booked', not 'used').
    Marks them as 'cancelled' so the capacity is freed for other students.
    Returns the number of slots expired.
    """
    now = datetime.now(timezone.utc)
    lapsed = (
        db.query(Slot)
        .filter(
            Slot.status == SlotStatusEnum.booked,
            Slot.submission_expires_at != None,          # noqa: E711
            Slot.submission_expires_at <= now,
        )
        .all()
    )
    for slot in lapsed:
        slot.status = SlotStatusEnum.cancelled
        slot.cancelled_at = now
    if lapsed:
        db.commit()
    return len(lapsed)