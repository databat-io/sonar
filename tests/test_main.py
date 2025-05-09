import asyncio
import hashlib
import subprocess
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.core.constants import MAX_TIME_SERIES_MINUTES
from app.main import (
    COMPLETE_16B_SERVICES,
    INCOMPLETE_16B_SERVICES,
    MANUFACTURER_DATA_TYPE,
    SCAN_DURATION_SECONDS,
    BackgroundScanner,
    ScanDelegate,
    app,
    background_scan,
    build_device_fingerprint,
    calculate_metrics,
    check_system_requirements,
    get_time_series,
    is_ios_device,
    scan_history,
    setup_bluetooth,
)
from app.persistence import ScanResult

# Test constants
TEST_INTERVAL_MINUTES = 60
TEST_RESULTS_COUNT = 3
TEST_MAC_ADDRESS = "00:11:22:33:44:55"
TEST_RSSI = -50
TEST_SCAN_DURATION = SCAN_DURATION_SECONDS
TEST_APPLE_MANU_DATA = "4c000000000000000000000000000000"
TEST_APPLE_SERVICE = "0xFD6F"
TEST_OTHER_SERVICE = "1234"
TEST_SETUP_BLUETOOTH_COMMANDS = 4
SHA256_LENGTH = 64
TEST_APPLE_COMPANY_ID = "4c00"
TEST_APPLE_SERVICE_UUID = "FD6F"  # Valid Apple Continuity UUID
TEST_NON_APPLE_SERVICE_UUID = "fe0d"
TEST_MANUFACTURER_DATA_TYPE = 255

# MAC randomization test constants
IOS_PRIVATE_ADDR_1 = "40:00:11:22:33:44"
IOS_PRIVATE_ADDR_2 = "40:00:55:66:77:88"
ANDROID_RANDOM_ADDR_1 = "42:11:22:33:44:55"
ANDROID_RANDOM_ADDR_2 = "42:aa:bb:cc:dd:ee"
TEST_IOS_MANU_DATA = "4c0012345678"  # Full Apple manufacturer data
TEST_ANDROID_MANU_DATA = "005912345678"  # Nordic Semiconductor manufacturer data

client = TestClient(app)

# Test constants
HTTP_OK = 200
HTTP_ERROR = 500
HTTP_BAD_REQUEST = 400

def test_health_check():
    with patch('app.main.check_system_requirements') as mock_check:
        mock_check.return_value = (True, "System requirements met")
        response = client.get("/health")
        assert response.status_code == HTTP_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "System requirements met"

@pytest.fixture
def mock_device():
    device = MagicMock()
    device.addr = TEST_MAC_ADDRESS
    device.addrType = "random"
    device.rssi = TEST_RSSI
    device.getValue = MagicMock(return_value=None)
    device.getValueText = MagicMock(return_value='')
    return device

@pytest.fixture
def mock_complete_device(mock_device):
    mock_device.getValue = MagicMock(return_value=b'4c00')
    mock_device.getValueText = MagicMock(return_value=TEST_APPLE_MANU_DATA)
    return mock_device

