"""
Tamil notification templates.
Each function returns (title, body).
"""
from datetime import date as DateType


def bag_received(student_name: str) -> tuple[str, str]:
    return (
        "பை பெறப்பட்டது ✅",
        f"வணக்கம் {student_name}, உங்கள் துணி பை சலவை ஊழியர்களால் பெறப்பட்டது.",
    )


def bag_ready(student_name: str) -> tuple[str, str]:
    return (
        "சலவை தயார் 👕",
        f"வணக்கம் {student_name}, உங்கள் துணிகள் துவைக்கப்பட்டு எடுத்துச் செல்ல தயாராக உள்ளன!",
    )


def delay(reason_label: str, affected_date: DateType) -> tuple[str, str]:
    return (
        "சலவை தாமதம் ⚠️",
        f"{affected_date.strftime('%d %b %Y')} அன்று {reason_label} காரணமாக "
        "சலவை சேவையில் தாமதம் ஏற்படும். மன்னிப்பை கோருகிறோம்.",
    )


def morning_reminder(student_name: str, slot_date: DateType) -> tuple[str, str]:
    return (
        "சலவை நாள் நினைவூட்டல் 🧺",
        f"வணக்கம் {student_name}, இன்று ({slot_date.strftime('%d %b')}) உங்கள் "
        "சலவை நாள். பையை சேகரிப்பு மையத்தில் கொண்டு வாருங்கள்.",
    )


def uncollected_warning(student_name: str) -> tuple[str, str]:
    return (
        "உங்கள் சலவையை எடுத்துச் செல்லுங்கள் ⏰",
        f"வணக்கம் {student_name}, உங்கள் துணிகள் இன்னும் எடுக்கப்படவில்லை. "
        "இன்று நள்ளிரவிற்கு முன் எடுத்துச் செல்லுங்கள்.",
    )


def slot_missed(student_name: str, slot_date: DateType) -> tuple[str, str]:
    return (
        "ஸ்லாட் தவறவிட்டது",
        f"வணக்கம் {student_name}, {slot_date.strftime('%d %b %Y')} அன்றைய உங்கள் "
        "சலவை ஸ்லாட் தவறவிட்டதாக குறிக்கப்பட்டது.",
    )


def slot_cancelled(student_name: str, slot_date: DateType) -> tuple[str, str]:
    return (
        "ஸ்லாட் ரத்து செய்யப்பட்டது",
        f"வணக்கம் {student_name}, {slot_date.strftime('%d %b %Y')} அன்றைய உங்கள் "
        "சலவை ஸ்லாட் வெற்றிகரமாக ரத்து செய்யப்பட்டது.",
    )


DELAY_REASON_LABELS = {
    "power_cut": "மின்சார தடை",
    "water_shortage": "தண்ணீர் பற்றாக்குறை",
    "machine_repair": "இயந்திரம் பழுது பார்க்கப்படுகிறது",
    "too_many_clothes": "அதிக துணிகள்",
    "staff_shortage": "ஊழியர் பற்றாக்குறை",
}