"""
test_auth.py — Auth endpoints: register, login, refresh.
"""
import pytest
from conftest import _headers, _register_student, _register_staff, _login


# ── Student registration ──────────────────────────────────────────────────

def test_register_student_success(client):
    resp = client.post("/auth/register/student", json={
        "registration_number": "22BCE0001",
        "name": "Test Student",
        "email": "ts@vit.ac.in",
        "phone_number": "9123456789",
        "password": "pass123",
        "block": "A",
        "floor": 2,
        "room_number": "A201",
        "language_preference": "en",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["role"] == "student"
    assert "access_token" in body
    assert "refresh_token" in body


def test_register_student_duplicate_email(client):
    _register_student(client, "22X001", "Dup A", "dup@vit.ac.in", "A")
    resp = client.post("/auth/register/student", json={
        "registration_number": "22X002",
        "name": "Dup B",
        "email": "dup@vit.ac.in",       # same email
        "phone_number": "9000000002",
        "password": "pass",
        "block": "B",
        "floor": 1,
        "room_number": "B101",
        "language_preference": "en",
    })
    assert resp.status_code == 409


def test_register_student_duplicate_reg_number(client):
    _register_student(client, "22DUPE01", "First", "first@vit.ac.in", "A")
    resp = client.post("/auth/register/student", json={
        "registration_number": "22DUPE01",  # same reg number
        "name": "Second",
        "email": "second@vit.ac.in",
        "phone_number": "9000000003",
        "password": "pass",
        "block": "B",
        "floor": 1,
        "room_number": "B101",
        "language_preference": "en",
    })
    assert resp.status_code == 409


def test_register_student_invalid_phone(client):
    resp = client.post("/auth/register/student", json={
        "registration_number": "22BCE9999",
        "name": "Bad Phone",
        "email": "bp@vit.ac.in",
        "phone_number": "123",          # too short
        "password": "pass",
        "block": "A",
        "floor": 1,
        "room_number": "A101",
        "language_preference": "en",
    })
    assert resp.status_code == 422


def test_register_student_invalid_language(client):
    resp = client.post("/auth/register/student", json={
        "registration_number": "22BCE8888",
        "name": "Bad Lang",
        "email": "bl@vit.ac.in",
        "phone_number": "9000000099",
        "password": "pass",
        "block": "A",
        "floor": 1,
        "room_number": "A101",
        "language_preference": "fr",    # unsupported
    })
    assert resp.status_code == 422


# ── Staff registration ────────────────────────────────────────────────────

def test_register_staff_success(client):
    resp = client.post("/auth/register/staff", json={
        "name": "Ravi",
        "employee_id": "EMP500",
        "phone_number": "9000000050",
        "password": "staffpass",
        "role": "staff",
    })
    assert resp.status_code == 201
    assert resp.json()["role"] == "staff"


def test_register_admin_success(client):
    resp = client.post("/auth/register/staff", json={
        "name": "Admin",
        "employee_id": "ADM500",
        "phone_number": "9000000051",
        "password": "adminpass",
        "role": "admin",
    })
    assert resp.status_code == 201
    assert resp.json()["role"] == "admin"


def test_register_staff_duplicate_employee_id(client):
    _register_staff(client, "EMP_DUP", "First Staff")
    resp = client.post("/auth/register/staff", json={
        "name": "Second Staff",
        "employee_id": "EMP_DUP",
        "phone_number": "9000000052",
        "password": "pass",
        "role": "staff",
    })
    assert resp.status_code == 409


def test_register_staff_invalid_role(client):
    resp = client.post("/auth/register/staff", json={
        "name": "Bad Role",
        "employee_id": "EMP_BR",
        "phone_number": "9000000053",
        "password": "pass",
        "role": "superuser",            # not allowed
    })
    assert resp.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────

def test_student_login_success(client):
    _register_student(client, "22LOGIN1", "Login A", "logina@vit.ac.in", "A")
    resp = client.post("/auth/login", json={
        "identifier": "logina@vit.ac.in",
        "password": "testpass",
        "role": "student",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "student"
    assert body["token_type"] == "bearer"


def test_student_login_wrong_password(client):
    _register_student(client, "22LOGIN2", "Login B", "loginb@vit.ac.in", "B")
    resp = client.post("/auth/login", json={
        "identifier": "loginb@vit.ac.in",
        "password": "wrongpass",
        "role": "student",
    })
    assert resp.status_code == 401


def test_student_login_unknown_email(client):
    resp = client.post("/auth/login", json={
        "identifier": "nobody@vit.ac.in",
        "password": "pass",
        "role": "student",
    })
    assert resp.status_code == 401


def test_staff_login_success(client):
    _register_staff(client, "EMP_LOG", "Log Staff")
    resp = client.post("/auth/login", json={
        "identifier": "EMP_LOG",
        "password": "staffpass",
        "role": "staff",
    })
    assert resp.status_code == 200
    assert resp.json()["role"] == "staff"


# ── Token refresh ─────────────────────────────────────────────────────────

def test_refresh_token(client):
    r = _register_student(client, "22RFRSH", "Refresh", "refresh@vit.ac.in", "C")
    refresh = r["refresh_token"]
    resp = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_refresh_with_invalid_token(client):
    resp = client.post("/auth/refresh", json={"refresh_token": "garbage.token.here"})
    assert resp.status_code == 401


# ── Protected endpoint without token ─────────────────────────────────────

def test_no_token_returns_401(client):
    resp = client.get("/students/me")
    assert resp.status_code == 403  # HTTPBearer returns 403 when no credentials