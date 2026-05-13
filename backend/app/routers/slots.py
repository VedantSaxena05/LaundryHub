from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session
from datetime import date

from app.database import get_db
from app.schemas.slot import (
    SlotBookRequest, SlotCancelRequest, SlotResponse,
    BlockAvailabilityResponse, DailyAvailabilityResponse,
)
from app.schemas.auth import UserRole
from app.services import slot_service
from app.utils.dependencies import get_current_user, require_admin
from app.utils.exceptions import ForbiddenError, BadRequestError
from app.config import HOSTEL_BLOCKS

router = APIRouter()


@router.post("/book", response_model=SlotResponse, status_code=201)
def book_slot(
    payload: SlotBookRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user._jwt_role != UserRole.student:
        raise ForbiddenError("Students only")
    return slot_service.book_slot(
        db, current_user, payload.date,
        payload.submission_start_time,
        payload.submission_window_minutes,
    )


@router.post("/cancel", response_model=SlotResponse)
def cancel_slot(
    payload: SlotCancelRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user._jwt_role != UserRole.student:
        raise ForbiddenError("Students only")
    return slot_service.cancel_slot(db, current_user, payload.slot_id)


@router.get("/my", response_model=list[SlotResponse])
def my_slots(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user._jwt_role != UserRole.student:
        raise ForbiddenError("Students only")
    return slot_service.get_student_slots(db, current_user.id)


@router.get("/availability/{target_date}", response_model=DailyAvailabilityResponse)
def daily_availability(
    target_date: date,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),  # any authenticated user can check
):
    """Returns availability for all blocks (A–E) on the given date."""
    return slot_service.get_daily_availability(db, target_date)


@router.get(
    "/availability/{target_date}/block/{block}",
    response_model=BlockAvailabilityResponse,
)
def block_availability(
    target_date: date,
    block: str = Path(..., description="Block letter A–E"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Returns availability for a single block on the given date."""
    block = block.upper()
    if block not in HOSTEL_BLOCKS:
        raise BadRequestError(f"Invalid block '{block}'. Must be one of {HOSTEL_BLOCKS}.")
    return slot_service.get_block_availability(db, target_date, block)


@router.patch("/block-limit/{block}", summary="Admin: update a block's daily slot limit at runtime")
def update_block_limit(
    block: str = Path(..., description="Block letter A–E"),
    new_limit: int = 30,
    _admin=Depends(require_admin),
):
    """
    Hot-updates the daily slot limit for a specific block in memory without
    restarting the server. For a permanent change, update BLOCK_SLOT_LIMITS in
    .env and restart.
    """
    from app.config import settings
    block = block.upper()
    if block not in HOSTEL_BLOCKS:
        raise BadRequestError(f"Invalid block '{block}'. Must be one of {HOSTEL_BLOCKS}.")
    if new_limit < 1:
        raise BadRequestError("Limit must be at least 1")
    settings.BLOCK_SLOT_LIMITS[block] = new_limit
    return {"message": f"Daily slot limit for Block {block} updated to {new_limit}"}

@router.post(
    "/expire-lapsed",
    summary="Expire slots whose submission window has passed",
    tags=["Slots"],
)
def expire_lapsed_slots(
    _staff=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Staff/admin trigger (or called by a cron job).
    Cancels all booked slots whose submission_expires_at has passed
    and the bag has not been dropped off, freeing capacity for other students.
    Returns the count of slots expired.
    """
    expired = slot_service.expire_lapsed_slots(db)
    return {"expired_slots": expired}