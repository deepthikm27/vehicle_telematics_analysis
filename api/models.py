from pydantic import BaseModel
from datetime import datetime

class VehicleTelemetry(BaseModel):
    vehicle_id: str
    timestamp: datetime
    speed_kmh: float
    rpm: int
    fuel_level_percent: float
    engine_temp_c: float
    latitude: float
    longitude: float
    oil_pressure_psi: float
    battery_voltage_v: float
    soc_percent: float
    odometer_km: float

