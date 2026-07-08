"""EAIDA backend (Milestone 6). Read-only API over data/analytics,
data/features, data/predictions. No writes, no raw data, no Postgres.

Run:
    uvicorn backend.main:app --reload
"""
from fastapi import FastAPI

from backend.routers import customers, forecast, inventory, overview, products, revenue, stores

app = FastAPI(title="EAIDA API", version="0.1.0")

app.include_router(overview.router, prefix="/api", tags=["overview"])
app.include_router(revenue.router, prefix="/api", tags=["revenue"])
app.include_router(forecast.router, prefix="/api", tags=["forecast"])
app.include_router(products.router, prefix="/api", tags=["products"])
app.include_router(stores.router, prefix="/api", tags=["stores"])
app.include_router(inventory.router, prefix="/api", tags=["inventory"])
app.include_router(customers.router, prefix="/api", tags=["customers"])


@app.get("/")
def root():
    return {"service": "EAIDA API", "status": "ok"}
