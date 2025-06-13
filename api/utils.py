def extract_metric(record, metric):
    # Handles nested metrics like tire_pressure_psi.front_left
    parts = metric.split(".")
    value = record.dict()
    for part in parts:
        value = value.get(part)
        if value is None:
            return None
    return value