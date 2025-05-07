"""
Data persistence module for saving and loading scan history.
"""
import json
import logging
import os
import tempfile
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path

from .aggregation import get_aggregated_history
from .models import ScanResult

logger = logging.getLogger(__name__)

class DataPersistence:
    """Handles saving and loading scan history."""
    def __init__(self, data_dir: str = "/data", save_interval_minutes: int = 60) -> None:
        """
        Initialize data persistence with a storage directory.

        Args:
            data_dir: Directory where data will be stored
            save_interval_minutes: Minimum minutes between saves
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.detailed_file = self.data_dir / "scan_history_detailed.json"
        self.hourly_file = self.data_dir / "scan_history_hourly.json"
        self.daily_file = self.data_dir / "scan_history_daily.json"
        self.save_interval = timedelta(minutes=save_interval_minutes)
        self.last_save = datetime.now()

    def _serialize_results(self, results: list[ScanResult]) -> list[dict]:
        """Convert ScanResult objects to serializable dictionaries."""
        serializable = []
        for result in results:
            result_dict = asdict(result)
            result_dict['timestamp'] = result_dict['timestamp'].isoformat()
            serializable.append(result_dict)
        return serializable

    def _deserialize_results(self, data: list[dict]) -> list[ScanResult]:
        """Convert serialized dictionaries back to ScanResult objects."""
        results = []
        for result_dict in data:
            result_dict['timestamp'] = datetime.fromisoformat(result_dict['timestamp'])
            results.append(ScanResult(**result_dict))
        return results

    def _atomic_write(self, file_path: Path, data: list[dict]) -> None:
        """
        Write data to a file atomically using a temporary file and rename.

        Args:
            file_path: Path to the target file
            data: Data to write (must be JSON serializable)
        """
        # Create a temporary file in the same directory as the target file
        temp_fd, temp_path = tempfile.mkstemp(dir=str(file_path.parent))
        try:
            with os.fdopen(temp_fd, 'w') as temp_file:
                json.dump(data, temp_file)
            # Perform atomic rename
            os.replace(temp_path, file_path)
        except Exception:
            # Clean up the temporary file if anything goes wrong
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    def save_history(self, history: list[ScanResult]) -> None:
        """
        Save scan history to disk with different granularities.

        Args:
            history: List of ScanResult objects to save
        """
        try:
            # Get aggregated history
            aggregated = get_aggregated_history(history)

            # Save detailed data (last 24 hours)
            self._atomic_write(self.detailed_file, self._serialize_results(aggregated["detailed"]))

            # Save hourly aggregated data (24h to 7 days)
            self._atomic_write(self.hourly_file, self._serialize_results(aggregated["hourly"]))

            # Save daily aggregated data (older than 7 days)
            self._atomic_write(self.daily_file, self._serialize_results(aggregated["daily"]))

            self.last_save = datetime.now()
            logger.info("Successfully saved scan results with different granularities")

        except Exception as e:
            logger.error(f"Failed to save scan history: {e!s}")
            raise

    def load_history(self) -> list[ScanResult]:
        """
        Load scan history from disk, combining all granularities.

        Returns:
            List of ScanResult objects
        """
        try:
            all_results = []

            # Load detailed data
            if self.detailed_file.exists():
                with open(self.detailed_file) as f:
                    detailed_data = json.load(f)
                all_results.extend(self._deserialize_results(detailed_data))

            # Load hourly aggregated data
            if self.hourly_file.exists():
                with open(self.hourly_file) as f:
                    hourly_data = json.load(f)
                all_results.extend(self._deserialize_results(hourly_data))

            # Load daily aggregated data
            if self.daily_file.exists():
                with open(self.daily_file) as f:
                    daily_data = json.load(f)
                all_results.extend(self._deserialize_results(daily_data))

            # Sort all results by timestamp
            all_results.sort(key=lambda x: x.timestamp)

            logger.info(f"Successfully loaded {len(all_results)} scan results")
            return all_results

        except Exception as e:
            logger.error(f"Failed to load scan history: {e!s}")
            return []

    def should_save(self) -> bool:
        """Check if enough time has passed since last save."""
        return datetime.now() - self.last_save >= self.save_interval