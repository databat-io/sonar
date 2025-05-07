import pytest
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
from app.persistence import DataPersistence, ScanResult
from unittest.mock import patch, mock_open

@pytest.fixture
def sample_scan_result():
    return ScanResult(
        timestamp=datetime.now(),
        total_devices=10,
        unique_devices=8,
        ios_devices=5,
        other_devices=3,
        manufacturer_stats={"Apple": 5, "Nordic": 3}
    )

@pytest.fixture
def temp_data_dir(tmp_path):
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    return str(data_dir)

def test_init_creates_directory(temp_data_dir):
    persistence = DataPersistence(data_dir=temp_data_dir)
    assert Path(temp_data_dir).exists()
    assert Path(temp_data_dir).is_dir()

def test_save_history(temp_data_dir, sample_scan_result):
    persistence = DataPersistence(data_dir=temp_data_dir)
    history = [sample_scan_result]
    persistence.save_history(history)

    # Verify file exists and contains valid JSON
    history_file = Path(temp_data_dir) / "scan_history.json"
    assert history_file.exists()

    with open(history_file, 'r') as f:
        saved_data = json.load(f)

    assert len(saved_data) == 1
    assert saved_data[0]['total_devices'] == 10
    assert saved_data[0]['unique_devices'] == 8
    assert saved_data[0]['ios_devices'] == 5
    assert saved_data[0]['manufacturer_stats'] == {"Apple": 5, "Nordic": 3}

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
    assert loaded_result.total_devices == 10
    assert loaded_result.unique_devices == 8
    assert loaded_result.ios_devices == 5
    assert loaded_result.manufacturer_stats == {"Apple": 5, "Nordic": 3}

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

    # Should save initially
    assert persistence.should_save(interval_minutes=60) is False

    # Simulate time passing
    persistence.last_save_time = datetime.now() - timedelta(minutes=61)
    assert persistence.should_save(interval_minutes=60) is True

    persistence.last_save_time = datetime.now() - timedelta(minutes=30)
    assert persistence.should_save(interval_minutes=60) is False

def test_save_history_file_permission_error(temp_data_dir, sample_scan_result):
    persistence = DataPersistence(data_dir=temp_data_dir)
    history = [sample_scan_result]

    # Simulate permission error
    with patch('builtins.open', side_effect=PermissionError):
        with pytest.raises(Exception):
            persistence.save_history(history)

def test_multiple_scan_results(temp_data_dir):
    persistence = DataPersistence(data_dir=temp_data_dir)

    # Create multiple scan results
    results = [
        ScanResult(
            timestamp=datetime.now() - timedelta(minutes=i),
            total_devices=i+5,
            unique_devices=i+3,
            ios_devices=i+2,
            other_devices=i+1,
            manufacturer_stats={"Apple": i+2, "Nordic": i+1}
        )
        for i in range(3)
    ]

    persistence.save_history(results)
    loaded_results = persistence.load_history()

    assert len(loaded_results) == 3
    for original, loaded in zip(results, loaded_results):
        assert loaded.total_devices == original.total_devices
        assert loaded.unique_devices == original.unique_devices
        assert loaded.ios_devices == original.ios_devices
        assert loaded.manufacturer_stats == original.manufacturer_stats