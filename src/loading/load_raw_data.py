"""
Day 3 — load the synthetic CSVs into PostgreSQL as the raw layer.

Usage:
    python -m src.loading.load_raw_data

Requires a running local Postgres (see README for the brew/docker options)
and a database matching your .env settings already created, e.g.:
    createdb eaida

Design choice: pandas.to_sql over psycopg2 COPY.
    to_sql is slower on very large files because it batches rows through
    the Python/SQLAlchemy layer instead of Postgres's native bulk loader.
    At our current volume (largest file ~99K rows) that difference is a
    few seconds, not minutes, so we take the simpler, more portable option.
    If this were multi-million-row files, the swap would be:
        with engine.raw_connection().cursor() as cur:
            with open(csv_path) as f:
                cur.copy_expert(f"COPY {table} FROM STDIN WITH CSV HEADER", f)
    copy_expert (not COPY FROM '<path>') is the version that works without
    Postgres server-side filesystem access, which matters once the DB isn't
    running on the same machine as your script — worth knowing even though
    we don't need it yet.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from src.config.settings import get_database_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
SCHEMA_SQL_PATH = PROJECT_ROOT / "sql" / "01_schema.sql"

# Order matters: parents before children, so foreign keys never fail.
LOAD_ORDER = [
    "customers",
    "stores",
    "products",
    "orders",
    "order_items",
    "inventory",
    "returns",
    "marketing_campaigns",
]

DATE_COLUMNS = {
    "customers": ["signup_date"],
    "stores": ["open_date"],
    "products": [],
    "orders": ["order_date"],
    "order_items": [],
    "inventory": ["snapshot_date"],
    "returns": ["return_date"],
    "marketing_campaigns": ["start_date", "end_date"],
}


def apply_schema(engine) -> None:
    logger.info("Applying schema from %s", SCHEMA_SQL_PATH)
    sql_script = SCHEMA_SQL_PATH.read_text()
    with engine.begin() as conn:
        for statement in sql_script.split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
    logger.info("Schema applied: %d tables created", len(LOAD_ORDER))


def load_table(engine, table_name: str) -> int:
    csv_path = RAW_DATA_DIR / f"{table_name}.csv"
    df = pd.read_csv(csv_path, parse_dates=DATE_COLUMNS[table_name])

    df.to_sql(
        table_name,
        engine,
        if_exists="append",  # schema/tables already created by apply_schema
        index=False,
        method="multi",      # batches multi-row INSERTs instead of one-by-one
        chunksize=5_000,
    )
    logger.info("Loaded %-22s %6d rows", table_name, len(df))
    return len(df)


def main() -> None:
    settings = get_database_settings()
    engine = create_engine(settings.sqlalchemy_url)

    apply_schema(engine)

    total_rows = 0
    for table_name in LOAD_ORDER:
        total_rows += load_table(engine, table_name)

    logger.info("Done. Loaded %d total rows across %d tables.", total_rows, len(LOAD_ORDER))


if __name__ == "__main__":
    main()
