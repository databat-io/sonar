"""
Tests for the persistence module.
"""
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from app.models import ScanResult

# Test constants
SAMPLE_UNIQUE_DEVICES = 8
SAMPLE_IOS_DEVICES = 5
SAMPLE_OTHER_DEVICES = 3
SAVE_INTERVAL_MINUTES = 60
TEST_RESULTS_COUNT = 3
HOURS_IN_DAY = 24
DAYS_IN_WEEK = 7
DAYS_BEFORE_WEEK = 6  # Days 2-7 for hourly data
DAYS_AFTER_WEEK = 14  # Days 8-14 for daily data

@pytest.fixture
def sample_scan_result():
    return ScanResult(
        timestamp=datetime.now(),
        unique_devices=SAMPLE_UNIQUE_DEVICES,
        ios_devices=SAMPLE_IOS_DEVICES,
        other_devices=SAMPLE_OTHER_DEVICES,
        manufacturer_stats={"Apple": SAMPLE_IOS_DEVICES, "Nordic": SAMPLE_OTHER_DEVICES}
    )

@pytest.fixture
def temp_data_dir(tmp_path):
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return str(data_dir)

def test_init_creates_directory(tmp_path):
    from app.persistence import DataPersistence

    data_dir = tmp_path / "test_data"
    DataPersistence(data_dir=str(data_dir))  # No need to store in variable
    assert data_dir.exists()

def test_save_history(temp_data_dir, sample_scan_result):
    from app.persistence import DataPersistence

    persistence = DataPersistence(data_dir=temp_data_dir)
    history = [sample_scan_result]
    persistence.save_history(history)

    # Verify files exist and contain valid JSON
    detailed_file = Path(temp_data_dir) / "scan_history_detailed.json"
    hourly_file = Path(temp_data_dir) / "scan_history_hourly.json"
    daily_file = Path(temp_data_dir) / "scan_history_daily.json"

    assert detailed_file.exists()
    assert hourly_file.exists()
    assert daily_file.exists()

    # Check detailed data
    with open(detailed_file) as f:
        detailed_data = json.load(f)
        assert len(detailed_data) == 1
        assert detailed_data[0]["unique_devices"] == SAMPLE_UNIQUE_DEVICES

def test_load_history(temp_data_dir, sample_scan_result):
    from app.persistence import DataPersistence

    persistence = DataPersistence(data_dir=temp_data_dir)

    # Save some test data
    history = [sample_scan_result]
    persistence.save_history(history)

    # Load and verify
    loaded_history = persistence.load_history()
    assert len(loaded_history) == 1
    assert loaded_history[0].unique_devices == SAMPLE_UNIQUE_DEVICES
    assert loaded_history[0].ios_devices == SAMPLE_IOS_DEVICES
    assert loaded_history[0].other_devices == SAMPLE_OTHER_DEVICES
    assert loaded_history[0].manufacturer_stats == {"Apple": SAMPLE_IOS_DEVICES, "Nordic": SAMPLE_OTHER_DEVICES}

def test_load_history_empty_file(temp_data_dir):
    from app.persistence import DataPersistence

    persistence = DataPersistence(data_dir=temp_data_dir)
    history = persistence.load_history()
    assert len(history) == 0

def test_load_history_corrupted_file(temp_data_dir):
    from app.persistence import DataPersistence

    # Create corrupted JSON file
    detailed_file = Path(temp_data_dir) / "scan_history_detailed.json"
    with open(detailed_file, 'w') as f:
        f.write("invalid json")

    persistence = DataPersistence(data_dir=temp_data_dir)
    history = persistence.load_history()
    assert len(history) == 0

def test_should_save_timing():
    from app.persistence import DataPersistence

    persistence = DataPersistence()

    # Should not save initially (just created)
    assert persistence.should_save() is False

    # Set last_save to 61 minutes ago
    persistence.last_save = datetime.now() - timedelta(minutes=61)
    assert persistence.should_save() is True

    # Update last_save to now
    persistence.last_save = datetime.now()
    assert persistence.should_save() is False

def test_save_history_file_permission_error(temp_data_dir, sample_scan_result):
    from app.persistence import DataPersistence

    persistence = DataPersistence(data_dir=temp_data_dir)
    history = [sample_scan_result]

    # Mock _atomic_write to raise permission error
    with patch.object(persistence, '_atomic_write', side_effect=PermissionError):
        with pytest.raises(PermissionError):
            persistence.save_history(history)

def test_multiple_scan_results(temp_data_dir):
    from app.persistence import DataPersistence

    persistence = DataPersistence(data_dir=temp_data_dir)
    now = datetime.now()

    # Create multiple scan results within the last 24 hours
    results = [
        ScanResult(
            timestamp=now - timedelta(minutes=i),
            unique_devices=i+3,
            ios_devices=i+2,
            other_devices=i+1,
            manufacturer_stats={"Apple": i+2, "Nordic": i+1}
        )
        for i in range(TEST_RESULTS_COUNT)
    ]

    persistence.save_history(results)
    loaded_results = persistence.load_history()

    # Since all results are within 24 hours, they should be in detailed data
    assert len(loaded_results) == TEST_RESULTS_COUNT

    # Sort both lists by timestamp for comparison
    results.sort(key=lambda x: x.timestamp)
    loaded_results.sort(key=lambda x: x.timestamp)

    for original, loaded in zip(results, loaded_results, strict=False):
        assert loaded.unique_devices == original.unique_devices
        assert loaded.ios_devices == original.ios_devices
        assert loaded.other_devices == original.other_devices
        assert loaded.manufacturer_stats == original.manufacturer_stats

def test_data_aggregation(temp_data_dir):
    from app.persistence import DataPersistence

    persistence = DataPersistence(data_dir=temp_data_dir)
    now = datetime.now()

    # Create data for different time periods
    results = []

    # Last 24 hours - detailed data
    for i in range(HOURS_IN_DAY):
        results.append(ScanResult(
            timestamp=now - timedelta(hours=i),
            unique_devices=10,
            ios_devices=5,
            other_devices=5,
            manufacturer_stats={"Apple": 5, "Nordic": 5}
        ))

    # 2-7 days ago - hourly data
    for day in range(2, DAYS_IN_WEEK + 1):
        for hour in range(HOURS_IN_DAY):
            results.append(ScanResult(
                timestamp=now - timedelta(days=day, hours=hour),
                unique_devices=20,
                ios_devices=10,
                other_devices=10,
                manufacturer_stats={"Apple": 10, "Nordic": 10}
            ))

    # 8-14 days ago - daily data
    for i in range(DAYS_IN_WEEK + 1, DAYS_AFTER_WEEK + 1):
        for hour in range(HOURS_IN_DAY):
            results.append(ScanResult(
                timestamp=now - timedelta(days=i, hours=hour),
                unique_devices=30,
                ios_devices=15,
                other_devices=15,
                manufacturer_stats={"Apple": 15, "Nordic": 15}
            ))

    persistence.save_history(results)
    loaded_results = persistence.load_history()

    # Verify data is properly aggregated
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=DAYS_IN_WEEK)

    detailed_data = [r for r in loaded_results if r.timestamp >= day_ago]
    hourly_data = [r for r in loaded_results if day_ago > r.timestamp >= week_ago]
    daily_data = [r for r in loaded_results if r.timestamp < week_ago]

    assert len(detailed_data) == HOURS_IN_DAY  # One entry per hour for last 24 hours
    assert len(hourly_data) == 5 * HOURS_IN_DAY  # 5 days of hourly data (days 2-6)
    assert len(daily_data) == DAYS_IN_WEEK  # 7 days of daily data (days 8-14)