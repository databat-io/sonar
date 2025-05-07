from unittest.mock import MagicMock

import pytest

from app.main import MANUFACTURER_DATA_TYPE
from app.manufacturers import (
    MANUFACTURER_DB,
    get_manufacturer_from_device,
    lookup_manufacturer,
)

# Test constants
TEST_APPLE_MANU_DATA = "4c00"
TEST_NORDIC_MANU_DATA = "0059"
TEST_UNKNOWN_MANU_DATA = "ffff"
TEST_APPLE_ID = 0x004C
TEST_NORDIC_ID = 0x0059
TEST_GOOGLE_ID = 0x0029
TEST_UNKNOWN_ID = 0xFFFF

@pytest.fixture
def mock_device():
    device = MagicMock()
    device.getValue = MagicMock(side_effect=lambda x: b'4c00' if x == MANUFACTURER_DATA_TYPE else None)
    device.getValueText = MagicMock(side_effect=lambda x: TEST_APPLE_MANU_DATA if x == MANUFACTURER_DATA_TYPE else '')
    return device

def test_lookup_manufacturer_known():
    assert lookup_manufacturer(TEST_APPLE_ID) == "Apple Inc."
    assert lookup_manufacturer(TEST_NORDIC_ID) == "Nordic Semiconductor ASA"
    assert lookup_manufacturer(TEST_GOOGLE_ID) == "Google Inc."

def test_lookup_manufacturer_unknown():
    assert lookup_manufacturer(TEST_UNKNOWN_ID) == "Unknown"

def test_get_manufacturer_from_device_apple(mock_device):
    assert get_manufacturer_from_device(mock_device) == "Apple Inc."

def test_get_manufacturer_from_device_nordic():
    device = MagicMock()
    device.getValue = MagicMock(side_effect=lambda x: b'0059' if x == MANUFACTURER_DATA_TYPE else None)
    device.getValueText = MagicMock(side_effect=lambda x: TEST_NORDIC_MANU_DATA if x == MANUFACTURER_DATA_TYPE else '')
    assert get_manufacturer_from_device(device) == "Nordic Semiconductor ASA"

def test_get_manufacturer_from_device_unknown():
    device = MagicMock()
    device.getValue = MagicMock(side_effect=lambda x: b'ffff' if x == MANUFACTURER_DATA_TYPE else None)
    device.getValueText = MagicMock(side_effect=lambda x: TEST_UNKNOWN_MANU_DATA if x == MANUFACTURER_DATA_TYPE else '')
    assert get_manufacturer_from_device(device) == "Unknown"

def test_get_manufacturer_from_device_with_data():
    device = MagicMock()
    # Mock manufacturer data for Apple (0x004C)
    device.getValue = MagicMock(side_effect=lambda x: b'004c' if x == MANUFACTURER_DATA_TYPE else None)
    device.getValueText = MagicMock(side_effect=lambda x: '004c' if x == MANUFACTURER_DATA_TYPE else '')

    assert get_manufacturer_from_device(device) == "Apple Inc."

def test_get_manufacturer_from_device_no_data():
    device = MagicMock()
    # Mock no manufacturer data
    device.getValue = MagicMock(return_value=None)
    device.getValueText = MagicMock(return_value='')

    assert get_manufacturer_from_device(device) == "Unknown"

def test_get_manufacturer_from_device_invalid_data():
    device = MagicMock()
    # Mock invalid manufacturer data format
    device.getValue = MagicMock(side_effect=lambda x: b'xyz' if x == MANUFACTURER_DATA_TYPE else None)
    device.getValueText = MagicMock(side_effect=lambda x: 'xyz' if x == MANUFACTURER_DATA_TYPE else '')

    # Should return Unknown for invalid hex data
    assert get_manufacturer_from_device(device) == "Unknown"

def test_get_manufacturer_from_device_short_data():
    device = MagicMock()
    # Mock too short manufacturer data
    device.getValue = MagicMock(side_effect=lambda x: b'00' if x == MANUFACTURER_DATA_TYPE else None)
    device.getValueText = MagicMock(side_effect=lambda x: '00' if x == MANUFACTURER_DATA_TYPE else '')

    # Should return Unknown for too short data
    assert get_manufacturer_from_device(device) == "Unknown"

def test_manufacturer_db_content():
    # Test that the database contains expected entries
    assert len(MANUFACTURER_DB) > 0
    assert MANUFACTURER_DB[0x004C] == "Apple Inc."
    assert MANUFACTURER_DB[0x0059] == "Nordic Semiconductor ASA"
    assert MANUFACTURER_DB[0x0029] == "Google Inc."