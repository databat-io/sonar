from fastapi.testclient import TestClient
from app.main import (
    app,
    build_device_fingerprint,
    is_ios_device,
    calculate_metrics,
    check_system_requirements
)
from app.persistence import ScanResult
from datetime import datetime, timedelta
import json
import pytest
from unittest.mock import patch, MagicMock
from bluepy.btle import Scanner, BTLEManagementError
import subprocess

client = TestClient(app)

def test_health_check():
    with patch('app.main.check_system_requirements') as mock_check:
        mock_check.return_value = (True, "System requirements met")
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "System requirements met"

@pytest.fixture
def mock_ble_device():
    device = MagicMock()
    device.addr = "00:11:22:33:44:55"
    device.addrType = "random"  # Most BLE devices use random addresses
    device.rssi = -65
    # Simulate Apple device with manufacturer data
    device.getValue = MagicMock(side_effect=lambda x: b'4c00' if x == 255 else None)
    device.getValueText = MagicMock(side_effect=lambda x: '4c00' if x == 255 else '')
    return device

def test_is_ios_device_with_apple_manufacturer():
    device = MagicMock()
    device.getValue = MagicMock(side_effect=lambda x: b'4c00' if x == 255 else None)
    device.getValueText = MagicMock(side_effect=lambda x: '4c00' if x == 255 else '')
    assert is_ios_device(device) is True

def test_is_ios_device_with_apple_service():
    device = MagicMock()
    device.getValue = MagicMock(side_effect=lambda x: b'0xFD6F' if x in [2, 3] else None)
    device.getValueText = MagicMock(side_effect=lambda x: '0xFD6F' if x in [2, 3] else '')
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
    assert len(fingerprint) == 64  # SHA-256 hash length

def test_build_device_fingerprint_with_manufacturer():
    device = MagicMock()
    device.addrType = "public"
    device.getValue = MagicMock(side_effect=lambda x: b'4c00' if x == 255 else None)
    device.getValueText = MagicMock(side_effect=lambda x: '4c00' if x == 255 else '')
    fingerprint1 = build_device_fingerprint(device)

    # Change manufacturer data
    device.getValueText = MagicMock(side_effect=lambda x: '0000' if x == 255 else '')
    fingerprint2 = build_device_fingerprint(device)

    assert fingerprint1 != fingerprint2

def test_build_device_fingerprint_with_services():
    device = MagicMock()
    device.addrType = "public"
    device.getValue = MagicMock(side_effect=lambda x: b'1234' if x in [2, 3] else None)
    device.getValueText = MagicMock(side_effect=lambda x: '1234' if x in [2, 3] else '')
    fingerprint = build_device_fingerprint(device)
    assert isinstance(fingerprint, str)

@pytest.mark.asyncio
async def test_scan_endpoint():
    # Mock device for testing
    mock_device = MagicMock()
    mock_device.addr = "00:11:22:33:44:55"
    mock_device.addrType = "random"
    mock_device.rssi = -65
    # Simulate Apple device with manufacturer data and service UUIDs
    mock_device.getValue = MagicMock(side_effect=lambda x: b'4c00' if x == 255 else b'0xFD6F' if x in [2, 3] else None)
    mock_device.getValueText = MagicMock(side_effect=lambda x: '4c00' if x == 255 else '0xFD6F' if x in [2, 3] else '')

    # Mock Scanner class and BTLEManagementError
    with patch('app.main.Scanner') as mock_scanner_class, \
         patch('app.main.check_system_requirements') as mock_check, \
         patch('subprocess.run') as mock_run, \
         patch('app.manufacturers.lookup_manufacturer') as mock_lookup:

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
                result.stdout = "Controller 00:11:22:33:44:55\nPowered: yes\nDiscoverable: no\nPairable: yes"
            elif 'hciconfig' in args[0]:
                result.stdout = ""
            return result
        mock_run.side_effect = mock_run_cmd

        response = client.get("/scan?timeout=1")
        assert response.status_code == 200
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
        assert current["scan_duration_seconds"] == 1

        # Verify scanner was called correctly
        scanner_instance.scan.assert_called_once_with(1.0)

@pytest.mark.asyncio
async def test_scan_endpoint_error():
    with patch('app.main.Scanner') as mock_scanner_class, \
         patch('app.main.check_system_requirements') as mock_check, \
         patch('subprocess.run') as mock_run:

        # Mock system requirements check
        mock_check.return_value = (True, "System requirements met")

        # Mock subprocess calls
        def mock_run_cmd(*args, **kwargs):
            result = MagicMock()
            result.returncode = 0
            if 'bluetoothctl --version' in args[0]:
                result.stdout = "bluetoothctl version 5.66"
            elif 'bluetoothctl show' in args[0]:
                result.stdout = "Controller 00:11:22:33:44:55\nPowered: yes\nDiscoverable: no\nPairable: yes"
            elif 'hciconfig' in args[0]:
                result.stdout = ""
            return result
        mock_run.side_effect = mock_run_cmd

        # Mock scanner to raise an error
        mock_scanner_class.side_effect = Exception("Failed to initialize scanner")

        response = client.get("/scan?timeout=1")
        assert response.status_code == 500
        assert response.json() == {"detail": "Unexpected error during scan: Failed to initialize scanner"}

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
        mock_show.stdout = "Controller 00:11:22:33:44:55\nPowered: yes\nDiscoverable: no\nPairable: yes"

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
                result.stdout = "Controller 00:11:22:33:44:55\nPowered: no\nDiscoverable: no\nPairable: yes"
            return result
        mock_run.side_effect = mock_run_cmd
        success, message = check_system_requirements()
        assert success is False
        assert "Bluetooth is not powered on" in message

def test_time_series_endpoint():
    response = client.get("/time-series?interval_minutes=60")
    assert response.status_code == 200
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
    assert response.status_code == 400

    response = client.get("/time-series?interval_minutes=1441")
    assert response.status_code == 400

def test_calculate_metrics():
    # Create sample scan results
    now = datetime.now()
    results = [
        ScanResult(
            timestamp=now - timedelta(minutes=30),
            total_devices=10,
            unique_devices=8,
            ios_devices=5,
            other_devices=3,
            manufacturer_stats={"Apple": 5, "Nordic": 3}
        ),
        ScanResult(
            timestamp=now - timedelta(minutes=15),
            total_devices=12,
            unique_devices=9,
            ios_devices=6,
            other_devices=3,
            manufacturer_stats={"Apple": 6, "Nordic": 3}
        )
    ]

    metrics = calculate_metrics(timedelta(hours=1))

    assert "average_total_devices" in metrics
    assert "average_unique_devices" in metrics
    assert "average_ios_devices" in metrics
    assert "average_other_devices" in metrics
    assert "peak_total_devices" in metrics
    assert "peak_unique_devices" in metrics
    assert "manufacturer_stats" in metrics