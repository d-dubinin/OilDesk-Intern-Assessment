
import sqlite3
from typing import Iterator

import pandas as pd

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.backtest import run_backtest, compute_metrics

from app.database import (
    get_connection,
    get_commodities,
    get_indicator_rows,
    get_indicators,
    get_summary,
)
from app.models import (
    HealthResponse,
    CommoditiesResponse,
    PricesResponse,
    PricesByCommodityResponse,
    IndicatorsResponse,
    SummaryResponse,
    BacktestResponse,
)

app = FastAPI(
    title="Oil Desk Analytics API",
    description="Commodity price and indicator data for the Oil Desk dashboard.",
    version="1.0.0",
)

# Allow the frontend to call the API from the browser
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db() -> Iterator[sqlite3.Connection]:
    """FastAPI dependency that opens a DB connection and closes it after the request."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


# Health

@app.get("/health", response_model=HealthResponse)
def health(conn: sqlite3.Connection = Depends(get_db)):
    """Check the API is running and the database is reachable."""
    try:
        conn.execute("SELECT 1")
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")


# Commodities

@app.get("/commodities", response_model=CommoditiesResponse)
def commodities(conn: sqlite3.Connection = Depends(get_db)):
    """Return the list of available commodities."""
    return {"commodities": get_commodities(conn)}


# Prices

@app.get("/prices", response_model=PricesResponse)
def prices(conn: sqlite3.Connection = Depends(get_db)):
    """Return all price and indicator data for all commodities."""
    return {"data": get_indicator_rows(conn)}


@app.get("/prices/{commodity}", response_model=PricesByCommodityResponse)
def prices_by_commodity(commodity: str, conn: sqlite3.Connection = Depends(get_db)):
    """Return price and indicator data for a specific commodity."""
    available = get_commodities(conn)
    if commodity not in available:
        raise HTTPException(
            status_code=404,
            detail=f"Commodity '{commodity}' not found. Available: {available}",
        )
    return {"commodity": commodity, "data": get_indicator_rows(conn, commodity)}


# Indicators

@app.get("/indicators/{commodity}", response_model=IndicatorsResponse)
def indicators(commodity: str, conn: sqlite3.Connection = Depends(get_db)):
    """Return indicator data (MA, MACD, RSI) for a specific commodity."""
    available = get_commodities(conn)
    if commodity not in available:
        raise HTTPException(
            status_code=404,
            detail=f"Commodity '{commodity}' not found. Available: {available}",
        )
    return {"commodity": commodity, "data": get_indicators(conn, commodity)}


# Summary

@app.get("/summary/{commodity}", response_model=SummaryResponse)
def summary(commodity: str, conn: sqlite3.Connection = Depends(get_db)):
    """Return price statistics summary for a specific commodity."""
    available = get_commodities(conn)
    if commodity not in available:
        raise HTTPException(
            status_code=404,
            detail=f"Commodity '{commodity}' not found. Available: {available}",
        )
    return {"commodity": commodity, "summary": get_summary(conn, commodity)}


@app.get("/backtest/{commodity}", response_model=BacktestResponse)
def backtest(commodity: str, conn: sqlite3.Connection = Depends(get_db)):
    """Run composite signal backtest for a specific commodity."""
    available = get_commodities(conn)
    if commodity not in available:
        raise HTTPException(
            status_code=404,
            detail=f"Commodity '{commodity}' not found. Available: {available}",
        )

    data = get_indicators(conn, commodity)

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    result = run_backtest(df)
    metrics = compute_metrics(result)

    series = result[["date", "cumulative_return", "cumulative_strategy_return", "drawdown", "position"]].copy()
    series["date"] = series["date"].dt.strftime("%Y-%m-%d")
    series = series.dropna()

    return {
        "commodity": commodity,
        "metrics": metrics,
        "series": series.to_dict(orient="records"),
    }