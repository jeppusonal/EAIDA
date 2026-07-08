"""Shared CSV loader for the backend. Reads only from data/analytics,
data/features, data/predictions. No writes, no DB, no raw data.
"""
from pathlib import Path
from typing import Any

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ANALYTICS_DIR = BASE_DIR / "data" / "analytics"
FEATURES_DIR = BASE_DIR / "data" / "features"
PREDICTIONS_DIR = BASE_DIR / "data" / "predictions"


def load_csv(path: Path) -> pd.DataFrame | None:
    """Return DataFrame, or None if file missing/unreadable. Never raises."""
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except Exception:
        return None


def df_to_records(df: pd.DataFrame | None) -> list[dict[str, Any]]:
    """NaN-safe dict conversion. Empty list if df is None."""
    if df is None:
        return []
    return df.where(pd.notnull(df), None).to_dict(orient="records")
