"""
conftest.py — shared fixtures for the entire test suite.

Strategy
--------
* Uses an in-memory SQLite database (no external Postgres required).
* Overrides FastAPI's `get_db` dependency so every test gets a fresh,
  rolled-back session — tests never pollute each other.
* Patches APScheduler so background jobs don't fire.
* Patches `app.services.slot_service.is_dropoff_open` and
  `app.services.slot_service.is_collection_open` to return True by default
  so time-window tests can toggle them explicitly.
* Provides pre-built fixtures: student_A (Block A), student_B (Block B),
  staff, admin, and a registered RFID device.

Run from the project root:
    pip install pytest httpx pytest-asyncio
    pytest tests/ -v
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# ── In-memory SQLite engine ───────────────────────────────────────────────
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# SQLite doesn't enforce FK constraints by default — enable them
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Patch scheduler + Firebase before importing the app ──────────────────
@pytest.fixture(autouse=True, scope="session")
def _patch_external():
    """
    Suppress APScheduler and firebase-admin so they don't need real
    connections during tests.
    """
    firebase_mock = MagicMock()
    with (
        patch("app.scheduler.jobs.start_scheduler", return_value=None),
        patch("app.scheduler.jobs.stop_scheduler", return_value=None),
        patch.dict("sys.modules", {"firebase_admin": firebase_mock,
                                   "firebase_admin.credentials": firebase_mock,
                                   "firebase_admin.messaging": firebase_mock}),
    ):
        yield


# ── Create tables once per session ───────────────────────────────────────
@pytest.fixture(autouse=True, scope="session")
def _create_tables(_patch_external):
    from app.database import Base
    # Import all models so Base knows about them
    import app.models.user          # noqa
    import app.models.hostel        # noqa
    import app.models.laundry       # noqa
    import app.models.rfid          # noqa
    import app.models.notification  # noqa
    import app.models.forum         # noqa
    import app.models.lost_found    # noqa
    import app.models.delay         # noqa
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ── Per-test DB session with automatic rollback ───────────────────────────
@pytest.fixture()
def db(_create_tables):
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# ── TestClient with DB override ───────────────────────────────────────────
@pytest.fixture()
def client(db):
    from app.main import app
    from app.database import get_db

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


# ── Time-window helpers ───────────────────────────────────────────────────
@pytest.fixture()
def dropoff_open(monkeypatch):
    """Force the drop-off window to be open."""
    monkeypatch.setattr("app.services.slot_service.is_dropoff_open", lambda *a: True)
    monkeypatch.setattr("app.services.bag_service.is_dropoff_open", lambda *a: True)


@pytest.fixture()
def dropoff_closed(monkeypatch):
    """Force the drop-off window to be closed."""
    monkeypatch.setattr("app.services.slot_service.is_dropoff_open", lambda *a: False)
    monkeypatch.setattr("app.services.bag_service.is_dropoff_open", lambda *a: False)


@pytest.fixture()
def collection_open(monkeypatch):
    """Force the collection window to be open."""
    monkeypatch.setattr("app.services.slot_service.is_collection_open", lambda *a: True)
    monkeypatch.setattr("app.services.bag_service.is_collection_open", lambda *a: True)


@pytest.fixture()
def collection_closed(monkeypatch):
    """Force the collection window to be closed."""
    monkeypatch.setattr("app.services.slot_service.is_collection_open", lambda *a: False)
    monkeypatch.setattr("app.services.bag_service.is_collection_open", lambda *a: False)


# ── Registration helpers ──────────────────────────────────────────────────
def _register_student(client, reg_num, name, email, block, floor="1", room="X101"):
    resp = client.post("/auth/register/student", json={
        "registration_number": reg_num,
        "name": name,
        "email": email,
        "phone_number": "9000000001",
        "password": "testpass",
        "block": block,
        "floor": int(floor),
        "room_number": room,
        "language_preference": "en",
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def _register_staff(client, emp_id, name, role="staff"):
    resp = client.post("/auth/register/staff", json={
        "name": name,
        "employee_id": emp_id,
        "phone_number": "9111111111",
        "password": "staffpass",
        "role": role,
    })
    assert resp.status_code == 201, resp.text
    return resp.json()


def _login(client, identifier, password, role):
    resp = client.post("/auth/login", json={
        "identifier": identifier,
        "password": password,
        "role": role,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


# ── Pre-built actor fixtures ──────────────────────────────────────────────
@pytest.fixture()
def student_a(client):
    """Registered + logged-in Block-A student. Returns (token, student_id)."""
    _register_student(client, "22A001", "Arjun A", "stuA@vit.ac.in", "A")
    token = _login(client, "stuA@vit.ac.in", "testpass", "student")
    sid = client.get("/students/me", headers=_headers(token)).json()["id"]
    return token, sid


@pytest.fixture()
def student_b(client):
    """Registered + logged-in Block-B student. Returns (token, student_id)."""
    _register_student(client, "22B001", "Priya B", "stuB@vit.ac.in", "B")
    token = _login(client, "stuB@vit.ac.in", "testpass", "student")
    sid = client.get("/students/me", headers=_headers(token)).json()["id"]
    return token, sid


@pytest.fixture()
def staff_token(client):
    _register_staff(client, "EMP001", "Ravi Staff", "staff")
    return _login(client, "EMP001", "staffpass", "staff")


@pytest.fixture()
def admin_token(client):
    _register_staff(client, "ADM001", "Admin User", "admin")
    return _login(client, "ADM001", "staffpass", "admin")


@pytest.fixture()
def device(client, admin_token):
    """Registered RFID device. Returns device_id string."""
    resp = client.post("/devices", json={
        "device_name": "Scanner-1",
        "location_tag": "dropoff",
    }, headers=_headers(admin_token))
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]