# BLE Device Counter

A FastAPI-based service for counting and analyzing Bluetooth Low Energy (BLE) devices in proximity. This service provides detailed statistics about nearby BLE devices, including manufacturer identification and device type classification.

## Features

- Real-time BLE device scanning and counting
- Manufacturer identification using Nordic Semiconductor's database
- iOS device detection
- Time-series data collection and analysis
- Historical data persistence
- RESTful API endpoints for data access
- Docker support with persistent storage

## Requirements

- Python 3.11+
- BlueZ (Linux Bluetooth stack)
- Bluetooth hardware with BLE support
- Proper permissions to access Bluetooth (usually requires root or special capabilities)

## Installation

1. Clone the repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Application

### Local Development

```bash
uvicorn app.main:app --reload
```

### Docker

The application is configured to run in a Docker container with all necessary Bluetooth access permissions. Use docker-compose to run the service:

```bash
docker-compose up -d
```

The docker-compose configuration includes:
- Host network mode for Bluetooth access
- Required volume mounts for Bluetooth and D-Bus
- USB device access for Bluetooth hardware
- Privileged mode for system access
- Automatic container restart
- Persistent data storage

To stop the service:
```bash
docker-compose down
```

## API Endpoints

### `/scan`
- **Method**: GET
- **Parameters**:
  - `timeout` (optional): Scan duration in seconds (default: 10)
- **Returns**: Current scan results and historical statistics
- **Example Response**:
```json
{
  "current_scan": {
    "total_devices": 15,
    "unique_devices": 12,
    "ios_devices": 8,
    "other_devices": 4,
    "manufacturer_stats": {
      "Apple Inc.": 8,
      "Nordic Semiconductor": 3,
      "Unknown": 1
    },
    "scan_duration_seconds": 10
  },
  "last_hour": {
    "average_total_devices": 14.5,
    "average_unique_devices": 11.2,
    "peak_total_devices": 18,
    "peak_unique_devices": 15
  },
  "last_24h": {
    "average_total_devices": 12.8,
    "average_unique_devices": 10.5,
    "peak_total_devices": 20,
    "peak_unique_devices": 16
  }
}
```

### `/time-series`
- **Method**: GET
- **Parameters**:
  - `interval_minutes` (optional): Time interval between data points (default: 60)
- **Returns**: Time-series data for the last 24 hours, suitable for generating charts
- **Example Response**:
```json
{
  "interval_minutes": 60,
  "time_series": [
    {
      "timestamp": "2024-02-20T10:00:00Z",
      "total_devices": 15,
      "unique_devices": 12,
      "ios_devices": 8,
      "other_devices": 4,
      "manufacturer_stats": {
        "Apple Inc.": 8,
        "Nordic Semiconductor": 3,
        "Unknown": 1
      }
    }
  ],
  "summary": {
    "average_total_devices": 14.5,
    "average_unique_devices": 11.2,
    "peak_total_devices": 18,
    "peak_unique_devices": 15
  },
  "manufacturer_summary": {
    "Apple Inc.": 8,
    "Nordic Semiconductor": 3,
    "Unknown": 1
  }
}
```

### `/health`
- **Method**: GET
- **Returns**: System health status and Bluetooth availability
- **Example Response**:
```json
{
  "status": "healthy",
  "message": "System requirements met",
  "bluetooth": {
    "version": "5.66",
    "controller": "00:11:22:33:44:55",
    "powered": true
  }
}
```

## Data Persistence

The service automatically:
- Saves scan history to disk every hour
- Loads historical data on startup
- Maintains data across container restarts
- Stores data in a Docker volume for persistence

## Docker Setup

### Prerequisites
- Docker and Docker Compose
- Bluetooth hardware access
- Linux host system (for Bluetooth support)

### Running with Docker Compose

1. Build and start the container:
```bash
docker-compose up -d
```

2. Access the API:
```bash
curl http://localhost:8000/scan
```

### Data Backup

To backup the scan history:
```bash
docker run --rm -v ble_data:/data -v $(pwd):/backup ubuntu tar czf /backup/ble_data_backup.tar.gz /data
```

To restore from backup:
```bash
docker run --rm -v ble_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/ble_data_backup.tar.gz -C /
```

## Development

### Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the development server:
```bash
uvicorn app.main:app --reload
```

### Testing

Run the test suite:
```bash
pytest
```

## License

MIT License
