import asyncio
import hashlib
import logging
import subprocess
from collections import deque
from datetime import datetime, timedelta
from typing import Any

from bluepy.btle import DefaultDelegate, Scanner
from fastapi import FastAPI, HTTPException

from .core.constants import (
    APPLE_COMPANY_ID,
    APPLE_SERVICE_UUIDS,
    COMPLETE_16B_SERVICES,
    COMPLETE_LOCAL_NAME,
    DEVICE_CLASS,
    INCOMPLETE_16B_SERVICES,
    MANUFACTURER_DATA_TYPE,
    MAX_HISTORY_MINUTES,
    MAX_TIME_SERIES_MINUTES,
    SCAN_DURATION_SECONDS,
    SCAN_INTERVAL_SECONDS,
    SHORT_LOCAL_NAME,
)
from .manufacturers import get_manufacturer_from_device
from .models import ScanResult
from .persistence import DataPersistence
from .session import SessionManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScanDelegate(DefaultDelegate):
    """Delegate for handling BLE scan events."""
    def __init__(self) -> None:
        """Initialize the ScanDelegate."""
        DefaultDelegate.__init__(self)

class BackgroundScanner:
    """Manages the background BLE scanning task."""
    def __init__(self) -> None:
        """Initialize the BackgroundScanner."""
        self.task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the background scanning task."""
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(background_scan())

    async def stop(self) -> None:
        """Stop the background scanning task."""
        if self.task is not None and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

app = FastAPI(
    title="BLE Device Counter",
    description="A simple API to count BLE devices in proximity",
    version="1.0.0"
)

# Initialize data persistence and scanner
persistence = DataPersistence()
scanner = BackgroundScanner()

# Store last 24 hours of scan results (assuming scans every minute)
scan_history = deque(maxlen=MAX_HISTORY_MINUTES)

# Load existing history on startup
scan_history.extend(persistence.load_history())
logger.info(f"Loaded {len(scan_history)} historical scan results")

# Initialize session manager
session_manager = SessionManager()

def check_system_requirements() -> tuple[bool, str]:
    """
    Checks if the system meets the requirements for BLE scanning.
    Returns (success: bool, message: str)
    """
    try:
        # Check if BlueZ is installed
        result = subprocess.run(['bluetoothctl', '--version'],
                              capture_output=True,
                              text=True, check=False)
        logger.debug(f"bluetoothctl --version result: {result.returncode}, {result.stdout}")
        if result.returncode != 0:
            return False, "BlueZ is not installed or not accessible"
    except (subprocess.SubprocessError, FileNotFoundError):
        return False, "BlueZ is not installed or not accessible"

    try:
        # Check if Bluetooth is enabled
        result = subprocess.run(['bluetoothctl', 'show'],
                              capture_output=True,
                              text=True, check=False)
        logger.debug(f"bluetoothctl show result: {result.returncode}, {result.stdout}")
        if result.returncode != 0:
            return False, "Could not check Bluetooth status"

        # Parse the output line by line to find Powered status
        powered = False
        for line in result.stdout.splitlines():
            logger.debug(f"Checking line: {line}")
            if line.strip().startswith('Powered:'):
                powered = line.strip().endswith('yes')
                logger.debug(f"Found Powered line: {line}, powered = {powered}")
                break

        if not powered:
            return False, "Bluetooth is not powered on"
    except subprocess.SubprocessError:
        return False, "Could not check Bluetooth status"

    return True, "System requirements met"

def is_ios_device(device: Any) -> bool:
    """
    Detects if a device is likely an iOS device based on advertising data patterns.
    Args:
        device: The BLE device object
    Returns:
        True if the device is likely an iOS device, False otherwise.
    """
    # Check for Apple-specific manufacturer data
    if device.getValue(MANUFACTURER_DATA_TYPE):
        manu_data = device.getValueText(MANUFACTURER_DATA_TYPE)
        if manu_data and manu_data.startswith(APPLE_COMPANY_ID):
            return True

    # Check for Apple service UUIDs
    services = []
    if device.getValue(INCOMPLETE_16B_SERVICES):
        services.append(device.getValueText(INCOMPLETE_16B_SERVICES))
    if device.getValue(COMPLETE_16B_SERVICES):
        services.append(device.getValueText(COMPLETE_16B_SERVICES))

    services_str = ''.join(services).upper()
    for uuid in APPLE_SERVICE_UUIDS:
        if uuid.replace('0x', '').upper() in services_str:
            return True

    return False

def _get_service_components(device: Any) -> list[str]:
    """Extract service information from device."""
    services = []
    if device.getValue(INCOMPLETE_16B_SERVICES):
        services.append(device.getValueText(INCOMPLETE_16B_SERVICES))
    if device.getValue(COMPLETE_16B_SERVICES):
        services.append(device.getValueText(COMPLETE_16B_SERVICES))
    if services:
        services_str = ''.join(sorted(services))
        return [f"services:{services_str}"]
    return []

def _get_name_components(device: Any) -> list[str]:
    """Extract name information from device."""
    if device.getValue(COMPLETE_LOCAL_NAME):
        name = device.getValueText(COMPLETE_LOCAL_NAME)
        if len(name) > 1 and not all(c in '0123456789abcdefABCDEF' for c in name):
            return [f"name:{name}"]
    elif device.getValue(SHORT_LOCAL_NAME):
        name = device.getValueText(SHORT_LOCAL_NAME)
        if len(name) > 1 and not all(c in '0123456789abcdefABCDEF' for c in name):
            return [f"short_name:{name}"]
    return []

def _get_manufacturer_components(device: Any) -> list[str]:
    """Extract manufacturer information from device."""
    if device.getValue(MANUFACTURER_DATA_TYPE):
        manu_data = device.getValueText(MANUFACTURER_DATA_TYPE)
        if manu_data:
            if manu_data.startswith(APPLE_COMPANY_ID):
                return [f"manu:{manu_data}"]
            return [f"manu:{manu_data[:4]}"]
    return []

def build_device_fingerprint(device: Any) -> str:
    """
    Creates a fingerprint for a BLE device based on its advertising data.
    Handles MAC randomization by focusing on stable device identifiers and platform-specific patterns.
    Args:
        device: The BLE device object
    Returns:
        A SHA-256 hash string representing the device fingerprint.
    """
    fingerprint_components = []

    # Get manufacturer data (most stable identifier)
    fingerprint_components.extend(_get_manufacturer_components(device))

    # Get service information (stable across MAC changes)
    fingerprint_components.extend(_get_service_components(device))

    # Get device name (if available and not random)
    fingerprint_components.extend(_get_name_components(device))

    # Device Class (stable across MAC changes)
    if device.getValue(DEVICE_CLASS):
        device_class = device.getValueText(DEVICE_CLASS)
        fingerprint_components.append(f"class:{device_class}")

    # For iOS devices, check for specific advertising patterns
    if device.addrType == "random" and device.addr.startswith("40:00"):
        # This is likely an iOS device with a private address
        # The manufacturer data and services are more reliable identifiers
        if not any("manu:" in comp for comp in fingerprint_components):
            # If we don't have manufacturer data, use the address type
            fingerprint_components.append("ios_private_addr")

    # For Android devices, check for specific advertising patterns
    if device.addrType == "random" and not device.addr.startswith("40:00"):
        # This is likely an Android device with a random address
        # The manufacturer data and services are more reliable identifiers
        if not any("manu:" in comp for comp in fingerprint_components):
            # If we don't have manufacturer data, use the address type
            fingerprint_components.append("android_random_addr")

    # If we have no components, use the address type as a last resort
    if not fingerprint_components:
        fingerprint_components.append(f"addr_type:{device.addrType}")

    # Sort components for consistent ordering
    fingerprint_components.sort()

    # Create a hash of all components
    fingerprint = hashlib.sha256('|'.join(fingerprint_components).encode()).hexdigest()
    return fingerprint

def calculate_metrics(time_window: timedelta) -> dict[str, Any]:
    """
    Calculate metrics for a given time window.
    Args:
        time_window: The time window as a timedelta object.
    Returns:
        A dictionary with calculated metrics.
    """
    now = datetime.now()
    window_start = now - time_window

    # Filter results within the time window
    window_results = [
        result for result in scan_history
        if result.timestamp >= window_start
    ]

    if not window_results:
        return {
            "average_unique_devices": 0,
            "average_ios_devices": 0,
            "average_other_devices": 0,
            "peak_unique_devices": 0,
            "peak_ios_devices": 0,
            "peak_other_devices": 0,
            "manufacturer_stats": {}
        }

    unique_devices = [r.unique_devices for r in window_results]
    ios_devices = [r.ios_devices for r in window_results]
    other_devices = [r.other_devices for r in window_results]

    # Calculate manufacturer statistics
    manufacturer_stats = {}
    for result in window_results:
        for manufacturer, count in result.manufacturer_stats.items():
            manufacturer_stats[manufacturer] = manufacturer_stats.get(manufacturer, 0) + count

    # Calculate averages for manufacturers
    for manufacturer in manufacturer_stats:
        manufacturer_stats[manufacturer] = manufacturer_stats[manufacturer] / len(window_results)

    return {
        "average_unique_devices": sum(unique_devices) / len(unique_devices),
        "average_ios_devices": sum(ios_devices) / len(ios_devices),
        "average_other_devices": sum(other_devices) / len(other_devices),
        "peak_unique_devices": max(unique_devices),
        "peak_ios_devices": max(ios_devices),
        "peak_other_devices": max(other_devices),
        "manufacturer_stats": manufacturer_stats
    }

def setup_bluetooth() -> None:
    """Set up Bluetooth adapter for scanning."""
    try:
        # Reset the Bluetooth adapter
        subprocess.run(['hciconfig', 'hci0', 'reset'], check=True)
        # Enable scanning
        subprocess.run(['hciconfig', 'hci0', 'up'], check=True)

        # Try to stop any existing scans, but don't fail if it errors
        try:
            subprocess.run(['bluetoothctl', 'scan', 'off'], check=False)
        except subprocess.SubprocessError:
            logger.debug("No active scan to stop")

        # Ensure power is on
        subprocess.run(['bluetoothctl', 'power', 'on'], check=True)

    except subprocess.CalledProcessError as e:
        logger.error(f"Error setting up Bluetooth: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set up Bluetooth adapter: {e!s}"
        ) from e

async def background_scan() -> None:
    """Background task that runs BLE scans periodically."""
    while True:
        try:
            # Check system requirements
            success, message = check_system_requirements()
            if not success:
                logger.error(f"System requirements not met: {message}")
                await asyncio.sleep(SCAN_INTERVAL_SECONDS)  # Wait before retrying
                continue

            # Set up Bluetooth adapter
            setup_bluetooth()

            logger.info("Starting background BLE scan")
            scanner = Scanner().withDelegate(ScanDelegate())
            devices = scanner.scan(SCAN_DURATION_SECONDS)

            # Track unique devices
            unique_devices: set[str] = set()
            ios_devices: set[str] = set()
            manufacturer_stats = {}
            current_time = datetime.now()

            # Clean up old sessions
            session_manager.cleanup_old_sessions(current_time)

            for device in devices:
                fingerprint = build_device_fingerprint(device)
                unique_devices.add(fingerprint)

                # Update session
                session_manager.update_session(fingerprint, current_time, device.rssi)

                if is_ios_device(device):
                    ios_devices.add(fingerprint)

                # Track manufacturer statistics
                manufacturer = get_manufacturer_from_device(device)
                manufacturer_stats[manufacturer] = manufacturer_stats.get(manufacturer, 0) + 1

            # Get session statistics
            session_stats = session_manager.get_session_stats()

            # Create and store scan result
            scan_result = ScanResult(
                timestamp=current_time,
                unique_devices=len(unique_devices),
                ios_devices=len(ios_devices),
                other_devices=len(unique_devices) - len(ios_devices),
                manufacturer_stats=manufacturer_stats,
                session_stats=session_stats  # Add session statistics
            )
            scan_history.append(scan_result)

            # Save to disk if enough time has passed
            if persistence.should_save():
                persistence.save_history(list(scan_history))

            logger.info(f"Background scan completed: {len(unique_devices)} unique devices found")
            logger.info(f"Active sessions: {session_stats['active_sessions']}")
            logger.info(f"Average dwell time: {session_stats['average_dwell_time']:.1f} seconds")

            await asyncio.sleep(SCAN_INTERVAL_SECONDS)

        except Exception as e:
            logger.error(f"Error during background scan: {e}")
            await asyncio.sleep(SCAN_INTERVAL_SECONDS)

@app.on_event("startup")
async def startup_event() -> None:
    """Start background scanning task on startup."""
    await scanner.start()

@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Stop background scanning task on shutdown."""
    await scanner.stop()

