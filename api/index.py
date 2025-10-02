# api/index.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import json
from pathlib import Path

# Initialize FastAPI app
app = FastAPI()

# Enable CORS for all origins, all methods, all headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # Allow any origin
    allow_methods=["*"],    # Allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],    # Allow any headers
)

# Load telemetry data (packaged with deployment)
data_file = Path(__file__).resolve().parent / "q-vercel-latency.json"
with open(data_file) as f:
    records = json.load(f)

df = pd.DataFrame(records)

# POST endpoint: check latency metrics per region
@app.post("/")
async def latency_check(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    results = {}
    for region in regions:
        subset = df[df["region"] == region]
        if subset.empty:
            continue
        avg_latency = subset["latency_ms"].mean()
        p95_latency = np.percentile(subset["latency_ms"], 95)
        avg_uptime = subset["uptime_pct"].mean()
        breaches = (subset["latency_ms"] > threshold).sum()

        results[region] = {
            "avg_latency": round(avg_latency, 2),
            "p95_latency": round(p95_latency, 2),
            "avg_uptime": round(avg_uptime, 3),
            "breaches": int(breaches),
        }

    return results

# GET endpoint: health check for browser
@app.get("/health")
def health():
    return {"status": "ok"}
