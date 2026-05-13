from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.staff import (
    DelayReportRequest, DelayReportResponse,
    BlockedDateRequest, BlockedDateResponse,
)
from app.services import staff_service
from app.utils.dependencies import require_staff, require_admin

router = APIRouter()


# ── Delay reports ─────────────────────────────────────────────────────────

@router.post("/delays", response_model=DelayReportResponse, status_code=201)
def report_delay(
    payload: DelayReportRequest,
    current_user=Depends(require_staff),
    db: Session = Depends(get_db),
):
    """
    Staff reports a delay for a given date.
    Automatically bulk-notifies all students with slots on that day.
    """
    return staff_service.create_delay_report(
        db=db,
        staff_id=current_user.id,
        reason=payload.reason,
        affected_date=payload.affected_date,
        note=payload.note,
    )


@router.get("/delays", response_model=List[DelayReportResponse])
def list_delays(
    current_user=Depends(require_staff),
    db: Session = Depends(get_db),
):
    return staff_service.list_delay_reports(db)


# ── Blocked dates ─────────────────────────────────────────────────────────

@router.post("/blocked-dates", response_model=BlockedDateResponse, status_code=201)
def add_blocked_date(
    payload: BlockedDateRequest,
    current_user=Depends(require_staff),
    db: Session = Depends(get_db),
):
    return staff_service.add_blocked_date(
        db=db,
        target_date=payload.date,
        reason=payload.reason,
        staff_id=current_user.id,
    )


@router.delete("/blocked-dates/{target_date}", status_code=204)
def remove_blocked_date(
    target_date: str,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    from datetime import date as Date
    from app.utils.exceptions import BadRequestError
    try:
        d = Date.fromisoformat(target_date)
    except ValueError:
        raise BadRequestError("Date must be YYYY-MM-DD")
    staff_service.remove_blocked_date(db, d)


@router.get("/blocked-dates", response_model=List[BlockedDateResponse])
def list_blocked_dates(
    current_user=Depends(require_staff),
    db: Session = Depends(get_db),
):
    return staff_service.list_blocked_dates(db)


# ── Today's ops dashboard ─────────────────────────────────────────────────

@router.get("/today")
def today_summary(
    current_user=Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Quick operational snapshot: bookings, drops, ready bags, collections."""
    return staff_service.get_today_summary(db)