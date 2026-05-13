"""
Push notification endpoints — FCM only.

POST /notifications/fcm/register   — save or update student's FCM token
DELETE /notifications/fcm/unregister — remove FCM token on logout
GET  /notifications/history        — student's notification log
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.database import get_db
from app.models.notification import NotificationLog, NotificationEventEnum
from app.schemas.auth import UserRole
from app.utils.dependencies import get_current_user
from app.utils.exceptions import ForbiddenError

router = APIRouter()


# ── Request / Response schemas ────────────────────────────────────────────

class FCMRegisterRequest(BaseModel):
    """Student registers (or refreshes) their FCM device token."""
    fcm_token: str


class NotificationLogResponse(BaseModel):
    id: UUID
    student_id: UUID
    event_type: str
    language: str
    title: str
    body: str
    sent_at: datetime
    fcm_success: bool

    model_config = {"from_attributes": True}


# ── FCM token registration ────────────────────────────────────────────────

@router.post("/fcm/register", status_code=204)
def register_fcm_token(
    payload: FCMRegisterRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save or refresh the authenticated student's FCM registration token.
    The mobile app calls this on login and whenever the FCM token is rotated
    (Firebase rotates tokens automatically; the app must update here).
    """
    if current_user._jwt_role != UserRole.student:
        raise ForbiddenError("Students only")
    current_user.fcm_token = payload.fcm_token
    db.commit()


@router.delete("/fcm/unregister", status_code=204)
def unregister_fcm_token(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Remove the FCM token when the student logs out or revokes notification
    permission. Prevents push deliveries to logged-out sessions.
    """
    if current_user._jwt_role != UserRole.student:
        raise ForbiddenError("Students only")
    current_user.fcm_token = None
    db.commit()


# ── Notification history ──────────────────────────────────────────────────

@router.get("/history", response_model=List[NotificationLogResponse])
def notification_history(
    limit: int = 50,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return the authenticated student's notification log, newest first.
    Useful for the in-app notification inbox and debugging delivery.
    """
    if current_user._jwt_role != UserRole.student:
        raise ForbiddenError("Students only")
    logs = (
        db.query(NotificationLog)
        .filter(NotificationLog.student_id == current_user.id)
        .order_by(NotificationLog.sent_at.desc())
        .limit(limit)
        .all()
    )
    return logs
