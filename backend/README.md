# Running the Test Suite

## 1. Install test dependencies (once)

```powershell
pip install pytest httpx pytest-asyncio
```

> All other dependencies (`fastapi`, `sqlalchemy`, `python-jose`, etc.) should
> already be installed from `requirements.txt`.

## 2. Copy files into your project

Place ALL files from this folder inside your project's `tests/` directory,
**replacing** the existing `conftest.py`:

```
laundry-backend/
├── tests/
│   ├── conftest.py          ← replace existing
│   ├── test_auth.py
│   ├── test_students.py
│   ├── test_slots.py
│   ├── test_staff.py
│   ├── test_rfid_bags.py
│   ├── test_admin.py
│   └── test_forum_lostfound.py
└── pytest.ini               ← place in project root
```

## 3. Run the full suite

```powershell
# From the project root (laundry-backend/)
pytest tests/ -v
```

Run a single file:
```powershell
pytest tests/test_slots.py -v
```

Run a single test:
```powershell
pytest tests/test_slots.py::test_block_limit_rejects_when_full -v
```

Stop on first failure:
```powershell
pytest tests/ -x
```

## 4. What is tested

| File | Coverage |
|------|----------|
| `test_auth.py` | Register (student/staff/admin), login, token refresh, duplicate guards, invalid inputs |
| `test_students.py` | Profile get/update, admin lookup, deactivation, role guards |
| `test_slots.py` | Availability (all blocks / single block), per-block limits, booking, cancellation, blocked dates, monthly quota, admin limit management |
| `test_staff.py` | Delay reports, blocked dates CRUD, today summary, role guards, confirms schedule endpoint removed |
| `test_rfid_bags.py` | Device registration, tag linking, full bag lifecycle (pending→dropped→ready→collected), drop-off window guard (10–14), collection window guard (14–18), unknown tag, wrong scan order, bag logs, ownership guards |
| `test_admin.py` | Overview (block_usage_today), slot analytics (by_block), bag counts, notification stats, student/staff listing and deactivation |
| `test_forum_lostfound.py` | Forum post/list/upvote/reply/pin, anonymous posts, lost & found create/list/match/resolve, ownership guards |

## 5. Key design decisions

* **In-memory SQLite** — no Postgres needed; each test gets a fresh rolled-back session.
* **Time-window fixtures** — `dropoff_open`, `dropoff_closed`, `collection_open`, `collection_closed` fixtures in `conftest.py` let individual tests toggle time windows without touching the clock.
* **APScheduler patched** — background jobs never fire during tests.
* **No `@pytest.mark.asyncio`** — tests use `TestClient` (synchronous), so no async configuration is needed.