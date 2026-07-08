from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.data_loader import ANALYTICS_DIR, df_to_records, load_csv

router = APIRouter()


class RevenueResponse(BaseModel):
    available: bool
    message: Optional[str] = None
    monthly: list[dict[str, Any]] = []
    daily: list[dict[str, Any]] = []


@router.get("/revenue", response_model=RevenueResponse)
def get_revenue() -> RevenueResponse:
    monthly = load_csv(ANALYTICS_DIR / "monthly_sales.csv")
    daily = load_csv(ANALYTICS_DIR / "daily_sales.csv")

    if monthly is None and daily is None:
        return RevenueResponse(available=False, message="monthly_sales.csv and daily_sales.csv not found")

    return RevenueResponse(
        available=True,
        monthly=df_to_records(monthly),
        daily=df_to_records(daily),
    )
