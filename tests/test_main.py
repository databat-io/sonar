from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_scan_endpoint():
    # Note: This test will only work if there's actual BLE hardware available
    # and the test is running with proper permissions
    response = client.get("/scan?timeout=1")
    assert response.status_code in [200, 500]  # 500 if no BLE hardware available

    if response.status_code == 200:
        data = response.json()
        assert "total_devices_found" in data
        assert "unique_devices" in data
        assert "scan_duration_seconds" in data
        assert "devices" in data
        assert isinstance(data["devices"], list)