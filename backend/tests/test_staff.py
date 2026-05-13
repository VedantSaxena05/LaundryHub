"""
test_staff.py — /staff endpoints.

Covers:
  - Delay reports (create, list)
  - Blocked dates (add, list, remove, duplicate guard)
  - Booking on a blocked date rejected
  - Today's ops summary
  - Floor-schedule endpoint is gone (404/405)
  - Role guards
"""
import pytest
from datetime import date, timedelta
from conftest import _headers

TODAY = date.today().isoformat()
FUTURE = (date.today() + timedelta(days=7)).isoformat()


# ── Delay reports ─────────────────────────────────────────────────────────

def test_report_delay(client, staff_token):
    resp = client.post("/staff/delays", headers=_headers(staff_token), json={
        "reason": "machine_repair",
        "affected_date": TODAY,
        "note": "Drum 2 broken",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["reason"] == "machine_repair"
    assert body["affected_date"] == TODAY
    assert "notification_sent" in body


def test_list_delays(client, staff_token):
    client.post("/staff/delays", headers=_headers(staff_token), json={
        "reason": "water_shortage",
        "affected_date": TODAY,
    })
    resp = client.get("/staff/delays", headers=_headers(staff_token))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


def test_student_cannot_report_delay(client, student_a):
    token, _ = student_a
    resp = client.post("/staff/delays", headers=_headers(token), json={
        "reason": "staff_shortage",
        "affected_date": TODAY,
    })
    assert resp.status_code == 403


def test_delay_notification_sent_when_slots_exist(client, staff_token, student_a):
    """notification_sent should be True when students have slots on that date."""
    token, _ = student_a
    client.post("/slots/book", headers=_headers(token), json={"date": TODAY})
    resp = client.post("/staff/delays", headers=_headers(staff_token), json={
        "reason": "power_cut",
        "affected_date": TODAY,
    })
    assert resp.status_code == 201
    # notification_sent = True because at least one student has a slot today
    assert resp.json()["notification_sent"] is True


def test_delay_notification_not_sent_when_no_slots(client, staff_token):
    """notification_sent should be False when no slots exist on that date."""
    future = (date.today() + timedelta(days=30)).isoformat()
    resp = client.post("/staff/delays", headers=_headers(staff_token), json={
        "reason": "power_cut",
        "affected_date": future,
    })
    assert resp.status_code == 201
    assert resp.json()["notification_sent"] is False


# ── Blocked dates ─────────────────────────────────────────────────────────

def test_add_blocked_date(client, staff_token):
    resp = client.post("/staff/blocked-dates", headers=_headers(staff_token), json={
        "date": FUTURE,
        "reason": "National holiday",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["date"] == FUTURE
    assert body["reason"] == "National holiday"


def test_duplicate_blocked_date_returns_409(client, staff_token):
    client.post("/staff/blocked-dates", headers=_headers(staff_token), json={
        "date": FUTURE,
        "reason": "First block",
    })
    resp = client.post("/staff/blocked-dates", headers=_headers(staff_token), json={
        "date": FUTURE,
        "reason": "Duplicate",
    })
    assert resp.status_code == 409


def test_list_blocked_dates(client, staff_token):
    client.post("/staff/blocked-dates", headers=_headers(staff_token), json={
        "date": FUTURE,
        "reason": "Test",
    })
    resp = client.get("/staff/blocked-dates", headers=_headers(staff_token))
    assert resp.status_code == 200
    assert any(b["date"] == FUTURE for b in resp.json())


def test_remove_blocked_date_admin_only(client, staff_token, admin_token):
    client.post("/staff/blocked-dates", headers=_headers(staff_token), json={
        "date": FUTURE,
        "reason": "To remove",
    })
    # Staff cannot remove
    resp_staff = client.delete(f"/staff/blocked-dates/{FUTURE}", headers=_headers(staff_token))
    assert resp_staff.status_code == 403
    # Admin can remove
    resp_admin = client.delete(f"/staff/blocked-dates/{FUTURE}", headers=_headers(admin_token))
    assert resp_admin.status_code == 204


def test_remove_nonexistent_blocked_date(client, admin_token):
    resp = client.delete("/staff/blocked-dates/2099-01-01", headers=_headers(admin_token))
    assert resp.status_code == 404


def test_remove_blocked_date_invalid_format(client, admin_token):
    resp = client.delete("/staff/blocked-dates/not-a-date", headers=_headers(admin_token))
    assert resp.status_code == 400


def test_booking_rejected_on_blocked_date(client, student_a, staff_token):
    token, _ = student_a
    client.post("/staff/blocked-dates", headers=_headers(staff_token), json={
        "date": FUTURE,
        "reason": "Blocked for test",
    })
    resp = client.post("/slots/book", headers=_headers(token), json={"date": FUTURE})
    assert resp.status_code == 400


def test_student_cannot_add_blocked_date(client, student_a):
    token, _ = student_a
    resp = client.post("/staff/blocked-dates", headers=_headers(token), json={
        "date": FUTURE,
        "reason": "Student trying",
    })
    assert resp.status_code == 403


# ── Today's ops snapshot ─────────────────────────────────────────────────

def test_today_summary(client, staff_token):
    resp = client.get("/staff/today", headers=_headers(staff_token))
    assert resp.status_code == 200
    body = resp.json()
    for key in ("date", "total_booked", "bags_dropped", "bags_ready", "bags_collected"):
        assert key in body


def test_student_cannot_access_today_summary(client, student_a):
    token, _ = student_a
    resp = client.get("/staff/today", headers=_headers(token))
    assert resp.status_code == 403


# ── Schedule endpoint is gone ─────────────────────────────────────────────

def test_floor_schedule_endpoint_does_not_exist(client, staff_token):
    """PUT /staff/schedules must no longer exist (removed in refactor)."""
    resp = client.put("/staff/schedules", headers=_headers(staff_token), json={
        "block": "A",
        "floor": 1,
        "day_of_week": 0,
        "is_active": True,
    })
    assert resp.status_code in (404, 405)


def test_floor_schedule_list_does_not_exist(client, staff_token):
    resp = client.get("/staff/schedules", headers=_headers(staff_token))
    assert resp.status_code in (404, 405)