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

- Python 3.9+
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

```bash
docker build -t ble-counter .
docker run --privileged ble-counter
```

Note: The `--privileged` flag is required to access Bluetooth hardware from within the container.

## API Endpoints

### `/scan`
- **Method**: GET
- **Parameters**:
  - `timeout` (optional): Scan duration in seconds (default: 10)
- **Returns**: Current scan results and historical statistics

### `/time-series`
- **Method**: GET
- **Parameters**:
  - `interval_minutes` (optional): Time interval between data points (default: 60)
- **Returns**: Time-series data for the last 24 hours, suitable for generating charts

### `/health`
- **Method**: GET
- **Returns**: System health status and Bluetooth availability

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
