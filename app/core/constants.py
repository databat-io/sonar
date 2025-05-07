"""Constants used throughout the application."""

# BLE Advertisement Data Types
MANUFACTURER_DATA_TYPE = 255  # Manufacturer Specific Data
INCOMPLETE_16B_SERVICES = 2  # Incomplete list of 16-bit Service UUIDs
COMPLETE_16B_SERVICES = 3  # Complete list of 16-bit Service UUIDs
COMPLETE_LOCAL_NAME = 9  # Complete Local Name
SHORT_LOCAL_NAME = 8  # Shortened Local Name
TX_POWER_LEVEL = 10  # TX Power Level
DEVICE_CLASS = 13  # Device Class

# Time-related constants
MAX_HISTORY_HOURS = 24
MAX_HISTORY_MINUTES = MAX_HISTORY_HOURS * 60
MAX_TIME_SERIES_MINUTES = 1440  # 24 hours in minutes
SCAN_INTERVAL_SECONDS = 60  # Scan every minute
SCAN_DURATION_SECONDS = 10  # Each scan lasts 10 seconds

# Apple-specific constants
APPLE_COMPANY_ID = '4c00'  # Apple's company ID
APPLE_SERVICE_UUIDS = [
    '0xFD6F',  # Apple Continuity
    '0xFE95',  # Apple Nearby
    '0xFE9B',  # Apple Nearby
    '0xFE9C',  # Apple Nearby
    '0xFE9D',  # Apple Nearby
    '0xFE9E',  # Apple Nearby
    '0xFE9F',  # Apple Nearby
]