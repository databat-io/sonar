from unittest.mock import MagicMock
from app.manufacturers import lookup_manufacturer, get_manufacturer_from_device, MANUFACTURER_DB

def test_lookup_manufacturer_known():
    # Test Apple's ID
    assert lookup_manufacturer(0x004C) == "Apple Inc."

    # Test Nordic's ID
    assert lookup_manufacturer(0x0018) == "Nordic Semiconductor ASA"

    # Test Google's ID
    assert lookup_manufacturer(0x0029) == "Google Inc."

def test_lookup_manufacturer_unknown():
    # Test unknown manufacturer ID
    assert lookup_manufacturer(0xFFFF) == "Unknown"
    assert lookup_manufacturer(123456) == "Unknown"

def test_get_manufacturer_from_device_with_data():
    device = MagicMock()
    # Mock manufacturer data for Apple (0x004C)
    device.getValue = MagicMock(side_effect=lambda x: b'004c' if x == 255 else None)
    device.getValueText = MagicMock(side_effect=lambda x: '004c' if x == 255 else '')

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
    device.getValue = MagicMock(side_effect=lambda x: b'xyz' if x == 255 else None)
    device.getValueText = MagicMock(side_effect=lambda x: 'xyz' if x == 255 else '')

    # Should return Unknown for invalid hex data
    assert get_manufacturer_from_device(device) == "Unknown"

def test_get_manufacturer_from_device_short_data():
    device = MagicMock()
    # Mock too short manufacturer data
    device.getValue = MagicMock(side_effect=lambda x: b'00' if x == 255 else None)
    device.getValueText = MagicMock(side_effect=lambda x: '00' if x == 255 else '')

    # Should return Unknown for too short data
    assert get_manufacturer_from_device(device) == "Unknown"

def test_manufacturer_db_content():
    # Test that the database contains expected entries
    assert len(MANUFACTURER_DB) > 0
    assert MANUFACTURER_DB[0x004C] == "Apple Inc."
    assert MANUFACTURER_DB[0x0018] == "Nordic Semiconductor ASA"
    assert MANUFACTURER_DB[0x0029] == "Google Inc."