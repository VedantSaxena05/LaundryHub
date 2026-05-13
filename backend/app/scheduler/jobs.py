"""
APScheduler background jobs.

Job 1 — 07:00  morning_reminder    Notify students with a slot today
Job 2 — 20:00  uncollected_warning Notify students whose bag is still 'ready'
Job 3 — 00:01  midnight_sweep      Mark un-dropped slots as 'missed'

The scheduler is started in app startup and stopped on shutdown.
"""
from datetime import date, datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal
from app.models.laundry import Slot, LaundryBag, SlotStatusEnum, BagStatusEnum
from app.models.user import Student
from app.services import notification_service

scheduler = BackgroundScheduler(timezone="Asia/Kolkata")


# ── Job 1: 7 AM morning reminder ─────────────────────────────────────────

def morning_reminder_job():
    db = SessionLocal()
    try:
        today = date.today()
        slots_today = (
            db.query(Slot)
            .filter(Slot.date == today, Slot.status == SlotStatusEnum.booked)
            .all()
        )
        for slot in slots_today:
            student = db.query(Student).filter(Student.id == slot.student_id).first()
            if student:
                notification_service.notify_reminder(db, student, today)
    finally:
        db.close()


# ── Job 2: 8 PM uncollected warning ──────────────────────────────────────

def uncollected_warning_job():
    db = SessionLocal()
    try:
        ready_bags = (
            db.query(LaundryBag)
            .filter(LaundryBag.status == BagStatusEnum.ready)
            .all()
        )
        for bag in ready_bags:
            student = db.query(Student).filter(Student.id == bag.student_id).first()
            if student:
                notification_service.notify_uncollected(db, student)
    finally:
        db.close()


# ── Job 3: midnight missed-slot sweep ─────────────────────────────────────

def midnight_sweep_job():
    """
    Runs at 00:01.
    Any slot dated yesterday that is still 'booked' (bag never dropped)
    → mark slot as 'missed' and bag as 'missed'.
    """
    from datetime import timedelta
    db = SessionLocal()
    try:
        yesterday = date.today() - timedelta(days=1)
        missed_slots = (
            db.query(Slot)
            .filter(Slot.date == yesterday, Slot.status == SlotStatusEnum.booked)
            .all()
        )
        for slot in missed_slots:
            slot.status = SlotStatusEnum.missed

            # Also mark any pending/dropped bag as missed
            bag = (
                db.query(LaundryBag)
                .filter(
                    LaundryBag.slot_id == slot.id,
                    LaundryBag.status.in_([BagStatusEnum.pending, BagStatusEnum.dropped]),
                )
                .first()
            )
            if bag:
                bag.status = BagStatusEnum.missed

            student = db.query(Student).filter(Student.id == slot.student_id).first()
            if student:
                notification_service.notify_slot_missed(db, student, yesterday)

        db.commit()
    finally:
        db.close()


# ── Register & lifecycle ──────────────────────────────────────────────────

def start_scheduler():
    scheduler.add_job(morning_reminder_job,  CronTrigger(hour=7,  minute=0),  id="morning_reminder")
    scheduler.add_job(uncollected_warning_job, CronTrigger(hour=20, minute=0), id="uncollected_warning")
    scheduler.add_job(midnight_sweep_job,    CronTrigger(hour=0,  minute=1),  id="midnight_sweep")
    scheduler.start()


def stop_scheduler():
    scheduler.shutdown(wait=False)