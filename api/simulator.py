import datetime
import random
import asyncio
from typing import List, Dict
from collections import deque # Import deque for efficient fixed-size collection

from api.models import VehicleTelemetry

data_lock = asyncio.Lock()

# Define how many total records to keep in memory.
# Example: 10 minutes * 60 seconds/minute * 1 record/sec/vehicle * NUM_VEHICLES
NUM_VEHICLES = 5 # Ensure this matches your actual NUM_VEHICLES if it's elsewhere
MAX_IN_MEMORY_RECORDS = 10 * 60 * NUM_VEHICLES # Holds ~10 minutes of data for all vehicles

telemetry_data_store: deque[VehicleTelemetry] = deque(maxlen=MAX_IN_MEMORY_RECORDS)
latest_telemetry_per_vehicle: Dict[str, VehicleTelemetry] = {}

VEHICLE_IDS = ["V001", "V002", "V003", "V004", "V005"] # Ensure this is defined or imported

def generate_single_telemetry_record(vehicle_id: str, base_timestamp: datetime.datetime) -> VehicleTelemetry:
    last = latest_telemetry_per_vehicle.get(vehicle_id)

    base_lat, base_lon = 12.9716, 77.5946 # Bangalore approximate

    # Initialize with default/random if no previous record exists
    last_speed = last.speed_kmh if last else random.uniform(20, 120)
    last_rpm = last.rpm if last else random.randint(1000, 5000)
    last_fuel_level = last.fuel_level_percent if last else random.uniform(10, 100)
    last_engine_temp = last.engine_temp_c if last else random.uniform(75, 105)
    last_lat = last.latitude if last else base_lat + random.uniform(-0.005, 0.005)
    last_lon = last.longitude if last else base_lon + random.uniform(-0.005, 0.005)
    last_oil_pressure = last.oil_pressure_psi if last else random.uniform(25, 55)
    last_voltage = last.battery_voltage_v if last else 13.5
    last_soc = last.soc_percent if last else random.uniform(0,100)
    last_odometer = last.odometer_km if last else random.uniform(10000, 150000)

    # Simulate realistic changes
    speed = round(min(120, max(20, last_speed + random.uniform(-5, 5))), 2)
    rpm = int(min(5000, max(1000, last_rpm + random.randint(-100, 100))))
    fuel_level = round(min(100, max(0, last_fuel_level - random.uniform(0.01, 0.05))), 1) # Slowly decrease
    engine_temp = round(min(105, max(75, last_engine_temp + random.uniform(-0.5, 0.5))), 1)
    lat = round(min(base_lat + 0.05, max(base_lat - 0.05, last_lat + random.uniform(-0.0001, 0.0001))), 6)
    lon = round(min(base_lon + 0.05, max(base_lon - 0.05, last_lon + random.uniform(-0.0001, 0.0001))), 6)
    oil_pressure = round(min(55, max(25, last_oil_pressure + random.uniform(-2, 2))), 1)
    battery_voltage = round(min(14.5, max(11.5, last_voltage + random.uniform(-0.3, 0.2))), 2)
    soc = round(min(100, max(0, last_soc + random.uniform(-30, 30))), 1)
    odometer = round(last_odometer + speed / 3600 * 1, 2) # Speed km/h * 1 second / 3600 seconds/hour

    return VehicleTelemetry(
        vehicle_id=vehicle_id,
        timestamp=base_timestamp,
        speed_kmh=speed,
        rpm=rpm,
        fuel_level_percent=fuel_level,
        engine_temp_c=engine_temp,
        latitude=lat,
        longitude=lon,
        oil_pressure_psi=oil_pressure,
        battery_voltage_v=battery_voltage,
        soc_percent=soc,
        odometer_km=odometer
    )

async def data_simulator_task():
    print("Telemetry simulator started (In-Memory Version)")
    global telemetry_data_store, latest_telemetry_per_vehicle

    # No need for complex initial records setup or pruning logic when using deque(maxlen).
    # The deque will automatically handle keeping only the latest MAX_IN_MEMORY_RECORDS.

    # Continuous data generation
    while True:
        await asyncio.sleep(1) # Sleeps for 1 second
        now = datetime.datetime.now(datetime.timezone.utc) # Get current UTC time
        
        new_records = []
        for vehicle_id in VEHICLE_IDS:
            record = generate_single_telemetry_record(vehicle_id, now)
            new_records.append(record)

        async with data_lock:
            # Use extend to add all new records
            telemetry_data_store.extend(new_records)
            
            # Update latest_telemetry_per_vehicle
            for r in new_records:
                latest_telemetry_per_vehicle[r.vehicle_id] = r
            
            # The deque's maxlen handles the pruning automatically.
            # No manual `telemetry_data_store = [r for r in ...]` needed here.