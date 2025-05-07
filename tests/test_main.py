from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import (
    COMPLETE_16B_SERVICES,
    INCOMPLETE_16B_SERVICES,
    MANUFACTURER_DATA_TYPE,
    MAX_TIME_SERIES_MINUTES,
    SCAN_DURATION_SECONDS,
    app,
    build_device_fingerprint,
    calculate_metrics,
    check_system_requirements,
    is_ios_device,
    scan_history,
)
from app.persistence import ScanResult

# Test constants
TEST_MAC_ADDRESS = "00:11:22:33:44:55"
TEST_RSSI = -65
TEST_SCAN_DURATION = SCAN_DURATION_SECONDS
TEST_INTERVAL_MINUTES = 60
TEST_APPLE_MANU_DATA = "4c00"
TEST_APPLE_SERVICE = "0xFD6F"
TEST_OTHER_SERVICE = "1234"
TEST_RESULTS_COUNT = 3
HTTP_OK = 200
HTTP_ERROR = 500
HTTP_BAD_REQUEST = 400
SHA256_LENGTH = 64

client = TestClient(app)

def test_health_check():
    with patch('app.main.check_system_requirements') as mock_check:
        mock_check.return_value = (True, "System requirements met")
        response = client.get("/health")
        assert response.status_code == HTTP_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "System requirements met"

@pytest.fixture
def mock_ble_device():
    device = MagicMock()
    device.addr = TEST_MAC_ADDRESS
    device.addrType = "random"  # Most BLE devices use random addresses
    device.rssi = TEST_RSSI
    # Simulate Apple device with manufacturer data
    device.getValue = MagicMock(side_effect=lambda x: b'4c00' if x == MANUFACTURER_DATA_TYPE else None)
    device.getValueText = MagicMock(side_effect=lambda x: TEST_APPLE_MANU_DATA if x == MANUFACTURER_DATA_TYPE else '')
    return device

def test_is_ios_device_with_apple_manufacturer():
    device = MagicMock()
    device.getValue = MagicMock(side_effect=lambda x: b'4c00' if x == MANUFACTURER_DATA_TYPE else None)
    device.getValueText = MagicMock(side_effect=lambda x: TEST_APPLE_MANU_DATA if x == MANUFACTURER_DATA_TYPE else '')
    assert is_ios_device(device) is True

def test_is_ios_device_with_apple_service():
    device = MagicMock()
    device.getValue = MagicMock(side_effect=lambda x: b'0xFD6F' if x in [INCOMPLETE_16B_SERVICES, COMPLETE_16B_SERVICES] else None)
    device.getValueText = MagicMock(side_effect=lambda x: TEST_APPLE_SERVICE if x in [INCOMPLETE_16B_SERVICES, COMPLETE_16B_SERVICES] else '')
    assert is_ios_device(device) is True

def test_is_ios_device_non_apple():
    device = MagicMock()
    device.getValue = MagicMock(return_value=None)
    device.getValueText = MagicMock(return_value='')
    assert is_ios_device(device) is False

def test_build_device_fingerprint_basic():
    device = MagicMock()
    device.addrType = "public"
    device.getValue = MagicMock(return_value=None)
    device.getValueText = MagicMock(return_value='')
    fingerprint = build_device_fingerprint(device)
    assert isinstance(fingerprint, str)
    assert len(fingerprint) == SHA256_LENGTH  # SHA-256 hash length

def test_build_device_fingerprint_with_manufacturer():
    device = MagicMock()
    device.addrType = "public"
    device.getValue = MagicMock(side_effect=lambda x: b'4c00' if x == MANUFACTURER_DATA_TYPE else None)
    device.getValueText = MagicMock(side_effect=lambda x: TEST_APPLE_MANU_DATA if x == MANUFACTURER_DATA_TYPE else '')
    fingerprint1 = build_device_fingerprint(device)

    # Change manufacturer data
    device.getValueText = MagicMock(side_effect=lambda x: '0000' if x == MANUFACTURER_DATA_TYPE else '')
    fingerprint2 = build_device_fingerprint(device)

    assert fingerprint1 != fingerprint2

def test_build_device_fingerprint_with_services():
    device = MagicMock()
    device.addrType = "public"
    device.getValue = MagicMock(side_effect=lambda x: b'1234' if x in [INCOMPLETE_16B_SERVICES, COMPLETE_16B_SERVICES] else None)
    device.getValueText = MagicMock(side_effect=lambda x: TEST_OTHER_SERVICE if x in [INCOMPLETE_16B_SERVICES, COMPLETE_16B_SERVICES] else '')
    fingerprint = build_device_fingerprint(device)
    assert isinstance(fingerprint, str)

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
            total_devices=1,
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
        assert current["total_devices"] == 1
        assert current["unique_devices"] == 1
        assert current["ios_devices"] == 1  # Should detect as iOS device
        assert current["other_devices"] == 0
        assert "Apple Inc." in current["manufacturer_stats"]
        assert current["scan_duration_seconds"] == TEST_SCAN_DURATION  # Fixed duration for background scans

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
    assert "total_devices" in first_entry
    assert "unique_devices" in first_entry
    assert "ios_devices" in first_entry
    assert "other_devices" in first_entry
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
            total_devices=i+5,
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
    assert "average_total_devices" in metrics
    assert "average_unique_devices" in metrics
    assert "average_ios_devices" in metrics
    assert "average_other_devices" in metrics
    assert "peak_total_devices" in metrics
    assert "peak_unique_devices" in metrics
    assert "peak_ios_devices" in metrics
    assert "peak_other_devices" in metrics
    assert "manufacturer_stats" in metrics