@app.get("/latest")
async def get_latest_scan() -> dict[str, Any]:
    """
    Return the most recent scan results and historical statistics.
    This endpoint does not trigger a new scan - it returns data from the background scanning task.
    Returns:
        Dictionary containing:
        - current_scan: Most recent scan results
        - last_hour: Statistics for the last hour
        - last_24h: Statistics for the last 24 hours
        - session_stats: Current session statistics
    """
    try:
        # Calculate metrics for different time windows
        last_hour = calculate_metrics(timedelta(hours=1))
        last_24h = calculate_metrics(timedelta(hours=24))

        # Get the most recent scan result
        if scan_history:
            latest_scan = scan_history[-1]
            current_scan = {
                "unique_devices": latest_scan.unique_devices,
                "ios_devices": latest_scan.ios_devices,
                "other_devices": latest_scan.other_devices,
                "manufacturer_stats": latest_scan.manufacturer_stats,
                "scan_duration_seconds": SCAN_DURATION_SECONDS,
                "session_stats": latest_scan.session_stats  # Add session statistics
            }
        else:
            current_scan = {
                "unique_devices": 0,
                "ios_devices": 0,
                "other_devices": 0,
                "manufacturer_stats": {},
                "scan_duration_seconds": 0,
                "session_stats": {
                    "total_sessions": 0,
                    "active_sessions": 0,
                    "average_dwell_time": 0
                }
            }

        # Get current session statistics
        session_stats = session_manager.get_session_stats()

        result = {
            "current_scan": current_scan,
            "last_hour": last_hour,
            "last_24h": last_24h,
            "session_stats": session_stats
        }

        return result

    except Exception as e:
        logger.error(f"Error getting scan results: {e!s}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting scan results: {e!s}"
        ) from e

