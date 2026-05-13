"""
test_admin.py — /admin endpoints.

Covers:
  - Analytics: overview, slots (with by_block), bags, notifications
  - Student listing and deactivation
  - Staff listing and deactivation
  - Role guards (students and staff cannot access admin routes)
"""
import pytest
from datetime import date, timedelta
from conftest import _headers, _register_student, _login, _register_staff

TODAY = date.today().isoformat()
THIS_MONTH_START = date.today().replace(day=1).isoformat()
THIS_MONTH_END = (date.today() + timedelta(days=30)).isoformat()


# ── Role guards ───────────────────────────────────────────────────────────

def test_student_cannot_access_admin_analytics(client, student_a):
    token, _ = student_a
    resp = client.get("/admin/analytics/overview", headers=_headers(token))
    assert resp.status_code == 403


def test_staff_cannot_access_admin_analytics(client, staff_token):
    resp = client.get("/admin/analytics/overview", headers=_headers(staff_token))
    assert resp.status_code == 403


# ── Overview ──────────────────────────────────────────────────────────────

def test_overview_structure(client, admin_token):
    resp = client.get("/admin/analytics/overview", headers=_headers(admin_token))
    assert resp.status_code == 200
    body = resp.json()
    for key in ("active_students", "active_staff", "slots_booked_today",
                "bags_in_flight", "block_usage_today"):
        assert key in body


def test_overview_block_usage_today_has_all_blocks(client, admin_token):
    resp = client.get("/admin/analytics/overview", headers=_headers(admin_token))
    usage = resp.json()["block_usage_today"]
    for block in ("A", "B", "C", "D", "E"):
        assert block in usage
        assert "booked" in usage[block]
        assert "limit" in usage[block]


def test_overview_reflects_booking(client, admin_token, student_a):
    token, _ = student_a
    before = client.get("/admin/analytics/overview", headers=_headers(admin_token)).json()
    before_count = before["slots_booked_today"]
    before_block_a = before["block_usage_today"]["A"]["booked"]

    client.post("/slots/book", headers=_headers(token), json={"date": TODAY})

    after = client.get("/admin/analytics/overview", headers=_headers(admin_token)).json()
    assert after["slots_booked_today"] == before_count + 1
    assert after["block_usage_today"]["A"]["booked"] == before_block_a + 1
    # Block B should be unchanged
    assert after["block_usage_today"]["B"]["booked"] == before["block_usage_today"]["B"]["booked"]


# ── Slot analytics ────────────────────────────────────────────────────────

def test_slot_analytics_structure(client, admin_token):
    resp = client.get(
        f"/admin/analytics/slots?from_date={THIS_MONTH_START}&to_date={THIS_MONTH_END}",
        headers=_headers(admin_token),
    )
    assert resp.status_code == 200
    body = resp.json()
    for key in ("from_date", "to_date", "total_booked", "used",
                "cancelled", "missed", "utilisation_rate", "by_block"):
        assert key in body


def test_slot_analytics_by_block_has_all_blocks(client, admin_token):
    resp = client.get(
        f"/admin/analytics/slots?from_date={THIS_MONTH_START}&to_date={THIS_MONTH_END}",
        headers=_headers(admin_token),
    )
    by_block = resp.json()["by_block"]
    for block in ("A", "B", "C", "D", "E"):
        assert block in by_block
        assert "limit_per_day" in by_block[block]
        assert "total_booked" in by_block[block]
        assert "used" in by_block[block]


def test_slot_analytics_counts_by_block(client, admin_token, student_a, student_b):
    token_a, _ = student_a
    token_b, _ = student_b
    client.post("/slots/book", headers=_headers(token_a), json={"date": TODAY})
    client.post("/slots/book", headers=_headers(token_b), json={"date": TODAY})

    resp = client.get(
        f"/admin/analytics/slots?from_date={TODAY}&to_date={TODAY}",
        headers=_headers(admin_token),
    )
    by_block = resp.json()["by_block"]
    assert by_block["A"]["total_booked"] >= 1
    assert by_block["B"]["total_booked"] >= 1


def test_slot_analytics_missing_params(client, admin_token):
    resp = client.get("/admin/analytics/slots", headers=_headers(admin_token))
    assert resp.status_code == 422


# ── Bag analytics ─────────────────────────────────────────────────────────

def test_bag_analytics(client, admin_token):
    resp = client.get("/admin/analytics/bags", headers=_headers(admin_token))
    assert resp.status_code == 200
    body = resp.json()
    for status in ("pending", "dropped", "washing", "ready", "collected", "missed"):
        assert status in body
        assert isinstance(body[status], int)


# ── Notification analytics ────────────────────────────────────────────────

def test_notification_analytics(client, admin_token):
    resp = client.get(
        f"/admin/analytics/notifications?from_date={THIS_MONTH_START}&to_date={THIS_MONTH_END}",
        headers=_headers(admin_token),
    )
    assert resp.status_code == 200
    body = resp.json()
    for key in ("total_sent", "fcm_success", "fcm_failure", "success_rate", "by_event_type"):
        assert key in body


# ── Student management ────────────────────────────────────────────────────

def test_list_students(client, admin_token, student_a):
    resp = client.get("/admin/students?active_only=true&page=1&page_size=50",
                      headers=_headers(admin_token))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


def test_list_students_pagination(client, admin_token):
    # Register 3 extra students
    for i in range(3):
        _register_student(client, f"22PG00{i}", f"Page {i}", f"page{i}@vit.ac.in", "E")
    resp = client.get("/admin/students?page=1&page_size=2", headers=_headers(admin_token))
    assert resp.status_code == 200
    assert len(resp.json()) <= 2


def test_deactivate_staff_member(client, admin_token):
    _register_staff(client, "DEACT_SF", "Deact Staff", "staff")
    from conftest import _login as login
    sf_token = login(client, "DEACT_SF", "staffpass", "staff")
    # Get staff id via admin list
    all_staff = client.get("/admin/staff?active_only=true", headers=_headers(admin_token)).json()
    sf = next((s for s in all_staff if s["employee_id"] == "DEACT_SF"), None)
    assert sf is not None
    resp = client.patch(f"/admin/staff/{sf['id']}/deactivate", headers=_headers(admin_token))
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False
    # Staff's token should now be rejected
    resp2 = client.get("/staff/today", headers=_headers(sf_token))
    assert resp2.status_code == 401


def test_deactivate_nonexistent_staff(client, admin_token):
    resp = client.patch(
        "/admin/staff/00000000-0000-0000-0000-000000000000/deactivate",
        headers=_headers(admin_token),
    )
    assert resp.status_code == 404


def test_list_staff(client, admin_token, staff_token):
    resp = client.get("/admin/staff", headers=_headers(admin_token))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)