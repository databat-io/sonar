"""
Tests for the data aggregation module.
"""
from datetime import datetime, timedelta

import pytest

from app.aggregation import aggregate_daily, aggregate_hourly, get_aggregated_history
from app.models import ScanResult

# Constants for test values
HOURS_IN_DAY = 24
DAYS_IN_WEEK = 7
DAYS_BEFORE_WEEK = 6  # Days 2-7 for hourly data
DAYS_AFTER_WEEK = 13  # Days 8-14 for daily data
EXPECTED_DAILY_DAYS = 12  # Days 2-13 for daily aggregation
EXPECTED_AGGREGATED_DAILY_DAYS = 6  # Days 8-13 for aggregated daily data

@pytest.fixture
def sample_scan_results():
    """Create sample scan results for testing."""
    now = datetime.now()
    results = []

    # Create detailed data (last 24 hours)
    for i in range(HOURS_IN_DAY):
        results.append(ScanResult(
            timestamp=now - timedelta(hours=i),
            unique_devices=10 + i,
            ios_devices=5 + i,
            other_devices=5,
            manufacturer_stats={"Apple": 5 + i, "Nordic": 5},
            session_stats={
                "total_sessions": 10 + i,
                "active_sessions": 5 + i,
                "average_dwell_time": 300 + i
            }
        ))

    # Create data between 24h and 7 days
    for i in range(1, DAYS_IN_WEEK):
        results.append(ScanResult(
            timestamp=now - timedelta(days=i),
            unique_devices=20 + i,
            ios_devices=10 + i,
            other_devices=10,
            manufacturer_stats={"Apple": 10 + i, "Nordic": 10},
            session_stats={
                "total_sessions": 20 + i,
                "active_sessions": 10 + i,
                "average_dwell_time": 400 + i
            }
        ))

    # Create data older than 7 days
    for i in range(DAYS_IN_WEEK, DAYS_AFTER_WEEK):
        results.append(ScanResult(
            timestamp=now - timedelta(days=i),
            unique_devices=30 + i,
            ios_devices=15 + i,
            other_devices=15,
            manufacturer_stats={"Apple": 15 + i, "Nordic": 15},
            session_stats={
                "total_sessions": 30 + i,
                "active_sessions": 15 + i,
                "average_dwell_time": 500 + i
            }
        ))

    return results

def test_aggregate_hourly(sample_scan_results):
    """Test hourly aggregation."""
    # Get results from last 24 hours
    now = datetime.now()
    day_ago = now - timedelta(days=1)
    hourly_data = [r for r in sample_scan_results if r.timestamp >= day_ago]

    # Aggregate hourly
    aggregated = aggregate_hourly(hourly_data)

    # Check results
    assert len(aggregated) == HOURS_IN_DAY  # One result per hour
    assert all(isinstance(r, ScanResult) for r in aggregated)
    assert all(r.unique_devices > 0 for r in aggregated)
    assert all(r.ios_devices > 0 for r in aggregated)
    assert all(r.other_devices > 0 for r in aggregated)
    assert all("Apple" in r.manufacturer_stats for r in aggregated)
    assert all("Nordic" in r.manufacturer_stats for r in aggregated)
    assert all(r.session_stats["total_sessions"] > 0 for r in aggregated)
    assert all(r.session_stats["active_sessions"] > 0 for r in aggregated)
    assert all(r.session_stats["average_dwell_time"] > 0 for r in aggregated)

def test_aggregate_daily(sample_scan_results):
    """Test daily aggregation."""
    # Get results older than 24 hours
    now = datetime.now()
    day_ago = now - timedelta(days=1)
    daily_data = [r for r in sample_scan_results if r.timestamp < day_ago]

    # Aggregate daily
    aggregated = aggregate_daily(daily_data)

    # Check results
    assert len(aggregated) == EXPECTED_DAILY_DAYS  # One result per day (days 2-13)
    assert all(isinstance(r, ScanResult) for r in aggregated)
    assert all(r.unique_devices > 0 for r in aggregated)
    assert all(r.ios_devices > 0 for r in aggregated)
    assert all(r.other_devices > 0 for r in aggregated)
    assert all("Apple" in r.manufacturer_stats for r in aggregated)
    assert all("Nordic" in r.manufacturer_stats for r in aggregated)
    assert all(r.session_stats["total_sessions"] > 0 for r in aggregated)
    assert all(r.session_stats["active_sessions"] > 0 for r in aggregated)
    assert all(r.session_stats["average_dwell_time"] > 0 for r in aggregated)

def test_get_aggregated_history(sample_scan_results):
    """Test getting aggregated history with different granularities."""
    aggregated = get_aggregated_history(sample_scan_results)

    # Check structure
    assert "detailed" in aggregated
    assert "hourly" in aggregated
    assert "daily" in aggregated

    # Check detailed data (last 24 hours)
    assert len(aggregated["detailed"]) == HOURS_IN_DAY
    assert all(r.timestamp >= datetime.now() - timedelta(days=1) for r in aggregated["detailed"])

    # Check hourly data (24h to 7 days)
    assert len(aggregated["hourly"]) == DAYS_BEFORE_WEEK  # 6 days of hourly data
    assert all(
        datetime.now() - timedelta(days=1) > r.timestamp >= datetime.now() - timedelta(days=DAYS_IN_WEEK)
        for r in aggregated["hourly"]
    )

    # Check daily data (older than 7 days)
    assert len(aggregated["daily"]) == EXPECTED_AGGREGATED_DAILY_DAYS  # 6 days of daily data (days 8-13)
    assert all(r.timestamp < datetime.now() - timedelta(days=DAYS_IN_WEEK) for r in aggregated["daily"])

def test_empty_data():
    """Test aggregation with empty data."""
    empty_results = []

    # Test hourly aggregation
    hourly = aggregate_hourly(empty_results)
    assert len(hourly) == 0

    # Test daily aggregation
    daily = aggregate_daily(empty_results)
    assert len(daily) == 0

    # Test getting aggregated history
    aggregated = get_aggregated_history(empty_results)
    assert len(aggregated["detailed"]) == 0
    assert len(aggregated["hourly"]) == 0
    assert len(aggregated["daily"]) == 0