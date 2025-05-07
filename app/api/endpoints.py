from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.core.constants import DEFAULT_SCAN_INTERVAL
from app.core.dependencies import get_scanner_service
from app.models.device import Device, DeviceCount
from app.models.manufacturer import ManufacturerData
from app.services.scanner import ScannerService

router = APIRouter()

# Move Depends to module level to avoid B008
scanner_dependency = Depends(get_scanner_service)

@router.get("/devices", response_model=list[Device])
async def get_devices(
    scanner_service: ScannerService = scanner_dependency
) -> list[Device]:
    """Get all currently detected BLE devices."""
    try:
        return await scanner_service.get_devices()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/count", response_model=DeviceCount)
async def get_device_count(
    scanner_service: ScannerService = scanner_dependency
) -> DeviceCount:
    """Get the current count of detected BLE devices."""
    try:
        return await scanner_service.get_device_count()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/manufacturers", response_model=list[ManufacturerData])
async def get_manufacturer_data(
    scanner_service: ScannerService = scanner_dependency
) -> list[ManufacturerData]:
    """Get manufacturer data for detected devices."""
    try:
        return await scanner_service.get_manufacturer_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/scan")
async def start_scan(
    scanner_service: ScannerService = scanner_dependency
) -> dict[str, Any]:
    """Start a new BLE device scan."""
    try:
        await scanner_service.start_scan(interval=DEFAULT_SCAN_INTERVAL)
        return {"status": "scanning", "interval": DEFAULT_SCAN_INTERVAL}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.delete("/scan")
async def stop_scan(
    scanner_service: ScannerService = scanner_dependency
) -> dict[str, Any]:
    """Stop the current BLE device scan."""
    try:
        await scanner_service.stop_scan()
        return {"status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e