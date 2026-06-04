import asyncio
import logging
 
import aiosqlite
import pandas as pd
 
from app.config import COMMODITIES, DB_PATH, YEARS
from app.pipeline import load_csv, filter_data
from app.calculations import compute_all_indicators
 
logger = logging.getLogger(__name__)
 
 
# Async database helpers
 
async def async_insert_indicators(df: pd.DataFrame) -> int:
    """
    Write transformed indicator data to SQLite asynchronously.
    """
    df_insert = df.copy()
    df_insert["date"] = df_insert["date"].dt.strftime("%Y-%m-%d")
    df_insert["source"] = "Bloomberg"
 
    cols = [
        "date", "commodity", "price", "ma_fast", "ma_medium",
        "ma_slow", "macd", "macd_signal", "macd_hist", "rsi", "source"
    ]
 
    records = df_insert[cols].to_dict(orient="records")
 
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.executemany(
            """
            INSERT OR IGNORE INTO indicators
                (date, commodity, price, ma_fast, ma_medium, ma_slow,
                 macd, macd_signal, macd_hist, rsi, source)
            VALUES
                (:date, :commodity, :price, :ma_fast, :ma_medium, :ma_slow,
                 :macd, :macd_signal, :macd_hist, :rsi, :source)
            """,
            records,
        )
        await conn.commit()
 
    logger.info(f"Async insert complete — {len(records)} records processed")
    return len(records)
 
 
async def async_read_commodity(commodity: str) -> list:
    """
    Read indicator data for a single commodity asynchronously
    """
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        async with conn.execute(
            """
            SELECT date, commodity, price, rsi, macd
            FROM indicators
            WHERE commodity = ?
            ORDER BY date
            """,
            (commodity,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
 
 
async def async_read_concurrent() -> dict:
    """
    Read from the database five times concurrently using asyncio.gather().
    """
    commodities = COMMODITIES + COMMODITIES[:2]
 
    results = await asyncio.gather(
        async_read_commodity(commodities[0]),
        async_read_commodity(commodities[1]),
        async_read_commodity(commodities[2]),
        async_read_commodity(commodities[3]),
        async_read_commodity(commodities[4]),
    )
 
    return {
        f"read_{i+1}_{commodities[i]}": len(results[i])
        for i in range(len(commodities))
    }
 
# Full async pipeline
 
async def run_async_pipeline() -> None:
    """
    Run the full pipeline asynchronously:
    1. Load and transform data
    2. Insert to database asynchronously
    3. Read from database five times concurrently
    """
    logger.info("Async pipeline started")
 
    # Data preparation is synchronous — pandas operations are CPU-bound
    # and do not benefit from async
    df_raw        = load_csv()
    df_filtered   = filter_data(df_raw, COMMODITIES, YEARS)
    df_indicators = compute_all_indicators(df_filtered)
 
    # Async insert
    rows = await async_insert_indicators(df_indicators)
    logger.info(f"Inserted {rows} rows asynchronously")
 
    # Concurrent reads
    read_results = await async_read_concurrent()
    logger.info(f"Concurrent reads complete: {read_results}")
 
    logger.info("Async pipeline complete")
 
 
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    asyncio.run(run_async_pipeline())