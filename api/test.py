# vehicle_telemetry/api/test.py
import httpx
import pytest
from datetime import datetime, timedelta, timezone

BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="module")
def client():
    # httpx.Client can automatically handle async test functions
    # by using `async with`
    with httpx.Client(base_url=BASE_URL) as client_instance:
        yield client_instance

# --- Test Cases ---

def test_read_root(client):
    """Test the root endpoint for a welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Real-Time Vehicle Telemetry API!"}

def test_list_metrics(client):
    """Test that the /metrics endpoint returns a list of available metrics."""
    response = client.get("/metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert isinstance(metrics, list)
    assert "speed_kmh" in metrics
    assert "fuel_level_percent" in metrics
    assert "soc_percent" in metrics # Verify the new metric is listed

def test_get_latest_telemetry_for_specific_vehicle(client):
    """Test /data/{vehicle_id} to get the latest data for V001."""
    vehicle_id = "V001"
    response = client.get(f"/data/{vehicle_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_id"] == vehicle_id
    assert "timestamp" in data
    assert "speed_kmh" in data
    assert "soc_percent" in data

def test_get_telemetry_data_all_latest(client):
    """Test /data with no parameters should return latest data for all vehicles."""
    response = client.get("/data")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Check if a few expected fields are present in the first record
    if data:
        assert "vehicle_id" in data[0]
        assert "timestamp" in data[0]
        assert "speed_kmh" in data[0]

def test_get_telemetry_data_time_series_for_single_vehicle(client):
    """
    Test /data with metric and time range for a specific vehicle.
    This should return multiple data points.
    """
    vehicle_id = "V002"
    metric = "rpm"
    now_utc = datetime.now(timezone.utc)
    from_ts = (now_utc - timedelta(minutes=10)).isoformat(timespec='milliseconds') + 'Z'
    to_ts = now_utc.isoformat(timespec='milliseconds') + 'Z'

    params = {
        "metric": metric,
        "vehicle_id": vehicle_id,
        "from_ts": from_ts,
        "to_ts": to_ts
    }
    response = client.get("/data", params=params)
    assert response.status_code == 200
    data = response.json()
    # Check if we get more than 1 record (should be ~120 for 2 mins)
    assert len(data) > 10 # Should be significantly more than 10 points
    
    # Check the structure of the returned data for time series (timestamp, metric_name, value)
    if data:
        assert "timestamp" in data[0]
        assert metric in data[0] # The metric should be directly in the dictionary
        assert "vehicle_id" in data[0] # Vehicle ID should also be present for grouping

