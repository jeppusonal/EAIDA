from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.data_loader import PREDICTIONS_DIR, df_to_records, load_csv

router = APIRouter()


class ForecastResponse(BaseModel):
    available: bool
    message: Optional[str] = None
    data: list[dict[str, Any]] = []


@router.get("/forecast", response_model=ForecastResponse)
def get_forecast() -> ForecastResponse:
    df = load_csv(PREDICTIONS_DIR / "sales_forecast_baseline.csv")
    if df is None:
        return ForecastResponse(available=False, message="sales_forecast_baseline.csv not found")
    return ForecastResponse(available=True, data=df_to_records(df))
