from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.data_loader import ANALYTICS_DIR, FEATURES_DIR, df_to_records, load_csv

router = APIRouter()


class StoresResponse(BaseModel):
    available: bool
    message: Optional[str] = None
    performance: list[dict[str, Any]] = []
    features: list[dict[str, Any]] = []


@router.get("/stores", response_model=StoresResponse)
def get_stores() -> StoresResponse:
    performance = load_csv(ANALYTICS_DIR / "store_performance.csv")
    features = load_csv(FEATURES_DIR / "store_features.csv")

    if performance is None and features is None:
        return StoresResponse(available=False, message="no store files found")

    return StoresResponse(
        available=True,
        performance=df_to_records(performance),
        features=df_to_records(features),
    )
