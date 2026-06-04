from pydantic import BaseModel
from typing import Optional
 
 
class HealthResponse(BaseModel):
    status: str
 
 
class CommoditiesResponse(BaseModel):
    commodities: list[str]
 
 
class PriceRecord(BaseModel):
    id: int
    date: str
    commodity: str
    price: float
    ma_fast: Optional[float]
    ma_medium: Optional[float]
    ma_slow: Optional[float]
    macd: Optional[float]
    macd_signal: Optional[float]
    macd_hist: Optional[float]
    rsi: Optional[float]
    source: str
    created_at: str
 
 
class PricesResponse(BaseModel):
    data: list[PriceRecord]
 
 
class PricesByCommodityResponse(BaseModel):
    commodity: str
    data: list[PriceRecord]
 
 
class IndicatorRecord(BaseModel):
    date: str
    commodity: str
    price: Optional[float]
    ma_fast: Optional[float]
    ma_medium: Optional[float]
    ma_slow: Optional[float]
    macd: Optional[float]
    macd_signal: Optional[float]
    macd_hist: Optional[float]
    rsi: Optional[float]
 
 
class IndicatorsResponse(BaseModel):
    commodity: str
    data: list[IndicatorRecord]
 
 
class SummaryData(BaseModel):
    commodity: str
    total_rows: int
    min_price: float
    max_price: float
    avg_price: float
    start_date: str
    end_date: str
    latest_price: float
    first_price: float
    latest_rsi: Optional[float]
    latest_macd: Optional[float]
    prev_day_price: Optional[float]
    prev_week_price: Optional[float]
    period_change_pct: Optional[float]
    daily_change_pct: Optional[float]
    weekly_change_pct: Optional[float]
 
 
class SummaryResponse(BaseModel):
    commodity: str
    summary: SummaryData

class BacktestMetrics(BaseModel):
    total_return_pct: float
    annualised_return_pct: float
    annualised_vol_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    n_trades: int
    n_days: int

class BacktestSeries(BaseModel):
    date: str
    cumulative_return: float
    cumulative_strategy_return: float
    drawdown: float
    position: float

class BacktestResponse(BaseModel):
    commodity: str
    metrics: BacktestMetrics
    series: list[BacktestSeries]