from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.schemas.rfid import DeviceRegisterRequest, DeviceResponse
from app.services import rfid_service
from app.utils.dependencies import require_staff, require_admin

router = APIRouter()


@router.post("", response_model=DeviceResponse, status_code=201)
def register_device(
    payload: DeviceRegisterRequest,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: register a new RFID reader device."""
    return rfid_service.register_device(db, payload, current_user.id)


@router.get("", response_model=List[DeviceResponse])
def list_devices(
    current_user=Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Staff/admin: list all registered devices."""
    return rfid_service.list_devices(db)


@router.get("/{device_id}", response_model=DeviceResponse)
def get_device(
    device_id: UUID,
    current_user=Depends(require_staff),
    db: Session = Depends(get_db),
):
    return rfid_service.get_device(db, device_id)


@router.delete("/{device_id}", status_code=204)
def deactivate_device(
    device_id: UUID,
    current_user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin: soft-delete a device."""
    rfid_service.deactivate_device(db, device_id)
