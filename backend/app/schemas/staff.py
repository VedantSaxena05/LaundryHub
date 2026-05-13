from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from typing import Optional


class DelayReportRequest(BaseModel):
    reason: str     # power_cut | water_shortage | machine_repair | too_many_clothes | staff_shortage
    affected_date: date
    note: Optional[str] = None


class DelayReportResponse(BaseModel):
    id: UUID
    reported_by: UUID
    reason: str
    affected_date: date
    note: Optional[str] = None
    created_at: datetime
    notification_sent: bool

    model_config = {"from_attributes": True}


class BlockedDateRequest(BaseModel):
    date: date
    reason: str


class BlockedDateResponse(BaseModel):
    id: UUID
    date: date
    reason: str
    created_by: Optional[UUID] = None

    model_config = {"from_attributes": True}