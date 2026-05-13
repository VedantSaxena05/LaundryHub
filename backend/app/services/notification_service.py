"""
Notification service — FCM only (Android / Capacitor).

Firebase Cloud Messaging is the sole push channel.
VAPID / Web Push has been removed.

Dispatch:
  1. If student has fcm_token → send FCM push
  2. Always write NotificationLog row

FCM failure does not raise — errors are logged and swallowed so that
the calling scan/booking code is never blocked by a notification failure.
"""
from datetime import date as DateType
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.notification import NotificationLog, NotificationEventEnum
from app.models.user import Student
from app.notifications import templates_en, templates_ta


# ── FCM singleton initialisation ─────────────────────────────────────────

_firebase_initialised = False


def _ensure_firebase():
    global _firebase_initialised
    if _firebase_initialised:
        return True
    try:
        import firebase_admin
        from firebase_admin import credentials
        from app.config import settings

        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
        _firebase_initialised = True
        return True
    except Exception as exc:
        print(f"[FCM] Firebase initialisation failed: {exc}")
        return False


# ── FCM dispatch ─────────────────────────────────────────────────────────

def _send_fcm(fcm_token: str, title: str, body: str, data: Optional[dict] = None) -> bool:
    """
    Send a push notification via Firebase Cloud Messaging.

    Args:
        fcm_token: The student's device FCM registration token.
        title:     Notification title (localised).
        body:      Notification body (localised).
        data:      Optional key-value data payload for the app to handle silently.

    Returns True on success, False on any failure.
    """
    if not _ensure_firebase():
        return False
    try:
        from firebase_admin import messaging

        android_config = messaging.AndroidConfig(
            priority="high",
            notification=messaging.AndroidNotification(
                icon="ic_notification",
                color="#1565C0",
                channel_id="laundry_alerts",
                sound="default",
            ),
        )

        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            android=android_config,
            data=data or {},
            token=fcm_token,
        )
        messaging.send(message)
        return True
    except Exception as exc:
        print(f"[FCM] send failed: {exc}")
        return False


# ── Template resolution ───────────────────────────────────────────────────

def _resolve(lang: str, event: str, **kwargs) -> tuple[str, str]:
    """Returns (title, body) for an event in the student's preferred language."""
    mod = templates_ta if lang == "ta" else templates_en
    fn = getattr(mod, event)
    return fn(**kwargs)


# ── Core dispatch + log ───────────────────────────────────────────────────

def send_notification(
    db: Session,
    student: Student,
    event_type: NotificationEventEnum,
    template_kwargs: dict,
    extra_data: Optional[dict] = None,
) -> NotificationLog:
    """
    Resolve templates, send FCM, and write a NotificationLog row.

    extra_data is passed as the FCM data payload (key-value strings),
    useful for the mobile app to route to the correct screen.
    """
    lang = student.language_preference or "en"
    title, body = _resolve(lang, event_type.value, **template_kwargs)

    fcm_ok = False
    if student.fcm_token:
        fcm_ok = _send_fcm(
            fcm_token=student.fcm_token,
            title=title,
            body=body,
            data=extra_data,
        )

    log = NotificationLog(
        student_id=student.id,
        event_type=event_type,
        language=lang,
        title=title,
        body=body,
        fcm_success=fcm_ok,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


# ── Convenience wrappers ──────────────────────────────────────────────────

def notify_bag_received(db: Session, student: Student, bag_id: Optional[str] = None):
    """Fired on dropoff scan — bag received at laundry."""
    send_notification(
        db, student,
        NotificationEventEnum.bag_received,
        {"student_name": student.name},
        extra_data={"event": "bag_received", "bag_id": str(bag_id) if bag_id else ""},
    )


def notify_bag_ready(db: Session, student: Student, bag_id: Optional[str] = None):
    """Fired on ready scan — bag washed and ready for collection."""
    send_notification(
        db, student,
        NotificationEventEnum.bag_ready,
        {"student_name": student.name},
        extra_data={"event": "bag_ready", "bag_id": str(bag_id) if bag_id else ""},
    )


def notify_delay(db: Session, student: Student, reason: str, affected_date: DateType):
    from app.notifications import templates_en as en, templates_ta as ta
    mod = ta if (student.language_preference or "en") == "ta" else en
    reason_label = mod.DELAY_REASON_LABELS.get(reason, reason)
    send_notification(
        db, student,
        NotificationEventEnum.delay,
        {"reason_label": reason_label, "affected_date": affected_date},
        extra_data={"event": "delay"},
    )


def notify_reminder(db: Session, student: Student, slot_date: DateType):
    send_notification(
        db, student,
        NotificationEventEnum.reminder,
        {"student_name": student.name, "slot_date": slot_date},
        extra_data={"event": "reminder", "slot_date": str(slot_date)},
    )


def notify_uncollected(db: Session, student: Student):
    send_notification(
        db, student,
        NotificationEventEnum.uncollected_warning,
        {"student_name": student.name},
        extra_data={"event": "uncollected_warning"},
    )


def notify_slot_missed(db: Session, student: Student, slot_date: DateType):
    send_notification(
        db, student,
        NotificationEventEnum.slot_missed,
        {"student_name": student.name, "slot_date": slot_date},
        extra_data={"event": "slot_missed", "slot_date": str(slot_date)},
    )
