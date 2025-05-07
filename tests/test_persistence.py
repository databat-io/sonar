import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from app.persistence import DataPersistence, ScanResult

# Test constants
SAMPLE_UNIQUE_DEVICES = 8
SAMPLE_IOS_DEVICES = 5
SAMPLE_OTHER_DEVICES = 3
SAVE_INTERVAL_MINUTES = 60
TEST_RESULTS_COUNT = 3

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

def test_init_creates_directory(temp_data_dir):
    DataPersistence(data_dir=temp_data_dir)
    assert Path(temp_data_dir).exists()
    assert Path(temp_data_dir).is_dir()

def test_save_history(temp_data_dir, sample_scan_result):
    persistence = DataPersistence(data_dir=temp_data_dir)
    history = [sample_scan_result]
    persistence.save_history(history)

    # Verify file exists and contains valid JSON
    history_file = Path(temp_data_dir) / "scan_history.json"
    assert history_file.exists()

    with open(history_file) as f:
        saved_data = json.load(f)

    assert len(saved_data) == 1
    assert saved_data[0]['unique_devices'] == SAMPLE_UNIQUE_DEVICES
    assert saved_data[0]['ios_devices'] == SAMPLE_IOS_DEVICES
    assert saved_data[0]['manufacturer_stats'] == {"Apple": SAMPLE_IOS_DEVICES, "Nordic": SAMPLE_OTHER_DEVICES}

def test_load_history(temp_data_dir, sample_scan_result):
    persistence = DataPersistence(data_dir=temp_data_dir)

    # First save some data
    history = [sample_scan_result]
    persistence.save_history(history)

    # Then load it back
    loaded_history = persistence.load_history()

    assert len(loaded_history) == 1
    loaded_result = loaded_history[0]
    assert isinstance(loaded_result, ScanResult)
    assert loaded_result.unique_devices == SAMPLE_UNIQUE_DEVICES
    assert loaded_result.ios_devices == SAMPLE_IOS_DEVICES
    assert loaded_result.manufacturer_stats == {"Apple": SAMPLE_IOS_DEVICES, "Nordic": SAMPLE_OTHER_DEVICES}

def test_load_history_empty_file(temp_data_dir):
    persistence = DataPersistence(data_dir=temp_data_dir)
    history = persistence.load_history()
    assert history == []

def test_load_history_corrupted_file(temp_data_dir):
    persistence = DataPersistence(data_dir=temp_data_dir)
    history_file = Path(temp_data_dir) / "scan_history.json"

    # Write corrupted JSON
    with open(history_file, 'w') as f:
        f.write("invalid json content")

    history = persistence.load_history()
    assert history == []

def test_should_save_timing():
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
    persistence = DataPersistence(data_dir=temp_data_dir)
    history = [sample_scan_result]

    # Simulate permission error
    with patch('builtins.open', side_effect=PermissionError("Permission denied")):
        with pytest.raises(PermissionError, match="Permission denied"):
            persistence.save_history(history)

def test_multiple_scan_results(temp_data_dir):
    persistence = DataPersistence(data_dir=temp_data_dir)

    # Create multiple scan results
    results = [
        ScanResult(
            timestamp=datetime.now() - timedelta(minutes=i),
            unique_devices=i+3,
            ios_devices=i+2,
            other_devices=i+1,
            manufacturer_stats={"Apple": i+2, "Nordic": i+1}
        )
        for i in range(TEST_RESULTS_COUNT)
    ]

    persistence.save_history(results)
    loaded_results = persistence.load_history()

    assert len(loaded_results) == TEST_RESULTS_COUNT
    for original, loaded in zip(results, loaded_results, strict=False):
        assert loaded.unique_devices == original.unique_devices
        assert loaded.ios_devices == original.ios_devices
        assert loaded.manufacturer_stats == original.manufacturer_stats