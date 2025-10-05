from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
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
    allow_methods=["GET", "POST"], # Allow GET requests
    allow_headers=["*"],
)

# --- Data Loading ---
# Load telemetry data from the JSON file at startup.
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

# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def handle_get_request():
    """
    Provides a helpful message when the endpoint is accessed via a browser (GET request).
    """
    return """
    <html>
        <head>
            <title>eShopCo Latency API</title>
            <style>
                body { font-family: sans-serif; padding: 2em; line-height: 1.6; }
                h1, h2 { color: #333; }
                code { background-color: #eee; padding: 3px 6px; border-radius: 4px; }
                pre { background-color: #f4f4f4; padding: 1em; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; }
            </style>
        </head>
        <body>
            <h1>eShopCo Latency API is Running</h1>
            <p>This endpoint is designed to accept <strong>POST</strong> requests with a JSON body.</p>
            <p>Accessing this URL in a browser sends a GET request, which is why you are seeing this page instead of an error.</p>
            <h2>How to Use This API</h2>
            <p>To fetch latency metrics, send a POST request to this URL with the following structure:</p>
            <pre><code>
{
  "regions": ["amer", "apac"],
  "threshold_ms": 152
}
            </code></pre>
            <h3>Example using cURL:</h3>
            <pre><code>curl -X POST "https://eshopco-latency-mocha.vercel.app/" \\
-H "Content-Type: application/json" \\
-d '{"regions":["amer","apac"],"threshold_ms":152}'</code></pre>
        </body>
    </html>
    """

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
        region_data = [record for record in telemetry_data if record.get('region') == region]

        if not region_data:
            continue

        latencies = [record['latency_ms'] for record in region_data]
        uptimes = [record['uptime_pct'] for record in region_data]

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
