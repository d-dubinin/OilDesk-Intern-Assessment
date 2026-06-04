
import pandas as pd

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.backtest import run_backtest, compute_metrics
 
from app.database import (
    get_connection,
    get_commodities,
    get_prices,
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
    BacktestResponse
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
 
 
# Health
 
@app.get("/health", response_model=HealthResponse)
def health():
    """Check the API is running and the database is reachable."""
    try:
        conn = get_connection()
        conn.execute("SELECT 1")
        conn.close()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
 
 
# Commodities
 
@app.get("/commodities", response_model=CommoditiesResponse)
def commodities():
    """Return the list of available commodities."""
    conn = get_connection()
    data = get_commodities(conn)
    conn.close()
    return {"commodities": data}
 
 
# Prices
 
@app.get("/prices", response_model=PricesResponse)
def prices():
    """Return all price and indicator data for all commodities."""
    conn = get_connection()
    data = get_prices(conn)
    conn.close()
    return {"data": data}
 
 
@app.get("/prices/{commodity}", response_model=PricesByCommodityResponse)
def prices_by_commodity(commodity: str):
    """Return price and indicator data for a specific commodity."""
    conn = get_connection()
    available = get_commodities(conn)
 
    if commodity not in available:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"Commodity '{commodity}' not found. Available: {available}",
        )
 
    data = get_prices(conn, commodity)
    conn.close()
    return {"commodity": commodity, "data": data}
 
 
# Indicators
 
@app.get("/indicators/{commodity}", response_model=IndicatorsResponse)
def indicators(commodity: str):
    """Return indicator data (MA, MACD, RSI) for a specific commodity."""
    conn = get_connection()
    available = get_commodities(conn)
 
    if commodity not in available:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"Commodity '{commodity}' not found. Available: {available}",
        )
 
    data = get_indicators(conn, commodity)
    conn.close()
    return {"commodity": commodity, "data": data}
 
 
# Summary
 
@app.get("/summary/{commodity}", response_model=SummaryResponse)
def summary(commodity: str):
    """Return price statistics summary for a specific commodity."""
    conn = get_connection()
    available = get_commodities(conn)
 
    if commodity not in available:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"Commodity '{commodity}' not found. Available: {available}",
        )
 
    data = get_summary(conn, commodity)
    conn.close()
    return {"commodity": commodity, "summary": data}

@app.get("/backtest/{commodity}", response_model=BacktestResponse)
def backtest(commodity: str):
    """Run composite signal backtest for a specific commodity."""
    conn = get_connection()
    available = get_commodities(conn)

    if commodity not in available:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail=f"Commodity '{commodity}' not found. Available: {available}",
        )

    data = get_indicators(conn, commodity)
    conn.close()

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    result   = run_backtest(df)
    metrics  = compute_metrics(result)

    # Return daily series for charting
    series = result[["date", "cumulative_return", "cumulative_strategy_return", "drawdown", "position"]].copy()
    series["date"] = series["date"].dt.strftime("%Y-%m-%d")
    series = series.dropna()

    return {
        "commodity": commodity,
        "metrics":   metrics,
        "series":    series.to_dict(orient="records"),
    }