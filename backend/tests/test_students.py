"""
test_students.py — /students endpoints.
"""
import pytest
from conftest import _headers, _register_student


def test_get_own_profile(client, student_a):
    token, sid = student_a
    resp = client.get("/students/me", headers=_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == sid
    assert body["block"] == "A"
    assert body["email"] == "stuA@vit.ac.in"


def test_staff_cannot_call_students_me(client, staff_token):
    resp = client.get("/students/me", headers=_headers(staff_token))
    assert resp.status_code == 403


def test_update_profile(client, student_a):
    token, _ = student_a
    resp = client.patch("/students/me", headers=_headers(token), json={
        "room_number": "A999",
        "language_preference": "ta",
        "fcm_token": "fcm-abc-123",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["room_number"] == "A999"
    assert body["language_preference"] == "ta"


def test_update_profile_invalid_language(client, student_a):
    token, _ = student_a
    resp = client.patch("/students/me", headers=_headers(token), json={
        "language_preference": "jp",
    })
    assert resp.status_code == 422


def test_admin_can_lookup_student_by_id(client, student_a, admin_token):
    _, sid = student_a
    resp = client.get(f"/students/{sid}", headers=_headers(admin_token))
    assert resp.status_code == 200
    assert resp.json()["id"] == sid


def test_student_cannot_lookup_by_id(client, student_a, student_b):
    token_a, _ = student_a
    _, sid_b = student_b
    resp = client.get(f"/students/{sid_b}", headers=_headers(token_a))
    assert resp.status_code == 403


def test_admin_deactivate_student(client, admin_token):
    _register_student(client, "22DEACT", "Deact", "deact@vit.ac.in", "D")
    from conftest import _login, _headers as h
    t = _login(client, "deact@vit.ac.in", "testpass", "student")
    sid = client.get("/students/me", headers=h(t)).json()["id"]
    resp = client.delete(f"/students/{sid}", headers=_headers(admin_token))
    assert resp.status_code == 204
    # Deactivated student's token should now be rejected
    resp2 = client.get("/students/me", headers=_headers(t))
    assert resp2.status_code == 401


def test_admin_lookup_nonexistent_student(client, admin_token):
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = client.get(f"/students/{fake_id}", headers=_headers(admin_token))
    assert resp.status_code == 404