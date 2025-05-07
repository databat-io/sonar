import asyncio
import hashlib
import logging
import subprocess
from collections import deque
from datetime import datetime, timedelta

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
    TX_POWER_LEVEL,
)
from .manufacturers import get_manufacturer_from_device
from .persistence import DataPersistence, ScanResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScanDelegate(DefaultDelegate):
    """Delegate for handling BLE scan events."""
    def __init__(self):
        DefaultDelegate.__init__(self)

class BackgroundScanner:
    """Manages the background BLE scanning task."""
    def __init__(self):
        self.task = None

    async def start(self):
        """Start the background scanning task."""
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(background_scan())

    async def stop(self):
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

def is_ios_device(device) -> bool:
    """
    Detects if a device is likely an iOS device based on advertising data patterns.
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

def build_device_fingerprint(device) -> str:
    """
    Creates a fingerprint for a BLE device based on its advertising data.
    """
    fingerprint_components = []

    # Basic device information
    fingerprint_components.append(f"addr_type:{device.addrType}")

    # Manufacturer data
    if device.getValue(MANUFACTURER_DATA_TYPE):
        manu_data = device.getValueText(MANUFACTURER_DATA_TYPE)
        fingerprint_components.append(f"manu:{manu_data[:4]}")

    # Service information
    if device.getValue(INCOMPLETE_16B_SERVICES):
        services = device.getValueText(INCOMPLETE_16B_SERVICES)
        fingerprint_components.append(f"services_16b:{services}")

    if device.getValue(COMPLETE_16B_SERVICES):
        services = device.getValueText(COMPLETE_16B_SERVICES)
        fingerprint_components.append(f"services_16b_complete:{services}")

    # Device name
    if device.getValue(COMPLETE_LOCAL_NAME):
        name = device.getValueText(COMPLETE_LOCAL_NAME)
        fingerprint_components.append(f"name:{name}")
    elif device.getValue(SHORT_LOCAL_NAME):
        name = device.getValueText(SHORT_LOCAL_NAME)
        fingerprint_components.append(f"short_name:{name}")

    # TX Power Level
    if device.getValue(TX_POWER_LEVEL):
        tx_power = device.getValueText(TX_POWER_LEVEL)
        fingerprint_components.append(f"tx_power:{tx_power}")

    # Device Class
    if device.getValue(DEVICE_CLASS):
        device_class = device.getValueText(DEVICE_CLASS)
        fingerprint_components.append(f"class:{device_class}")

    # Create a stable fingerprint
    fingerprint = '|'.join(sorted(fingerprint_components))
    return hashlib.sha256(fingerprint.encode()).hexdigest()

def calculate_metrics(time_window: timedelta) -> dict:
    """
    Calculate metrics for a given time window.
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
            "average_total_devices": 0,
            "average_unique_devices": 0,
            "average_ios_devices": 0,
            "average_other_devices": 0,
            "peak_total_devices": 0,
            "peak_unique_devices": 0,
            "peak_ios_devices": 0,
            "peak_other_devices": 0,
            "manufacturer_stats": {}
        }

    # Calculate averages
    total_devices = [r.total_devices for r in window_results]
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
        "average_total_devices": sum(total_devices) / len(total_devices),
        "average_unique_devices": sum(unique_devices) / len(unique_devices),
        "average_ios_devices": sum(ios_devices) / len(ios_devices),
        "average_other_devices": sum(other_devices) / len(other_devices),
        "peak_total_devices": max(total_devices),
        "peak_unique_devices": max(unique_devices),
        "peak_ios_devices": max(ios_devices),
        "peak_other_devices": max(other_devices),
        "manufacturer_stats": manufacturer_stats
    }

def setup_bluetooth():
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

async def background_scan():
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

            for device in devices:
                fingerprint = build_device_fingerprint(device)
                unique_devices.add(fingerprint)

                if is_ios_device(device):
                    ios_devices.add(fingerprint)

                # Track manufacturer statistics
                manufacturer = get_manufacturer_from_device(device)
                manufacturer_stats[manufacturer] = manufacturer_stats.get(manufacturer, 0) + 1

            # Create and store scan result
            scan_result = ScanResult(
                timestamp=datetime.now(),
                total_devices=len(devices),
                unique_devices=len(unique_devices),
                ios_devices=len(ios_devices),
                other_devices=len(unique_devices) - len(ios_devices),
                manufacturer_stats=manufacturer_stats
            )
            scan_history.append(scan_result)

            # Save to disk if enough time has passed
            if persistence.should_save():
                persistence.save_history(list(scan_history))

            logger.info(f"Background scan completed: {len(devices)} devices found")

        except Exception as e:
            logger.error(f"Error in background scan: {e!s}")

        # Wait for next scan interval
        await asyncio.sleep(SCAN_INTERVAL_SECONDS)

