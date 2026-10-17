
from fastapi import FastAPI

app = FastAPI(title="Price Monitor")


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "application": "price-monitor",
    }