@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Check if the system meets the requirements for BLE scanning.
    Returns:
        Dictionary containing status and message.
    """
    success, message = check_system_requirements()
    if not success:
        raise HTTPException(status_code=500, detail=message)
    return {"status": "healthy", "message": message}

def _assign_results_to_slots(scan_history, start_time, interval_minutes, time_slots):
    """Assign scan results to time slots."""
    for result in scan_history:
        if result.timestamp < start_time:
            continue
        slot_time = result.timestamp.replace(
            minute=(result.timestamp.minute // interval_minutes) * interval_minutes,
            second=0,
            microsecond=0
        )
        if slot_time not in time_slots:
            slot_time = min(time_slots.keys(), key=lambda t: abs((t - slot_time).total_seconds()))
        time_slots[slot_time].append(result)

def _build_time_slot_stats(slot_time, results):
    """Build statistics for a time slot."""
    if results:
        unique_devices = [r.unique_devices for r in results]
        ios_devices = [r.ios_devices for r in results]
        other_devices = [r.other_devices for r in results]
        manufacturer_stats = {}
        session_stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "average_dwell_time": 0
        }

        # Calculate manufacturer statistics
        for r in results:
            for manu, count in r.manufacturer_stats.items():
                manufacturer_stats[manu] = manufacturer_stats.get(manu, 0) + count
            # Aggregate session statistics
            if hasattr(r, 'session_stats'):
                session_stats["total_sessions"] += r.session_stats.get("total_sessions", 0)
                session_stats["active_sessions"] += r.session_stats.get("active_sessions", 0)
                session_stats["average_dwell_time"] += r.session_stats.get("average_dwell_time", 0)

        # Calculate averages
        for manu in manufacturer_stats:
            manufacturer_stats[manu] = manufacturer_stats[manu] / len(results)
        if len(results) > 0:
            session_stats["total_sessions"] = session_stats["total_sessions"] / len(results)
            session_stats["active_sessions"] = session_stats["active_sessions"] / len(results)
            session_stats["average_dwell_time"] = session_stats["average_dwell_time"] / len(results)

        return {
            "timestamp": slot_time.isoformat(),
            "average_unique_devices": sum(unique_devices) / len(unique_devices),
            "average_ios_devices": sum(ios_devices) / len(ios_devices),
            "average_other_devices": sum(other_devices) / len(other_devices),
            "peak_unique_devices": max(unique_devices),
            "peak_ios_devices": max(ios_devices),
            "peak_other_devices": max(other_devices),
            "manufacturer_stats": manufacturer_stats,
            "session_stats": session_stats
        }
    else:
        return {
            "timestamp": slot_time.isoformat(),
            "average_unique_devices": 0,
            "average_ios_devices": 0,
            "average_other_devices": 0,
            "peak_unique_devices": 0,
            "peak_ios_devices": 0,
            "peak_other_devices": 0,
            "manufacturer_stats": {},
            "session_stats": {
                "total_sessions": 0,
                "active_sessions": 0,
                "average_dwell_time": 0
            }
        }

def _calculate_manufacturer_summary(time_series):
    manufacturer_summary = {}
    for slot in time_series:
        for manufacturer, count in slot["manufacturer_stats"].items():
            if manufacturer not in manufacturer_summary:
                manufacturer_summary[manufacturer] = {
                    "min": float('inf'),
                    "max": 0,
                    "avg": 0
                }
            manufacturer_summary[manufacturer]["min"] = min(
                manufacturer_summary[manufacturer]["min"],
                count
            )
            manufacturer_summary[manufacturer]["max"] = max(
                manufacturer_summary[manufacturer]["max"],
                count
            )
            manufacturer_summary[manufacturer]["avg"] += count
    for manufacturer in manufacturer_summary:
        manufacturer_summary[manufacturer]["avg"] /= len(time_series)
    return manufacturer_summary

@app.get("/time-series")
async def get_time_series(interval_minutes: int = 60) -> dict[str, Any]:
    """
    Get time series data for the last 24 hours, suitable for generating bar charts.
    Args:
        interval_minutes: Time interval between data points in minutes (default: 60)
    Returns:
        Dictionary containing time series data for the last 24 hours
    """
    if interval_minutes < 1 or interval_minutes > MAX_TIME_SERIES_MINUTES:
        raise HTTPException(
            status_code=400,
            detail=f"Interval must be between 1 and {MAX_TIME_SERIES_MINUTES} minutes"
        )

    now = datetime.now()
    start_time = now - timedelta(hours=24)

    # Initialize time slots
    time_slots = {}
    current_time = start_time
    while current_time <= now:
        time_slots[current_time] = []
        current_time += timedelta(minutes=interval_minutes)

    # Assign scan results to slots
    _assign_results_to_slots(scan_history, start_time, interval_minutes, time_slots)

    # Build new time series format
    time_series = [_build_time_slot_stats(slot_time, results) for slot_time, results in time_slots.items()]

    # Calculate summary statistics
    summary = {
        "unique_devices": {
            "min": min(slot["average_unique_devices"] for slot in time_series),
            "max": max(slot["average_unique_devices"] for slot in time_series),
            "avg": sum(slot["average_unique_devices"] for slot in time_series) / len(time_series)
        },
        "ios_devices": {
            "min": min(slot["average_ios_devices"] for slot in time_series),
            "max": max(slot["average_ios_devices"] for slot in time_series),
            "avg": sum(slot["average_ios_devices"] for slot in time_series) / len(time_series)
        },
        "other_devices": {
            "min": min(slot["average_other_devices"] for slot in time_series),
            "max": max(slot["average_other_devices"] for slot in time_series),
            "avg": sum(slot["average_other_devices"] for slot in time_series) / len(time_series)
        }
    }

    # Calculate manufacturer summary
    manufacturer_summary = _calculate_manufacturer_summary(time_series)

    return {
        "interval_minutes": interval_minutes,
        "time_series": time_series,
        "summary": summary,
        "manufacturer_summary": manufacturer_summary
    }