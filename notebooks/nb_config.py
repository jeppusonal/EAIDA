"""Shared constants for the data-generation notebooks.

Deliberately tiny: paths and the random seed only. All generation logic
stays inside each notebook so the notebooks remain the readable, educational
artifact for this MVP stage.
"""
from pathlib import Path

SEED = 42
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

N_CUSTOMERS = 5_000
N_PRODUCTS = 200
N_STORES = 8

CITIES = [
    ("Sydney", "NSW"),
    ("Sydney", "NSW"),
    ("Melbourne", "VIC"),
    ("Melbourne", "VIC"),
    ("Brisbane", "QLD"),
    ("Perth", "WA"),
    ("Adelaide", "SA"),
    ("Canberra", "ACT"),
]

ORDER_HISTORY_MONTHS = 18
ANOMALY_MONTHS = 2          # final N months get the Sydney drop
ANOMALY_CITY = "Sydney"

# The Sydney drop is now driven by two INDEPENDENT, separately-tunable causes
# instead of one blanket order-volume multiplier. This is what makes it
# possible for the Day 4 SQL to distinguish acquisition decline from
# retention decline instead of just observing "fewer orders" with no cause.
ANOMALY_SIGNUP_REDUCTION = 0.45     # fewer NEW Sydney signups during the anomaly window (acquisition)
ANOMALY_RETENTION_PENALTY = 0.50    # existing Sydney customers (signed up 90+ days before the order)
                                     # are this much less likely to be drawn for an order during the
                                     # anomaly window (retention)
ANOMALY_EXISTING_CUTOFF_DAYS = 90   # "existing" = signed up at least this long before the order date
ANOMALY_BASE_SOFTNESS = 0.15        # small general demand softening, applied to ALL Sydney orders in
                                     # the anomaly window regardless of cohort (keeps some realistic noise)
