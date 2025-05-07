"""
Data aggregation module for managing historical scan data.
"""
from datetime import datetime, timedelta

from .models import ScanResult


def aggregate_hourly(results: list[ScanResult]) -> list[ScanResult]:
    """
    Aggregate scan results into hourly averages.

    Args:
        results: List of ScanResult objects to aggregate

    Returns:
        List of ScanResult objects with hourly averages
    """
    if not results:
        return []

    # Group results by hour
    hourly_groups: dict[datetime, list[ScanResult]] = {}
    for result in results:
        hour_key = result.timestamp.replace(minute=0, second=0, microsecond=0)
        if hour_key not in hourly_groups:
            hourly_groups[hour_key] = []
        hourly_groups[hour_key].append(result)

    # Calculate averages for each hour
    aggregated_results = []
    for hour, group in hourly_groups.items():
        # Calculate averages for device counts
        unique_devices = sum(r.unique_devices for r in group) / len(group)
        ios_devices = sum(r.ios_devices for r in group) / len(group)
        other_devices = sum(r.other_devices for r in group) / len(group)

        # Aggregate manufacturer stats
        manufacturer_stats: dict[str, float] = {}
        for result in group:
            for manufacturer, count in result.manufacturer_stats.items():
                if manufacturer not in manufacturer_stats:
                    manufacturer_stats[manufacturer] = 0
                manufacturer_stats[manufacturer] += count
        # Calculate averages
        for manufacturer in manufacturer_stats:
            manufacturer_stats[manufacturer] /= len(group)

        # Aggregate session stats
        session_stats = {
            "total_sessions": sum(r.session_stats["total_sessions"] for r in group) / len(group),
            "active_sessions": sum(r.session_stats["active_sessions"] for r in group) / len(group),
            "average_dwell_time": sum(r.session_stats["average_dwell_time"] for r in group) / len(group)
        }

        aggregated_results.append(ScanResult(
            timestamp=hour,
            unique_devices=round(unique_devices),
            ios_devices=round(ios_devices),
            other_devices=round(other_devices),
            manufacturer_stats={k: round(v) for k, v in manufacturer_stats.items()},
            session_stats=session_stats
        ))

    return sorted(aggregated_results, key=lambda x: x.timestamp)

def aggregate_daily(results: list[ScanResult]) -> list[ScanResult]:
    """
    Aggregate scan results into daily averages.

    Args:
        results: List of ScanResult objects to aggregate

    Returns:
        List of ScanResult objects with daily averages
    """
    if not results:
        return []

    # Group results by day
    daily_groups: dict[datetime, list[ScanResult]] = {}
    for result in results:
        day_key = result.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        if day_key not in daily_groups:
            daily_groups[day_key] = []
        daily_groups[day_key].append(result)

    # Calculate averages for each day
    aggregated_results = []
    for day, group in daily_groups.items():
        # Calculate averages for device counts
        unique_devices = sum(r.unique_devices for r in group) / len(group)
        ios_devices = sum(r.ios_devices for r in group) / len(group)
        other_devices = sum(r.other_devices for r in group) / len(group)

        # Aggregate manufacturer stats
        manufacturer_stats: dict[str, float] = {}
        for result in group:
            for manufacturer, count in result.manufacturer_stats.items():
                if manufacturer not in manufacturer_stats:
                    manufacturer_stats[manufacturer] = 0
                manufacturer_stats[manufacturer] += count
        # Calculate averages
        for manufacturer in manufacturer_stats:
            manufacturer_stats[manufacturer] /= len(group)

        # Aggregate session stats
        session_stats = {
            "total_sessions": sum(r.session_stats["total_sessions"] for r in group) / len(group),
            "active_sessions": sum(r.session_stats["active_sessions"] for r in group) / len(group),
            "average_dwell_time": sum(r.session_stats["average_dwell_time"] for r in group) / len(group)
        }

        aggregated_results.append(ScanResult(
            timestamp=day,
            unique_devices=round(unique_devices),
            ios_devices=round(ios_devices),
            other_devices=round(other_devices),
            manufacturer_stats={k: round(v) for k, v in manufacturer_stats.items()},
            session_stats=session_stats
        ))

    return sorted(aggregated_results, key=lambda x: x.timestamp)

def get_aggregated_history(results: list[ScanResult]) -> dict[str, list[ScanResult]]:
    """
    Get aggregated history with different time granularities.

    Args:
        results: List of all ScanResult objects

    Returns:
        Dictionary containing:
        - detailed: Last 24 hours of detailed data
        - hourly: Data between 24 hours and 7 days, aggregated hourly
        - daily: Data older than 7 days, aggregated daily
    """
    now = datetime.now()
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    # Sort results by timestamp
    sorted_results = sorted(results, key=lambda x: x.timestamp)

    # Split data into time periods
    detailed_data = [r for r in sorted_results if r.timestamp >= day_ago]
    hourly_data = [r for r in sorted_results if day_ago > r.timestamp >= week_ago]
    daily_data = [r for r in sorted_results if r.timestamp < week_ago]

    # Aggregate data
    hourly_aggregated = aggregate_hourly(hourly_data)
    daily_aggregated = aggregate_daily(daily_data)

    # For daily data, keep only the last 7 days
    if daily_aggregated:
        daily_aggregated = sorted(daily_aggregated, key=lambda x: x.timestamp, reverse=True)[:7]
        daily_aggregated = sorted(daily_aggregated, key=lambda x: x.timestamp)

    return {
        "detailed": detailed_data,
        "hourly": hourly_aggregated,
        "daily": daily_aggregated
    }