@pytest.mark.asyncio
async def test_latest_endpoint():
    # Mock device for testing
    mock_device = MagicMock()
    mock_device.addr = TEST_MAC_ADDRESS
    mock_device.addrType = "random"
    mock_device.rssi = TEST_RSSI

    # Configure mock device's getValue and getValueText behavior
    def mock_get_value(x):
        if x == MANUFACTURER_DATA_TYPE:
            return b'4c00'
        if x in [INCOMPLETE_16B_SERVICES, COMPLETE_16B_SERVICES]:
            return b'0xFD6F'
        return None

    def mock_get_value_text(x):
        if x == MANUFACTURER_DATA_TYPE:
            return TEST_APPLE_MANU_DATA
        if x in [INCOMPLETE_16B_SERVICES, COMPLETE_16B_SERVICES]:
            return TEST_APPLE_SERVICE
        return ''

    mock_device.getValue = MagicMock(side_effect=mock_get_value)
    mock_device.getValueText = MagicMock(side_effect=mock_get_value_text)

    # Mock Scanner class and BTLEManagementError
    with patch('app.main.Scanner') as mock_scanner_class, \
         patch('app.main.check_system_requirements') as mock_check, \
         patch('subprocess.run') as mock_run, \
         patch('app.manufacturers.lookup_manufacturer') as mock_lookup, \
         patch('app.main.scan_history') as mock_history:

        # Configure scanner mock
        scanner_instance = MagicMock()
        scanner_instance.scan = MagicMock(return_value=[mock_device])
        scanner_instance.withDelegate = MagicMock(return_value=scanner_instance)
        mock_scanner_class.return_value = scanner_instance

        # Mock system requirements check
        mock_check.return_value = (True, "System requirements met")

        # Mock manufacturer lookup
        mock_lookup.return_value = "Apple Inc."

        # Mock subprocess calls
        def mock_run_cmd(*args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            if 'bluetoothctl --version' in args[0]:
                result.stdout = "bluetoothctl version 5.66"
            elif 'bluetoothctl show' in args[0]:
                result.stdout = f"Controller {TEST_MAC_ADDRESS}\nPowered: yes\nDiscoverable: no\nPairable: yes"
            elif 'hciconfig' in args[0]:
                result.stdout = ""
            return result
        mock_run.side_effect = mock_run_cmd

        # Mock scan history
        mock_history.__getitem__.return_value = ScanResult(
            timestamp=datetime.now(),
            unique_devices=1,
            ios_devices=1,
            other_devices=0,
            manufacturer_stats={"Apple Inc.": 1}
        )
        mock_history.__len__.return_value = 1

        response = client.get("/latest")
        assert response.status_code == HTTP_OK
        data = response.json()

        # Check response structure
        assert "current_scan" in data
        assert "last_hour" in data
        assert "last_24h" in data

        # Check current scan data
        current = data["current_scan"]
        assert current["unique_devices"] == 1
        assert current["ios_devices"] == 1
        assert current["other_devices"] == 0
        assert "Apple Inc." in current["manufacturer_stats"]
        assert current["scan_duration_seconds"] == TEST_SCAN_DURATION

@pytest.mark.asyncio
async def test_latest_endpoint_error():
    with patch('app.main.scan_history') as mock_history:
        # Mock scan history to raise an error
        mock_history.__getitem__.side_effect = Exception("Failed to get latest scan")

        response = client.get("/latest")
        assert response.status_code == HTTP_ERROR
        assert response.json() == {"detail": "Error getting scan results: Failed to get latest scan"}

def test_check_system_requirements_success():
    """Test successful system requirements check."""
    with patch('subprocess.run') as mock_run:
        # Mock successful bluetoothctl version check
        mock_version = MagicMock()
        mock_version.returncode = 0
        mock_version.stdout = "bluetoothctl version 5.66"

        # Mock successful bluetoothctl show check
        mock_show = MagicMock()
        mock_show.returncode = 0
        mock_show.stdout = f"Controller {TEST_MAC_ADDRESS}\nPowered: yes\nDiscoverable: no\nPairable: yes"

        # Configure mock_run to return different results based on command
        def mock_run_cmd(*args, **kwargs):
            if not isinstance(args[0], list):
                return MagicMock(returncode=1)

            cmd = args[0][0]
            if cmd == 'bluetoothctl':
                if args[0][1] == '--version':
                    return mock_version
                elif args[0][1] == 'show':
                    return mock_show
            return MagicMock(returncode=1)
        mock_run.side_effect = mock_run_cmd

        success, message = check_system_requirements()
        assert success is True
        assert "System requirements met" in message

def test_check_system_requirements_bluez_missing():
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError()
        success, message = check_system_requirements()
        assert success is False
        assert "BlueZ is not installed" in message

def test_check_system_requirements_bluetooth_off():
    with patch('subprocess.run') as mock_run:
        def mock_run_cmd(*args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            if 'bluetoothctl --version' in args[0]:
                result.stdout = "bluetoothctl version 5.66"
            elif 'bluetoothctl show' in args[0]:
                result.stdout = f"Controller {TEST_MAC_ADDRESS}\nPowered: no\nDiscoverable: no\nPairable: yes"
            return result
        mock_run.side_effect = mock_run_cmd
        success, message = check_system_requirements()
        assert success is False
        assert "Bluetooth is not powered on" in message

def test_time_series_endpoint():
    response = client.get(f"/time-series?interval_minutes={TEST_INTERVAL_MINUTES}")
    assert response.status_code == HTTP_OK
    data = response.json()

    # Check response structure
    assert "interval_minutes" in data
    assert "time_series" in data
    assert "summary" in data
    assert "manufacturer_summary" in data

    # Check time series data
    time_series = data["time_series"]
    assert len(time_series) > 0
    first_entry = time_series[0]
    assert "timestamp" in first_entry
    assert "average_unique_devices" in first_entry
    assert "average_ios_devices" in first_entry
    assert "average_other_devices" in first_entry
    assert "manufacturer_stats" in first_entry

def test_invalid_interval():
    response = client.get("/time-series?interval_minutes=0")
    assert response.status_code == HTTP_BAD_REQUEST

    response = client.get(f"/time-series?interval_minutes={MAX_TIME_SERIES_MINUTES + 1}")
    assert response.status_code == HTTP_BAD_REQUEST

def test_calculate_metrics():
    # Create test data
    now = datetime.now()
    test_data = [
        ScanResult(
            timestamp=now - timedelta(minutes=i),
            unique_devices=i+3,
            ios_devices=i+2,
            other_devices=i+1,
            manufacturer_stats={"Apple": i+2, "Nordic": i+1}
        )
        for i in range(TEST_RESULTS_COUNT)
    ]

    # Add test data to scan history
    scan_history.clear()
    scan_history.extend(test_data)

    # Calculate metrics for last hour
    metrics = calculate_metrics(timedelta(hours=1))

    # Verify metrics
    assert isinstance(metrics, dict)
    assert "average_unique_devices" in metrics
    assert "average_ios_devices" in metrics
    assert "average_other_devices" in metrics
    assert "peak_unique_devices" in metrics
    assert "peak_ios_devices" in metrics
    assert "peak_other_devices" in metrics
    assert "manufacturer_stats" in metrics

@pytest.fixture
def mock_apple_device():
    device = MagicMock()
    device.addrType = "random"
    device.getValue = MagicMock(side_effect=lambda x: b'4c00' if x == TEST_MANUFACTURER_DATA_TYPE else None)
    device.getValueText = MagicMock(side_effect=lambda x: TEST_APPLE_COMPANY_ID if x == TEST_MANUFACTURER_DATA_TYPE else '')
    return device

@pytest.fixture
def mock_apple_service_device():
    device = MagicMock()
    device.addrType = "random"
    device.getValue = MagicMock(side_effect=lambda x: b'fd6f' if x in [2, 3] else None)
    device.getValueText = MagicMock(side_effect=lambda x: TEST_APPLE_SERVICE_UUID if x in [2, 3] else '')
    return device

def test_is_ios_device_by_manufacturer(mock_apple_device):
    assert is_ios_device(mock_apple_device)

def test_is_ios_device_by_service(mock_apple_service_device):
    assert is_ios_device(mock_apple_service_device)

def test_is_ios_device_negative(mock_device):
    assert not is_ios_device(mock_device)

def test_build_device_fingerprint_complete(mock_complete_device):
    fingerprint = build_device_fingerprint(mock_complete_device)
    assert isinstance(fingerprint, str)
    assert len(fingerprint) == SHA256_LENGTH

def test_build_device_fingerprint_minimal(mock_device):
    # Configure mock device to return empty strings for services
    mock_device.getValue = MagicMock(return_value=None)
    mock_device.getValueText = MagicMock(return_value='')
    fingerprint = build_device_fingerprint(mock_device)
    assert isinstance(fingerprint, str)
    assert len(fingerprint) == SHA256_LENGTH

def test_calculate_metrics_empty():
    # Clear scan history before testing
    scan_history.clear()
    metrics = calculate_metrics(timedelta(minutes=5))
    assert metrics["average_unique_devices"] == 0
    assert metrics["average_ios_devices"] == 0
    assert metrics["average_other_devices"] == 0
    assert metrics["peak_unique_devices"] == 0
    assert metrics["peak_ios_devices"] == 0
    assert metrics["peak_other_devices"] == 0
    assert isinstance(metrics["manufacturer_stats"], dict)
    assert len(metrics["manufacturer_stats"]) == 0

def test_scan_delegate():
    delegate = ScanDelegate()
    assert delegate is not None

@pytest.mark.asyncio
async def test_background_scanner():
    scanner = BackgroundScanner()
    assert scanner.task is None

    # Test start
    await scanner.start()
    assert scanner.task is not None
    assert not scanner.task.done()

    # Test stop
    await scanner.stop()
    assert scanner.task is None

@pytest.mark.asyncio
async def test_background_scanner_double_start():
    scanner = BackgroundScanner()
    await scanner.start()
    task1 = scanner.task
    await scanner.start()
    assert scanner.task is task1  # Should not create a new task

@pytest.mark.asyncio
async def test_background_scanner_double_stop():
    scanner = BackgroundScanner()
    await scanner.start()
    await scanner.stop()
    await scanner.stop()  # Should not raise an error
    assert scanner.task is None

def test_setup_bluetooth_success():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        setup_bluetooth()  # Should not raise an exception
        assert mock_run.call_count == TEST_SETUP_BLUETOOTH_COMMANDS

def test_setup_bluetooth_failure():
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, 'hciconfig')
        with pytest.raises(HTTPException) as exc_info:
            setup_bluetooth()
        assert exc_info.value.status_code == HTTP_ERROR
        assert "Failed to set up Bluetooth adapter" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_background_scan_system_requirements_not_met():
    with patch('app.main.check_system_requirements') as mock_check:
        mock_check.return_value = (False, "Test error")
        with patch('asyncio.sleep') as mock_sleep:
            mock_sleep.side_effect = asyncio.CancelledError  # Stop the loop
            with pytest.raises(asyncio.CancelledError):
                await background_scan()

@pytest.mark.asyncio
async def test_background_scan_success():
    with patch('app.main.check_system_requirements') as mock_check, \
         patch('app.main.setup_bluetooth') as mock_setup, \
         patch('bluepy.btle.Scanner') as mock_scanner_class, \
         patch('app.main.logger') as mock_logger:  # Mock logger to avoid permission error messages

        # Mock successful system check
        mock_check.return_value = (True, "OK")

        # Mock scanner
        mock_scanner = MagicMock()
        mock_scanner.scan.return_value = []
        mock_scanner_class.return_value.withDelegate.return_value = mock_scanner

        # Run scan and cancel after first iteration
        with patch('asyncio.sleep') as mock_sleep:
            mock_sleep.side_effect = asyncio.CancelledError
            with pytest.raises(asyncio.CancelledError):
                await background_scan()

        # Verify calls
        mock_check.assert_called_once()
        mock_setup.assert_called_once()
        mock_logger.info.assert_called_with("Starting background BLE scan")

@pytest.mark.asyncio
async def test_get_time_series_invalid_interval():
    with pytest.raises(HTTPException) as exc_info:
        await get_time_series(interval_minutes=0)
    assert exc_info.value.status_code == HTTP_BAD_REQUEST
    assert "must be between 1 and 1440" in str(exc_info.value.detail)

    with pytest.raises(HTTPException) as exc_info:
        await get_time_series(interval_minutes=1441)  # More than 24 hours
    assert exc_info.value.status_code == HTTP_BAD_REQUEST
    assert "must be between 1 and 1440" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_get_time_series_success():
    # Clear scan history
    scan_history.clear()

    # Add some test data
    now = datetime.now()
    for i in range(5):
        scan_history.append(ScanResult(
            timestamp=now - timedelta(minutes=i*10),
            unique_devices=i,
            ios_devices=i//2,
            other_devices=i//2,
            manufacturer_stats={"Test": i}
        ))

    # Test with 30-minute interval
    result = await get_time_series(interval_minutes=30)
    assert "summary" in result
    assert "time_series" in result
    assert len(result["time_series"]) > 0
    assert all(isinstance(m, dict) for m in result["time_series"])

@pytest.fixture
def mock_ios_device():
    """Create a mock iOS device with private address."""
    device = MagicMock()
    device.addr = IOS_PRIVATE_ADDR_1
    device.addrType = "random"
    device.getValue = MagicMock(side_effect=lambda x: b'4c0012345678' if x == TEST_MANUFACTURER_DATA_TYPE else None)
    device.getValueText = MagicMock(side_effect=lambda x: TEST_IOS_MANU_DATA if x == TEST_MANUFACTURER_DATA_TYPE else '')
    return device

@pytest.fixture
def mock_ios_device_different_mac():
    """Create a mock iOS device with a different private address."""
    device = MagicMock()
    device.addr = IOS_PRIVATE_ADDR_2
    device.addrType = "random"
    device.getValue = MagicMock(side_effect=lambda x: b'4c0012345678' if x == TEST_MANUFACTURER_DATA_TYPE else None)
    device.getValueText = MagicMock(side_effect=lambda x: TEST_IOS_MANU_DATA if x == TEST_MANUFACTURER_DATA_TYPE else '')
    return device

@pytest.fixture
def mock_android_device():
    """Create a mock Android device with random address."""
    device = MagicMock()
    device.addr = ANDROID_RANDOM_ADDR_1
    device.addrType = "random"
    device.getValue = MagicMock(side_effect=lambda x: b'005912345678' if x == TEST_MANUFACTURER_DATA_TYPE else None)
    device.getValueText = MagicMock(side_effect=lambda x: TEST_ANDROID_MANU_DATA if x == TEST_MANUFACTURER_DATA_TYPE else '')
    return device

@pytest.fixture
def mock_android_device_different_mac():
    """Create a mock Android device with a different random address."""
    device = MagicMock()
    device.addr = ANDROID_RANDOM_ADDR_2
    device.addrType = "random"
    device.getValue = MagicMock(side_effect=lambda x: b'005912345678' if x == TEST_MANUFACTURER_DATA_TYPE else None)
    device.getValueText = MagicMock(side_effect=lambda x: TEST_ANDROID_MANU_DATA if x == TEST_MANUFACTURER_DATA_TYPE else '')
    return device

def test_ios_mac_randomization(mock_ios_device, mock_ios_device_different_mac):
    """Test that iOS devices with different private addresses are recognized as the same device."""
    # Get fingerprints for both devices
    fingerprint1 = build_device_fingerprint(mock_ios_device)
    fingerprint2 = build_device_fingerprint(mock_ios_device_different_mac)

    # The fingerprints should be identical despite different MAC addresses
    assert fingerprint1 == fingerprint2
    assert "ios_private_addr" not in fingerprint1  # Should use manufacturer data instead

def test_android_mac_randomization(mock_android_device, mock_android_device_different_mac):
    """Test that Android devices with different random addresses are recognized as the same device."""
    # Get fingerprints for both devices
    fingerprint1 = build_device_fingerprint(mock_android_device)
    fingerprint2 = build_device_fingerprint(mock_android_device_different_mac)

    # The fingerprints should be identical despite different MAC addresses
    assert fingerprint1 == fingerprint2
    assert "android_random_addr" not in fingerprint1  # Should use manufacturer data instead

def test_ios_device_without_manufacturer_data():
    """Test iOS device identification when manufacturer data is not available."""
    device = MagicMock()
    device.addr = IOS_PRIVATE_ADDR_1
    device.addrType = "random"
    device.getValue = MagicMock(return_value=None)
    device.getValueText = MagicMock(return_value='')

    # Get the fingerprint components before hashing
    fingerprint_components = []
    if device.addrType == "random" and device.addr.startswith("40:00"):
        fingerprint_components.append("ios_private_addr")

    # Create the fingerprint
    fingerprint = '|'.join(sorted(fingerprint_components))
    hashed_fingerprint = hashlib.sha256(fingerprint.encode()).hexdigest()

    # Verify the components
    assert "ios_private_addr" in fingerprint_components
    assert build_device_fingerprint(device) == hashed_fingerprint

def test_android_device_without_manufacturer_data():
    """Test Android device identification when manufacturer data is not available."""
    device = MagicMock()
    device.addr = ANDROID_RANDOM_ADDR_1
    device.addrType = "random"
    device.getValue = MagicMock(return_value=None)
    device.getValueText = MagicMock(return_value='')

    # Get the fingerprint components before hashing
    fingerprint_components = []
    if device.addrType == "random" and not device.addr.startswith("40:00"):
        fingerprint_components.append("android_random_addr")

    # Create the fingerprint
    fingerprint = '|'.join(sorted(fingerprint_components))
    hashed_fingerprint = hashlib.sha256(fingerprint.encode()).hexdigest()

    # Verify the components
    assert "android_random_addr" in fingerprint_components
    assert build_device_fingerprint(device) == hashed_fingerprint

def test_different_ios_devices():
    """Test that different iOS devices are recognized as different devices."""
    device1 = MagicMock()
    device1.addr = IOS_PRIVATE_ADDR_1
    device1.addrType = "random"
    device1.getValue = MagicMock(side_effect=lambda x: b'4c0012345678' if x == TEST_MANUFACTURER_DATA_TYPE else None)
    device1.getValueText = MagicMock(side_effect=lambda x: "4c0012345678" if x == TEST_MANUFACTURER_DATA_TYPE else '')

    device2 = MagicMock()
    device2.addr = IOS_PRIVATE_ADDR_2
    device2.addrType = "random"
    device2.getValue = MagicMock(side_effect=lambda x: b'4c0098765432' if x == TEST_MANUFACTURER_DATA_TYPE else None)
    device2.getValueText = MagicMock(side_effect=lambda x: "4c0098765432" if x == TEST_MANUFACTURER_DATA_TYPE else '')

    fingerprint1 = build_device_fingerprint(device1)
    fingerprint2 = build_device_fingerprint(device2)

    assert fingerprint1 != fingerprint2  # Different manufacturer data = different devices