from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.data_loader import ANALYTICS_DIR, FEATURES_DIR, df_to_records, load_csv

router = APIRouter()


class ProductsResponse(BaseModel):
    available: bool
    message: Optional[str] = None
    performance: list[dict[str, Any]] = []
    returns: list[dict[str, Any]] = []
    features: list[dict[str, Any]] = []


@router.get("/products", response_model=ProductsResponse)
def get_products() -> ProductsResponse:
    performance = load_csv(ANALYTICS_DIR / "product_performance.csv")
    returns = load_csv(ANALYTICS_DIR / "returns_summary.csv")
    features = load_csv(FEATURES_DIR / "product_features.csv")

    if performance is None and returns is None and features is None:
        return ProductsResponse(available=False, message="no product files found")

    return ProductsResponse(
        available=True,
        performance=df_to_records(performance),
        returns=df_to_records(returns),
        features=df_to_records(features),
    )
