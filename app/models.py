"""
Data models used throughout the application.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ScanResult:
    """Represents the results of a BLE scan."""
    timestamp: datetime
    unique_devices: int
    ios_devices: int
    other_devices: int
    manufacturer_stats: dict[str, int]
    session_stats: dict[str, float] | None = None

    def __post_init__(self):
        if self.session_stats is None:
            self.session_stats = {
                "total_sessions": 0,
                "active_sessions": 0,
                "average_dwell_time": 0
            }