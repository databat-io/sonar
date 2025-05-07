from unittest.mock import MagicMock, patch

import pytest

from app.main import MANUFACTURER_DATA_TYPE


@pytest.fixture(autouse=True)
def mock_bluetooth():
    """Mock Bluetooth functionality for testing."""
    with patch('bluepy.btle.Scanner') as mock_scanner:
        # Create a mock device
        mock_device = MagicMock()
        mock_device.addr = "00:11:22:33:44:55"
        mock_device.addrType = "random"  # Most BLE devices use random addresses
        mock_device.rssi = -65
        # Simulate Apple device with manufacturer data and service UUIDs
        mock_device.getValue = MagicMock(side_effect=lambda x: b'4c00' if x == MANUFACTURER_DATA_TYPE else b'0xFD6F' if x in [2, 3] else None)
        mock_device.getValueText = MagicMock(side_effect=lambda x: '4c00' if x == MANUFACTURER_DATA_TYPE else '0xFD6F' if x in [2, 3] else '')

        # Configure the mock scanner to return our mock device
        scanner_instance = MagicMock()
        scanner_instance.scan = MagicMock(return_value=[mock_device])
        scanner_instance.withDelegate = MagicMock(return_value=scanner_instance)
        mock_scanner.return_value = scanner_instance

        yield mock_scanner

@pytest.fixture
def mock_manufacturer_data():
    """Mock manufacturer data for testing."""
    with patch('app.manufacturers.MANUFACTURER_DB') as mock_db:
        mock_db.get.return_value = "Test Manufacturer"
        yield mock_db

@pytest.fixture
def mock_system_requirements():
    """Mock system requirements check for testing."""
    with patch('app.main.check_system_requirements') as mock_check:
        mock_check.return_value = (True, "System requirements met")
        yield mock_check

@pytest.fixture
def mock_device():
    device = MagicMock()
    device.addr = "00:11:22:33:44:55"
    device.addrType = "random"
    device.rssi = -65
    device.getValue = MagicMock(side_effect=lambda x: b'4c00' if x == MANUFACTURER_DATA_TYPE else None)
    device.getValueText = MagicMock(side_effect=lambda x: '4c00' if x == MANUFACTURER_DATA_TYPE else '')