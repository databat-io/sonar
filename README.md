# Sonar - BLE Device Counter

A FastAPI-based service for counting and analyzing Bluetooth Low Energy (BLE) devices in proximity. This service provides detailed statistics about nearby BLE devices, including manufacturer identification and device type classification.

## 📋 Features

- Real-time BLE device scanning and counting
- Manufacturer identification using Nordic Semiconductor's database
- iOS device detection
- Time-series data collection and analysis
- Historical data persistence
- RESTful API endpoints for data access
- Docker support with persistent storage

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- BlueZ (Linux Bluetooth stack)
- Bluetooth hardware with BLE support
- Proper permissions to access Bluetooth (usually requires root or special capabilities)

### Installation

1. **Clone the repository:**

```bash
git clone https://github.com/Viktopia/sonar.git
cd sonar
```

2. **Choose your installation method:**

### Docker (Recommended)

```bash
docker-compose up -d --build
```

### Local Installation

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

3. **Verify Installation:**

```bash
curl http://localhost:8000/health
```

> **Note:** This project is primarily designed to run on a Raspberry Pi but works on any BlueZ-compatible Linux device with proper Bluetooth permissions.

## 🛠️ Development

### Local Development Setup

1. **Install dependencies:**

```bash
pip install -r requirements.txt
```

2. **Run the development server:**

```bash
uvicorn app.main:app --reload
```

### Running Tests

```bash
# Run test suite
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing
```

## 📡 API Documentation

### Endpoints

#### GET /latest

Returns the most recent scan results and historical statistics.

**Response:**

```json
{
    "current_scan": {
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
        "average_unique_devices": 7.5,
        "average_ios_devices": 4.5,
        "average_other_devices": 3.0,
        "peak_unique_devices": 9,
        "peak_ios_devices": 6,
        "peak_other_devices": 3,
        "manufacturer_stats": {
            "Apple Inc.": 5.5,
            "Nordic Semiconductor ASA": 3.0
        }
    }
}
```

#### GET /time-series

Get time series data for the last 24 hours.

**Query Parameters:**

- `interval_minutes`: Time interval between data points (default: 60, min: 1, max: 1440)

**Response:**

```json
{
    "interval_minutes": 60,
    "time_series": [
        {
            "timestamp": "2024-03-20T10:00:00",
            "average_unique_devices": 8.0,
            "average_ios_devices": 5.0,
            "average_other_devices": 3.0,
            "peak_unique_devices": 9,
            "peak_ios_devices": 6,
            "peak_other_devices": 3,
            "manufacturer_stats": {
                "Apple Inc.": 5.0,
                "Nordic Semiconductor ASA": 3.0
            }
        }
    ]
}
```

#### GET /health

Health check endpoint.

**Response:**

```json
{
    "status": "healthy",
    "message": "System requirements met"
}
```

## 🐳 Docker Deployment

### Prerequisites

- Docker and Docker Compose
- Bluetooth hardware access
- Linux host system (for Bluetooth support)

### Running with Docker Compose

1. **Start the service:**

```bash
docker-compose up -d
```

2. **Access the API:**

```bash
curl http://localhost:8000/health
```

### Data Management

#### Backup

```bash
docker run --rm -v ble_data:/data -v $(pwd):/backup ubuntu tar czf /backup/ble_data_backup.tar.gz /data
```

#### Restore

```bash
docker run --rm -v ble_data:/data -v $(pwd):/backup ubuntu tar xzf /backup/ble_data_backup.tar.gz -C /
```

## 📊 Data Persistence

The service automatically:

- Saves scan history to disk every hour
- Loads historical data on startup
- Maintains data across container restarts
- Stores data in a Docker volume for persistence
