import logging
import time
from datetime import datetime
from functools import wraps
from pathlib import Path

import pandas as pd

from app.calculations import compute_all_indicators
from app.database import get_connection, create_tables
from app.config import CSV_PATH, COMMODITIES, YEARS


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# Decorator


def log_insert(func):
    """Log function name, start time, end time, duration, and rows inserted."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        logger.info(
            f"Starting {func.__name__} at {datetime.now().strftime('%H:%M:%S')}"
        )
        rows = func(*args, **kwargs)
        duration = time.time() - start
        logger.info(
            f"Finished {func.__name__} | rows processed: {rows} | duration: {duration:.3f}s"
        )
        return rows

    return wrapper


# Pipeline steps


def load_csv(path: Path = CSV_PATH) -> pd.DataFrame:
    """Load and parse the raw CSV file."""
    columns = ["date", "copper", "aluminium", "zinc", "lead", "tin", "crude_oil"]

    df = pd.read_csv(path, skiprows=7, header=None, names=columns)
    df["date"] = pd.to_datetime(df["date"], dayfirst=True)

    price_cols = columns[1:]
    df[price_cols] = df[price_cols].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=price_cols, how="all")

    return df


def filter_data(df: pd.DataFrame, commodities: list, years: list) -> pd.DataFrame:
    """Filter by commodities and years, melt to long format."""
    df = df[df["date"].dt.year.isin(years)][["date"] + commodities].copy()
    df = df.melt(
        id_vars="date", value_vars=commodities, var_name="commodity", value_name="price"
    )
    df = df.dropna(subset=["price"])
    df = df.sort_values(["commodity", "date"]).reset_index(drop=True)
    return df


@log_insert
def insert_indicators(df: pd.DataFrame) -> int:
    """Insert transformed indicator data into SQLite. Returns row count."""
    conn = get_connection()
    create_tables(conn)

    df_insert = df.copy()
    df_insert["date"] = df_insert["date"].dt.strftime("%Y-%m-%d")
    df_insert["source"] = "Bloomberg"

    cols = [
        "date",
        "commodity",
        "price",
        "ma_fast",
        "ma_medium",
        "ma_slow",
        "macd",
        "macd_signal",
        "macd_hist",
        "rsi",
        "source",
    ]

    cursor = conn.cursor()
    cursor.executemany(
        """
        INSERT OR IGNORE INTO indicators
            (date, commodity, price, ma_fast, ma_medium, ma_slow,
             macd, macd_signal, macd_hist, rsi, source)
        VALUES
            (:date, :commodity, :price, :ma_fast, :ma_medium, :ma_slow,
             :macd, :macd_signal, :macd_hist, :rsi, :source)
        """,
        df_insert[cols].to_dict(orient="records"),
    )
    conn.commit()
    conn.close()
    return len(df_insert)


# Run the full pipeline


def run_pipeline(
    commodities: list = COMMODITIES,
    years: list = YEARS,
) -> None:
    logger.info("Pipeline started")

    df_raw = load_csv()
    df_filtered = filter_data(df_raw, commodities, years)
    df_indicators = compute_all_indicators(df_filtered)

    insert_indicators(df_indicators)

    logger.info("Pipeline complete")


if __name__ == "__main__":
    run_pipeline()
