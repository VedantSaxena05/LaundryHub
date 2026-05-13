from pydantic import BaseModel, field_validator, model_validator
from uuid import UUID
from datetime import date, datetime, time
from typing import Optional

# Valid submission window bounds (in minutes)
SUBMISSION_WINDOW_MIN = 10
SUBMISSION_WINDOW_MAX = 60

# Drop-off period bounds (hour, minute) in local/UTC
DROPOFF_START = time(10, 0)   # 10:00
DROPOFF_END   = time(19, 0)   # 19:00


class SlotBookRequest(BaseModel):
    date: date
    # HH:MM string e.g. "12:30" — must be within 10:00–19:00
    submission_start_time: str = "10:00"
    # Duration in minutes the student commits to; 10–60
    submission_window_minutes: int = 30

    @field_validator("submission_start_time")
    @classmethod
    def validate_start_format(cls, v: str) -> str:
        try:
            h, m = v.split(":")
            t = time(int(h), int(m))
        except Exception:
            raise ValueError("submission_start_time must be HH:MM (e.g. '10:30')")
        if not (DROPOFF_START <= t < DROPOFF_END):
            raise ValueError(
                f"submission_start_time must be between "
                f"{DROPOFF_START.strftime('%H:%M')} and {DROPOFF_END.strftime('%H:%M')}"
            )
        return v

    @field_validator("submission_window_minutes")
    @classmethod
    def validate_duration(cls, v: int) -> int:
        if not (SUBMISSION_WINDOW_MIN <= v <= SUBMISSION_WINDOW_MAX):
            raise ValueError(
                f"submission_window_minutes must be between "
                f"{SUBMISSION_WINDOW_MIN} and {SUBMISSION_WINDOW_MAX}"
            )
        return v

    @model_validator(mode="after")
    def validate_window_fits(self) -> "SlotBookRequest":
        """Ensure start + duration does not exceed 19:00."""
        h, m = self.submission_start_time.split(":")
        start = time(int(h), int(m))
        total_minutes = start.hour * 60 + start.minute + self.submission_window_minutes
        if total_minutes > DROPOFF_END.hour * 60:
            max_duration = DROPOFF_END.hour * 60 - (start.hour * 60 + start.minute)
            raise ValueError(
                f"Window exceeds drop-off period: start {self.submission_start_time} "
                f"+ {self.submission_window_minutes} min goes past 19:00. "
                f"Max duration from this start is {max_duration} min."
            )
        return self


class SlotCancelRequest(BaseModel):
    slot_id: UUID


class SlotResponse(BaseModel):
    id: UUID
    student_id: UUID
    date: date
    status: str
    month_index: int
    submission_window_minutes: Optional[int] = None
    submission_window_start: Optional[datetime] = None
    submission_expires_at: Optional[datetime] = None
    created_at: datetime
    cancelled_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BlockAvailabilityResponse(BaseModel):
    date: date
    block: str
    block_limit: int
    booked_count: int
    remaining: int
    is_available: bool
    dropoff_window: str
    collection_window: str


class DailyAvailabilityResponse(BaseModel):
    date: date
    blocks: list[BlockAvailabilityResponse]