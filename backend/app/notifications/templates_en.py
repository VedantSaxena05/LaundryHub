"""
English notification templates.
Each function returns (title, body) for a given event.
"""
from datetime import date as DateType


def bag_received(student_name: str) -> tuple[str, str]:
    return (
        "Bag Received ✅",
        f"Hi {student_name}, your laundry bag has been received by the laundry staff.",
    )


def bag_ready(student_name: str) -> tuple[str, str]:
    return (
        "Laundry Ready 👕",
        f"Hi {student_name}, your laundry is washed and ready for collection!",
    )


def delay(reason_label: str, affected_date: DateType) -> tuple[str, str]:
    return (
        "Laundry Delay ⚠️",
        f"There will be a delay in laundry service on {affected_date.strftime('%d %b %Y')} "
        f"due to: {reason_label}. We apologise for the inconvenience.",
    )


def morning_reminder(student_name: str, slot_date: DateType) -> tuple[str, str]:
    return (
        "Laundry Day Reminder 🧺",
        f"Hi {student_name}, today ({slot_date.strftime('%d %b')}) is your scheduled laundry day. "
        "Drop your bag at the collection counter.",
    )


def uncollected_warning(student_name: str) -> tuple[str, str]:
    return (
        "Collect Your Laundry ⏰",
        f"Hi {student_name}, your laundry is still waiting to be collected. "
        "Please pick it up before midnight to avoid it being marked missed.",
    )


def slot_missed(student_name: str, slot_date: DateType) -> tuple[str, str]:
    return (
        "Slot Missed",
        f"Hi {student_name}, your laundry slot on {slot_date.strftime('%d %b %Y')} "
        "was marked as missed because no bag was dropped off.",
    )


def slot_cancelled(student_name: str, slot_date: DateType) -> tuple[str, str]:
    return (
        "Slot Cancelled",
        f"Hi {student_name}, your laundry slot on {slot_date.strftime('%d %b %Y')} "
        "has been cancelled successfully.",
    )


DELAY_REASON_LABELS = {
    "power_cut": "power cut",
    "water_shortage": "water shortage",
    "machine_repair": "machine under repair",
    "too_many_clothes": "high volume of clothes",
    "staff_shortage": "staff shortage",
}