@app.on_event("startup")
async def startup_event():
    """Start background scanning task on startup."""
    await scanner.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop background scanning task on shutdown."""
    await scanner.stop()

@app.get("/latest")
async def get_latest_scan() -> dict:
    """
    Return the most recent scan results and historical statistics.
    This endpoint does not trigger a new scan - it returns data from the background scanning task.

    Returns:
        Dictionary containing:
        - current_scan: Most recent scan results
        - last_hour: Statistics for the last hour
        - last_24h: Statistics for the last 24 hours
    """
    try:
        # Calculate metrics for different time windows
        last_hour = calculate_metrics(timedelta(hours=1))
        last_24h = calculate_metrics(timedelta(hours=24))

        # Get the most recent scan result
        if scan_history:
            latest_scan = scan_history[-1]
            current_scan = {
                "total_devices": latest_scan.total_devices,
                "unique_devices": latest_scan.unique_devices,
                "ios_devices": latest_scan.ios_devices,
                "other_devices": latest_scan.other_devices,
                "manufacturer_stats": latest_scan.manufacturer_stats,
                "scan_duration_seconds": 10  # Fixed duration for background scans
            }
        else:
            current_scan = {
                "total_devices": 0,
                "unique_devices": 0,
                "ios_devices": 0,
                "other_devices": 0,
                "manufacturer_stats": {},
                "scan_duration_seconds": 0
            }

        result = {
            "current_scan": current_scan,
            "last_hour": last_hour,
            "last_24h": last_24h
        }

        return result

    except Exception as e:
        logger.error(f"Error getting scan results: {e!s}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting scan results: {e!s}"
        ) from e

@app.get("/health")
async def health_check() -> dict:
    """
    Simple health check endpoint that also verifies system requirements.
    """
    success, message = check_system_requirements()
    return {
        "status": "healthy" if success else "unhealthy",
        "message": message
    }

@app.get("/time-series")
async def get_time_series(interval_minutes: int = 60) -> dict:
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
        time_slots[current_time] = {
            "timestamp": current_time.isoformat(),
            "total_devices": 0,
            "unique_devices": 0,
            "ios_devices": 0,
            "other_devices": 0,
            "manufacturer_stats": {}
        }
        current_time += timedelta(minutes=interval_minutes)

    # Process scan history
    for result in scan_history:
        if result.timestamp < start_time:
            continue

        # Find the appropriate time slot
        slot_time = result.timestamp.replace(
            minute=(result.timestamp.minute // interval_minutes) * interval_minutes,
            second=0,
            microsecond=0
        )

        if slot_time in time_slots:
            slot = time_slots[slot_time]
            slot["total_devices"] = max(slot["total_devices"], result.total_devices)
            slot["unique_devices"] = max(slot["unique_devices"], result.unique_devices)
            slot["ios_devices"] = max(slot["ios_devices"], result.ios_devices)
            slot["other_devices"] = max(slot["other_devices"], result.other_devices)

            # Update manufacturer stats
            for manufacturer, count in result.manufacturer_stats.items():
                if manufacturer not in slot["manufacturer_stats"]:
                    slot["manufacturer_stats"][manufacturer] = 0
                slot["manufacturer_stats"][manufacturer] = max(
                    slot["manufacturer_stats"][manufacturer],
                    count
                )

    # Convert to list format for easier client-side processing
    time_series = list(time_slots.values())

    # Calculate summary statistics
    summary = {
        "total_devices": {
            "min": min(slot["total_devices"] for slot in time_series),
            "max": max(slot["total_devices"] for slot in time_series),
            "avg": sum(slot["total_devices"] for slot in time_series) / len(time_series)
        },
        "unique_devices": {
            "min": min(slot["unique_devices"] for slot in time_series),
            "max": max(slot["unique_devices"] for slot in time_series),
            "avg": sum(slot["unique_devices"] for slot in time_series) / len(time_series)
        },
        "ios_devices": {
            "min": min(slot["ios_devices"] for slot in time_series),
            "max": max(slot["ios_devices"] for slot in time_series),
            "avg": sum(slot["ios_devices"] for slot in time_series) / len(time_series)
        },
        "other_devices": {
            "min": min(slot["other_devices"] for slot in time_series),
            "max": max(slot["other_devices"] for slot in time_series),
            "avg": sum(slot["other_devices"] for slot in time_series) / len(time_series)
        }
    }

    # Calculate manufacturer summary
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

    # Calculate averages for manufacturers
    for manufacturer in manufacturer_summary:
        manufacturer_summary[manufacturer]["avg"] /= len(time_series)

    return {
        "interval_minutes": interval_minutes,
        "time_series": time_series,
        "summary": summary,
        "manufacturer_summary": manufacturer_summary
    }