from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.data_loader import ANALYTICS_DIR, load_csv

router = APIRouter()


class OverviewResponse(BaseModel):
    available: bool
    message: Optional[str] = None
    total_revenue: Optional[float] = None
    total_orders: Optional[float] = None
    total_customers: Optional[int] = None
    average_order_value: Optional[float] = None


@router.get("/overview", response_model=OverviewResponse)
def get_overview() -> OverviewResponse:
    monthly_sales = load_csv(ANALYTICS_DIR / "monthly_sales.csv")
    customer_summary = load_csv(ANALYTICS_DIR / "customer_summary.csv")

    if monthly_sales is None:
        return OverviewResponse(available=False, message="monthly_sales.csv not found")

    total_revenue = float(monthly_sales["revenue"].sum())
    total_orders = float(monthly_sales["orders"].sum())
    avg_order_value = total_revenue / total_orders if total_orders else None
    total_customers = len(customer_summary) if customer_summary is not None else None

    return OverviewResponse(
        available=True,
        total_revenue=total_revenue,
        total_orders=total_orders,
        total_customers=total_customers,
        average_order_value=avg_order_value,
    )
