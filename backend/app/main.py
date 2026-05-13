from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base

from app.models import user, hostel, laundry, rfid, notification, forum, lost_found  # noqa: F401

app = FastAPI(
    title="VIT Laundry Management API",
    version="1.0.0",
    description="Backend for hostel laundry tracking, slot booking, RFID scanning, and notifications.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import auth, students, slots, bags, rfid as rfid_router  # noqa: E402
from app.routers import devices, staff, admin, forum as forum_router, lost_found as lf_router  # noqa: E402
from app.routers import notifications  # noqa: E402

app.include_router(auth.router,            prefix="/auth",          tags=["Auth"])
app.include_router(students.router,        prefix="/students",      tags=["Students"])
app.include_router(slots.router,           prefix="/slots",         tags=["Slots"])
app.include_router(bags.router,            prefix="/bags",          tags=["Bags"])
app.include_router(rfid_router.router,     prefix="/rfid",          tags=["RFID"])
app.include_router(devices.router,         prefix="/devices",       tags=["Devices"])
app.include_router(staff.router,           prefix="/staff",         tags=["Staff"])
app.include_router(admin.router,           prefix="/admin",         tags=["Admin"])
app.include_router(forum_router.router,    prefix="/forum",         tags=["Forum"])
app.include_router(lf_router.router,       prefix="/lost-found",    tags=["Lost & Found"])
app.include_router(notifications.router,   prefix="/notifications", tags=["Notifications"])


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "env": settings.APP_ENV}


@app.on_event("startup")
def startup_event():
    if settings.APP_ENV == "development":
        Base.metadata.create_all(bind=engine)