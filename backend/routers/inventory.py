from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.data_loader import ANALYTICS_DIR, df_to_records, load_csv

router = APIRouter()


class InventoryResponse(BaseModel):
    available: bool
    message: Optional[str] = None
    data: list[dict[str, Any]] = []


@router.get("/inventory", response_model=InventoryResponse)
def get_inventory() -> InventoryResponse:
    df = load_csv(ANALYTICS_DIR / "inventory_health.csv")
    if df is None:
        return InventoryResponse(available=False, message="inventory_health.csv not found")
    return InventoryResponse(available=True, data=df_to_records(df))
