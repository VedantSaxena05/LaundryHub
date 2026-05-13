"""
test_rfid_bags.py — /devices, /rfid, and /bags endpoints.

Covers:
  - Device registration, listing, deactivation
  - RFID tag linking (success, duplicate guard)
  - Full bag lifecycle: pending → dropped → ready → collected
  - Time-window guards: dropoff only 10–14, collection only 14–18
  - Unknown tag scan is accepted but produces no state change
  - Bag status log
  - Role guards
"""
import pytest
from datetime import date
from conftest import _headers, _register_student, _login

TODAY = date.today().isoformat()


# ── Helpers ───────────────────────────────────────────────────────────────

def _book(client, token, d=TODAY):
    return client.post("/slots/book", headers=_headers(token), json={"date": d})


def _scan(client, staff_token, tag_uid, device_id, scan_type):
    return client.post("/rfid/scan", headers=_headers(staff_token), json={
        "tag_uid": tag_uid,
        "device_id": device_id,
        "scan_type": scan_type,
    })


def _link(client, staff_token, tag_uid, student_id):
    return client.post("/rfid/link", headers=_headers(staff_token), json={
        "tag_uid": tag_uid,
        "student_id": student_id,
    })


# ── Devices ───────────────────────────────────────────────────────────────

def test_register_device(client, admin_token):
    resp = client.post("/devices", headers=_headers(admin_token), json={
        "device_name": "Dropoff Scanner",
        "location_tag": "dropoff",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["device_name"] == "Dropoff Scanner"
    assert body["is_active"] is True


def test_list_devices(client, admin_token, staff_token, device):
    resp = client.get("/devices", headers=_headers(staff_token))
    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()]
    assert device in ids


def test_student_cannot_register_device(client, student_a):
    token, _ = student_a
    resp = client.post("/devices", headers=_headers(token), json={
        "device_name": "Hacked",
        "location_tag": "dropoff",
    })
    assert resp.status_code == 403


def test_staff_cannot_register_device(client, staff_token):
    resp = client.post("/devices", headers=_headers(staff_token), json={
        "device_name": "Hacked",
        "location_tag": "dropoff",
    })
    assert resp.status_code == 403


def test_deactivate_device(client, admin_token):
    dev_id = client.post("/devices", headers=_headers(admin_token), json={
        "device_name": "To Deactivate",
        "location_tag": "dropoff",
    }).json()["id"]
    resp = client.delete(f"/devices/{dev_id}", headers=_headers(admin_token))
    assert resp.status_code == 204


# ── RFID tag linking ──────────────────────────────────────────────────────

def test_link_tag_to_student(client, staff_token, student_a):
    _, sid = student_a
    resp = _link(client, staff_token, "TAGA001", sid)
    assert resp.status_code == 201
    assert resp.json()["tag_uid"] == "TAGA001"
    assert resp.json()["student_id"] == sid


def test_link_same_tag_to_different_student_fails(client, staff_token, student_a, student_b):
    _, sid_a = student_a
    _, sid_b = student_b
    _link(client, staff_token, "SHARED01", sid_a)
    resp = _link(client, staff_token, "SHARED01", sid_b)
    assert resp.status_code == 400


def test_student_cannot_link_tag(client, student_a):
    token, sid = student_a
    resp = client.post("/rfid/link", headers=_headers(token), json={
        "tag_uid": "STUTAG", "student_id": sid,
    })
    assert resp.status_code == 403


def test_list_tags(client, staff_token, student_a):
    _, sid = student_a
    _link(client, staff_token, "LISTTAG", sid)
    resp = client.get("/rfid/tags", headers=_headers(staff_token))
    assert resp.status_code == 200
    uids = [t["tag_uid"] for t in resp.json()]
    assert "LISTTAG" in uids


# ── Scan state machine ────────────────────────────────────────────────────

def test_full_bag_lifecycle(client, staff_token, student_a, device, dropoff_open, collection_open):
    token, sid = student_a
    _book(client, token)
    _link(client, staff_token, "FULL001", sid)

    # dropoff → bag created, status = dropped
    r1 = _scan(client, staff_token, "FULL001", device, "dropoff")
    assert r1.status_code == 200

    bag_status = client.get("/bags/my", headers=_headers(token)).json()["status"]
    assert bag_status == "dropped"

    # ready scan
    r2 = _scan(client, staff_token, "FULL001", device, "ready")
    assert r2.status_code == 200
    assert client.get("/bags/my", headers=_headers(token)).json()["status"] == "ready"

    # collected scan
    r3 = _scan(client, staff_token, "FULL001", device, "collected")
    assert r3.status_code == 200

    # After collection the bag is gone from /bags/my (collected)
    r4 = client.get("/bags/my", headers=_headers(token))
    assert r4.status_code == 404


def test_dropoff_scan_blocked_outside_window(client, staff_token, student_a, device, dropoff_closed):
    token, sid = student_a
    _book(client, token)
    _link(client, staff_token, "CLOSED01", sid)
    resp = _scan(client, staff_token, "CLOSED01", device, "dropoff")
    assert resp.status_code == 400
    assert "10:00" in resp.json()["detail"]


def test_collection_scan_blocked_outside_window(
    client, staff_token, student_a, device, dropoff_open, collection_closed
):
    token, sid = student_a
    _book(client, token)
    _link(client, staff_token, "NOCOL01", sid)
    _scan(client, staff_token, "NOCOL01", device, "dropoff")
    _scan(client, staff_token, "NOCOL01", device, "ready")
    resp = _scan(client, staff_token, "NOCOL01", device, "collected")
    assert resp.status_code == 400
    assert "14:00" in resp.json()["detail"]


def test_ready_scan_has_no_time_restriction(
    client, staff_token, student_a, device, dropoff_open, collection_closed
):
    """Ready scan should succeed regardless of time window."""
    token, sid = student_a
    _book(client, token)
    _link(client, staff_token, "READY01", sid)
    _scan(client, staff_token, "READY01", device, "dropoff")
    resp = _scan(client, staff_token, "READY01", device, "ready")
    assert resp.status_code == 200


def test_scan_unknown_tag_returns_200_no_state_change(
    client, staff_token, device, dropoff_open
):
    """Unknown tag must be logged but not crash; returns 200."""
    resp = _scan(client, staff_token, "UNKNOWN99", device, "dropoff")
    assert resp.status_code == 200


def test_scan_wrong_order_ignored(client, staff_token, student_a, device, dropoff_open):
    """Trying to do 'ready' before 'dropoff' should be a no-op (200, no crash)."""
    token, sid = student_a
    _book(client, token)
    _link(client, staff_token, "ORDER01", sid)
    # Skip dropoff, go straight to ready — bag is still pending
    resp = _scan(client, staff_token, "ORDER01", device, "ready")
    assert resp.status_code == 200
    # Bag status unchanged (still no active bag → 404)
    r = client.get("/bags/my", headers=_headers(token))
    assert r.status_code == 404


def test_scan_inactive_device_returns_404(client, staff_token, student_a, admin_token, dropoff_open):
    token, sid = student_a
    _book(client, token)
    # Register and immediately deactivate a device
    dev = client.post("/devices", headers=_headers(admin_token), json={
        "device_name": "Inactive",
        "location_tag": "dropoff",
    }).json()["id"]
    client.delete(f"/devices/{dev}", headers=_headers(admin_token))
    _link(client, staff_token, "INACT01", sid)
    resp = _scan(client, staff_token, "INACT01", dev, "dropoff")
    assert resp.status_code == 404


# ── Bags ──────────────────────────────────────────────────────────────────

def test_bag_history(client, staff_token, student_a, device, dropoff_open):
    token, sid = student_a
    _book(client, token)
    _link(client, staff_token, "HIST001", sid)
    _scan(client, staff_token, "HIST001", device, "dropoff")
    resp = client.get("/bags/my/history", headers=_headers(token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_bag_status_log(client, staff_token, student_a, device, dropoff_open):
    token, sid = student_a
    _book(client, token)
    _link(client, staff_token, "LOG001", sid)
    _scan(client, staff_token, "LOG001", device, "dropoff")
    bags = client.get("/bags/my/history", headers=_headers(token)).json()
    bag_id = bags[0]["id"]
    resp = client.get(f"/bags/{bag_id}/logs", headers=_headers(token))
    assert resp.status_code == 200
    logs = resp.json()
    assert any(l["to_status"] == "dropped" for l in logs)


def test_student_cannot_view_another_bag_log(
    client, staff_token, student_a, student_b, device, dropoff_open
):
    token_a, sid_a = student_a
    token_b, sid_b = student_b
    _book(client, token_b)
    _link(client, staff_token, "PRIVTAG", sid_b)
    _scan(client, staff_token, "PRIVTAG", device, "dropoff")
    bags_b = client.get("/bags/my/history", headers=_headers(token_b)).json()
    bag_id_b = bags_b[0]["id"]
    # Student A tries to read Student B's log
    resp = client.get(f"/bags/{bag_id_b}/logs", headers=_headers(token_a))
    assert resp.status_code == 403


def test_staff_can_view_any_student_bags(client, staff_token, student_a, device, dropoff_open):
    token, sid = student_a
    _book(client, token)
    _link(client, staff_token, "STFBAG", sid)
    _scan(client, staff_token, "STFBAG", device, "dropoff")
    resp = client.get(f"/bags/student/{sid}", headers=_headers(staff_token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_scan_audit_log(client, staff_token, student_a, device, dropoff_open):
    token, sid = student_a
    _book(client, token)
    _link(client, staff_token, "AUDIT01", sid)
    _scan(client, staff_token, "AUDIT01", device, "dropoff")
    resp = client.get("/rfid/scan-log?limit=10", headers=_headers(staff_token))
    assert resp.status_code == 200
    uids = [e["tag_uid"] for e in resp.json()]
    assert "AUDIT01" in uids