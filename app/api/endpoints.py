from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from app.core.config import settings
from app.services.scanner import ScannerService
from app.models.device import Device, DeviceCount
from app.models.manufacturer import ManufacturerData
from app.core.dependencies import get_scanner_service
from app.core.constants import DEFAULT_SCAN_INTERVAL

router = APIRouter()

@router.get("/devices", response_model=List[Device])
async def get_devices(
    scanner_service: ScannerService = Depends(get_scanner_service)
) -> List[Device]:
    """Get all currently detected BLE devices."""
    try:
        return await scanner_service.get_devices()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/count", response_model=DeviceCount)
async def get_device_count(
    scanner_service: ScannerService = Depends(get_scanner_service)
) -> DeviceCount:
    """Get the current count of detected BLE devices."""
    try:
        return await scanner_service.get_device_count()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/manufacturers", response_model=List[ManufacturerData])
async def get_manufacturer_data(
    scanner_service: ScannerService = Depends(get_scanner_service)
) -> List[ManufacturerData]:
    """Get manufacturer data for detected devices."""
    try:
        return await scanner_service.get_manufacturer_data()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scan")
async def start_scan(
    scanner_service: ScannerService = Depends(get_scanner_service)
) -> Dict[str, Any]:
    """Start a new BLE device scan."""
    try:
        await scanner_service.start_scan(interval=DEFAULT_SCAN_INTERVAL)
        return {"status": "scanning", "interval": DEFAULT_SCAN_INTERVAL}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/scan")
async def stop_scan(
    scanner_service: ScannerService = Depends(get_scanner_service)
) -> Dict[str, Any]:
    """Stop the current BLE device scan."""
    try:
        await scanner_service.stop_scan()
        return {"status": "stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))