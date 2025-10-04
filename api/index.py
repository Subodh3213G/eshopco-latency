from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json, time
import numpy as np
from pathlib import Path

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST","OPTIONS","GET"],
    allow_headers=["*"],
)

# Load telemetry data
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

    return {
        "avg_latency": round(avg_latency, 2),
        "p95_latency": round(p95_latency, 2),
        "avg_uptime": round(avg_uptime, 3),
        "breaches": int(breaches)
    }

# ✅ Health check route
@app.get("/api/latency")
async def status():
    return {
        "message": "Latency API is working",
        "timestamp": time.time(),
        "total_records": len(telemetry)
    }

# ✅ Analysis route
@app.post("/api/latency")
async def analyze(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = float(body.get("threshold", 500))

    results = {}
    for region in regions:
        stats = stats_for_region(region, threshold)
        if stats:
            results[region] = stats

    return results
