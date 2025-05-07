"""
Data persistence module for saving and loading scan history.
"""
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ScanResult:
    timestamp: datetime
    total_devices: int
    unique_devices: int
    ios_devices: int
    other_devices: int
    manufacturer_stats: dict[str, int]

class DataPersistence:
    def __init__(self, data_dir: str = "/data") -> None:
        """
        Initialize data persistence with a storage directory.

        Args:
            data_dir: Directory where data will be stored
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "scan_history.json"
        self.last_save_time = datetime.now()

    def save_history(self, history: list[ScanResult]) -> None:
        """
        Save scan history to disk.

        Args:
            history: List of ScanResult objects to save
        """
        try:
            # Convert datetime objects to ISO format strings
            serializable_history = []
            for result in history:
                result_dict = asdict(result)
                result_dict['timestamp'] = result_dict['timestamp'].isoformat()
                serializable_history.append(result_dict)

            # Save to file
            with open(self.history_file, 'w') as f:
                json.dump(serializable_history, f)

            self.last_save_time = datetime.now()
            logger.info(f"Successfully saved {len(history)} scan results to {self.history_file}")

        except Exception as e:
            logger.error(f"Failed to save scan history: {e!s}")
            raise

    def load_history(self) -> list[ScanResult]:
        """
        Load scan history from disk.

        Returns:
            List of ScanResult objects
        """
        try:
            if not self.history_file.exists():
                logger.info("No existing history file found")
                return []

            with open(self.history_file) as f:
                history_data = json.load(f)

            # Convert ISO format strings back to datetime objects
            history = []
            for result_dict in history_data:
                result_dict['timestamp'] = datetime.fromisoformat(result_dict['timestamp'])
                history.append(ScanResult(**result_dict))

            logger.info(f"Successfully loaded {len(history)} scan results from {self.history_file}")
            return history

        except Exception as e:
            logger.error(f"Failed to load scan history: {e!s}")
            return []

    def should_save(self, interval_minutes: int = 60) -> bool:
        """
        Check if it's time to save based on the last save time.

        Args:
            interval_minutes: Minimum minutes between saves

        Returns:
            bool: True if it's time to save
        """
        time_since_last_save = datetime.now() - self.last_save_time
        return time_since_last_save.total_seconds() >= interval_minutes * 60