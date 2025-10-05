from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import json
import numpy as np
import os

# --- FastAPI App Initialization ---
app = FastAPI()

# --- CORS Configuration ---
# Enables POST requests from any origin as required.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# --- Data Loading ---
# Load telemetry data from the JSON file at startup.
# The path is relative to this script's location to work in the Vercel environment.
try:
    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'q-vercel-latency.json')
    with open(data_path, 'r') as f:
        telemetry_data = json.load(f)
except FileNotFoundError:
    telemetry_data = []

# --- Pydantic Model for Request Body Validation ---
class TelemetryRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

# --- API Endpoint ---
@app.post("/")
def get_latency_metrics(request: TelemetryRequest):
    """
    Accepts a list of regions and a latency threshold, then returns
    aggregated metrics for each region based on the telemetry data.
    """
    response_data = {}

    if not telemetry_data:
        return {"error": "Telemetry data file not found or is empty."}

    for region in request.regions:
        # Filter data for the current region
        region_data = [record for record in telemetry_data if record.get('region') == region]

        if not region_data:
            continue

        # Extract latency and uptime values for calculations
        latencies = [record['latency_ms'] for record in region_data]
        uptimes = [record['uptime_pct'] for record in region_data]

        # Calculate the required metrics
        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        avg_uptime = np.mean(uptimes)
        breaches = sum(1 for lat in latencies if lat > request.threshold_ms)

        response_data[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    return response_data
