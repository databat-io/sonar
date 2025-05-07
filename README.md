# BLE Device Counter

## Quickstart

1. **Clone the repository:**

```bash
git clone https://github.com/viktopia/sonar.git
cd sonar
```

2. **On a Raspberry Pi (or any BlueZ-compatible Linux device):**

- **With Docker (recommended):**

```bash
docker-compose up -d --build
```

- **Or, run locally:**

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

3. **Access the API:**

run `curl http://[device-ip]:8000/latest` to see statistics

> **Note:** This project is primarily designed to run on a Raspberry Pi, but should in theory work on any other device with a BlueZ-compatible Bluetooth interface and the required permissions.

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

### GET /latest
Returns the most recent scan results and historical statistics. The scanning is performed automatically in the background every minute.

Response:
```json
{
    "current_scan": {
        "total_devices": 10,
        "unique_devices": 8,
        "ios_devices": 5,
        "other_devices": 3,
        "manufacturer_stats": {
            "Apple Inc.": 5,
            "Nordic Semiconductor ASA": 3
        },
        "scan_duration_seconds": 10
    },
    "last_hour": {
        "average_total_devices": 9.5,
        "average_unique_devices": 7.5,
        "average_ios_devices": 4.5,
        "average_other_devices": 3.0,
        "peak_total_devices": 12,
        "peak_unique_devices": 9,
        "peak_ios_devices": 6,
        "peak_other_devices": 3,
        "manufacturer_stats": {
            "Apple Inc.": 5.5,
            "Nordic Semiconductor ASA": 3.0
        }
    },
    "last_24h": {
        // Similar structure to last_hour
    }
}
```

### GET /time-series
Get time series data for the last 24 hours, suitable for generating bar charts.

Query Parameters:
- `interval_minutes`: Time interval between data points (default: 60, min: 1, max: 1440)

Response:
```json
{
    "interval_minutes": 60,
    "time_series": [
        {
            "timestamp": "2024-03-20T10:00:00",
            "total_devices": 10,
            "unique_devices": 8,
            "ios_devices": 5,
            "other_devices": 3,
            "manufacturer_stats": {
                "Apple Inc.": 5,
                "Nordic Semiconductor ASA": 3
            }
        }
        // ... more time slots
    ],
    "summary": {
        "total_devices": {
            "min": 5,
            "max": 15,
            "avg": 10.2
        },
        // ... similar stats for other metrics
    },
    "manufacturer_summary": {
        "Apple Inc.": {
            "min": 3,
            "max": 8,
            "avg": 5.5
        }
        // ... similar stats for other manufacturers
    }
}
```

### GET /health
Simple health check endpoint that verifies system requirements.

Response:
```json
{
    "status": "healthy",
    "message": "System requirements met"
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
