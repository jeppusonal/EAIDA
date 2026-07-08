from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.data_loader import ANALYTICS_DIR, FEATURES_DIR, df_to_records, load_csv

router = APIRouter()


class CustomersResponse(BaseModel):
    available: bool
    message: Optional[str] = None
    total_customers: Optional[int] = None
    summary_sample: list[dict[str, Any]] = []
    features_sample: list[dict[str, Any]] = []


@router.get("/customers", response_model=CustomersResponse)
def get_customers(sample_size: int = 20) -> CustomersResponse:
    summary = load_csv(ANALYTICS_DIR / "customer_summary.csv")
    features = load_csv(FEATURES_DIR / "customer_features.csv")

    if summary is None and features is None:
        return CustomersResponse(available=False, message="no customer files found")

    return CustomersResponse(
        available=True,
        total_customers=len(summary) if summary is not None else None,
        summary_sample=df_to_records(summary.head(sample_size) if summary is not None else None),
        features_sample=df_to_records(features.head(sample_size) if features is not None else None),
    )
