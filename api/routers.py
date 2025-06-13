from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from api.models import VehicleTelemetry
from api.simulator import telemetry_data_store, latest_telemetry_per_vehicle, VEHICLE_IDS, data_lock

router = APIRouter()

@router.get("/", summary="Root endpoint for the API")
async def read_root():
    return {"message": "Welcome to the Real-Time Vehicle Telemetry API!"}

@router.get("/metrics", response_model=List[str], summary="List available telemetry metrics")
async def list_metrics():
    metrics = []
    for field_name in VehicleTelemetry.model_fields:
        if field_name not in ["vehicle_id", "timestamp"]:  # Skip identifiers
            metrics.append(field_name)
    return metrics

@router.get("/data/{vehicle_id}", response_model=VehicleTelemetry, summary="Get latest telemetry data for a specific vehicle")
async def get_vehicle_telemetry(vehicle_id: str):
    if vehicle_id not in latest_telemetry_per_vehicle:
        raise HTTPException(status_code=404, detail=f"Telemetry data for vehicle '{vehicle_id}' not found.")
    return latest_telemetry_per_vehicle[vehicle_id]

def extract_metric(record: VehicleTelemetry, metric: str):
    return getattr(record, metric, None)

@router.get("/data", summary="Get telemetry data for specified vehicles and metrics")
async def get_metric_data(
    metric: Optional[str] = None,
    vehicle_id: Optional[str] = None,
    from_ts: Optional[datetime] = None,
    to_ts: Optional[datetime] = None,
    agg: Optional[str] = None,
):
    # Acquire lock for thread-safe access to telemetry_data_store
    async with data_lock:
        # Determine which records from the store to consider based on vehicle_id filter
        if vehicle_id: # If specific vehicle_ids are requested
            # Efficiently filter all records for the requested vehicles
            all_relevant_records = [
                r for r in telemetry_data_store if r.vehicle_id in vehicle_id
            ]
        else: # If no vehicle_id specified, consider all records in the store
            all_relevant_records = list(telemetry_data_store) # Make a copy

        # Apply time filters and ensure records are sorted by timestamp (ascending for time-series)
        # The simulator might sort records descending for pruning, so re-sort for output.
        filtered_records = []
        for rec in sorted(all_relevant_records, key=lambda x: x.timestamp): # Sort by timestamp ascending
            if (from_ts is None or rec.timestamp >= from_ts) and \
               (to_ts is None or rec.timestamp <= to_ts):
                filtered_records.append(rec)

    
    if not metric and not from_ts and not to_ts and not agg:
        # Return full telemetry objects for all filtered_records
        return filtered_records

    # Validate metric if provided
    if metric:
        valid_metrics = await list_metrics()
        if metric not in valid_metrics:
            raise HTTPException(status_code=400, detail=f"Metric '{metric}' is not valid.")
    elif agg: # Aggregation without metric is not allowed
         raise HTTPException(status_code=400, detail="Aggregation requires a 'metric' to be specified.")

    # Process metrics and aggregation
    values = []
    for rec in filtered_records:
        if metric: # If a specific metric is requested
            value = extract_metric(rec, metric)
            if value is not None:
                # Return 'timestamp', 'vehicle_id', and 'value' for the specified metric
                values.append({"vehicle_id": rec.vehicle_id, "timestamp": rec.timestamp, "value": value})
        else: # If no specific metric, return the full telemetry record
            values.append(rec) # Ensure this branch is still desired for full records if not filtering by metric

    if not values and (metric or from_ts or to_ts or agg): # Only raise if filters applied and no data
        raise HTTPException(status_code=404, detail="No data found for given filters.")

    if agg:
        # Check if values contain the "value" key and are numeric
        numeric_values = [item["value"] for item in values if "value" in item and isinstance(item["value"], (int, float))]
        
        if not numeric_values:
            raise HTTPException(status_code=400, detail="Aggregation requires numeric values. No valid metric values found.")

        result_value = {
            "avg": sum(numeric_values) / len(numeric_values) if numeric_values else 0,
            "min": min(numeric_values) if numeric_values else None,
            "max": max(numeric_values) if numeric_values else None
        }.get(agg)

        if result_value is None:
            raise HTTPException(status_code=400, detail="Invalid aggregation type. Use avg, min, or max.")

        # For aggregation, return a single dictionary with the aggregated result
        return {"metric": metric, "aggregation": agg, "value": result_value}
        
    return values # Return the list of processed records (full or metric-specific)
