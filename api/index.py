from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import numpy as np
from pathlib import Path
import time

app = FastAPI()

# Allow POST requests from any origin (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS", "GET"],
    allow_headers=["*"],
)

# Load the telemetry data that was deployed with the function
DATA_FILE = Path("q-vercel-latency.json")
if DATA_FILE.exists():
    telemetry = json.loads(DATA_FILE.read_text())
else:
    telemetry = []

def stats_for_region(region: str, threshold: float):
    items = [r for r in telemetry if r.get("region") == region]
    if not items:
        return None
    latencies = [float(r["latency_ms"]) for r in items]
    uptimes = [float(r["uptime_pct"]) for r in items]

    avg_latency = float(np.mean(latencies))
    p95_latency = float(np.percentile(latencies, 95))
    avg_uptime = float(np.mean(uptimes))
    breaches = sum(1 for l in latencies if l > threshold)

    # rounding for nicer JSON
    return {
        "avg_latency": round(avg_latency, 2),
        "p95_latency": round(p95_latency, 2),
        "avg_uptime": round(avg_uptime, 3),
        "breaches": int(breaches),
    }

@app.post("/")
async def analyze(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    return {"received_regions": regions}

# ✅ New GET endpoint for /api/latency
@app.get("/api/latency")
async def latency():
    return JSONResponse({
        "message": "Latency API is working",
        "timestamp": time.time(),
        "total_records": len(telemetry)
    })

