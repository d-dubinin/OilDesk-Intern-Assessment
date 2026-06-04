import pandas as pd
import numpy as np

from app.config import (
    MA_FAST,
    MA_MEDIUM,
    MA_SLOW,
    MACD_FAST,
    MACD_SLOW,
    MACD_SIGNAL,
    RSI_PERIOD,
)


def compute_moving_averages(
    df: pd.DataFrame,
    fast: int = MA_FAST,
    medium: int = MA_MEDIUM,
    slow: int = MA_SLOW,
) -> pd.DataFrame:
    """
    Simple moving averages applied per commodity group.

    Defaults are standard commodity market lookbacks:
    - 20-day = one trading month
    - 50-day = one trading quarter
    - 200-day = one trading year
    """
    grp = df.groupby("commodity")["price"]

    df["ma_fast"] = grp.transform(lambda x: x.rolling(fast).mean())
    df["ma_medium"] = grp.transform(lambda x: x.rolling(medium).mean())
    df["ma_slow"] = grp.transform(lambda x: x.rolling(slow).mean())

    return df


def compute_macd(
    df: pd.DataFrame,
    fast: int = MACD_FAST,
    slow: int = MACD_SLOW,
    signal: int = MACD_SIGNAL,
) -> pd.DataFrame:
    """
    MACD line, signal line, and histogram applied per commodity group.

    - MACD line = fast EMA minus slow EMA
    - Signal line = EMA of the MACD line
    - Histogram = MACD minus signal

    12/26/9 are the universal defaults across all trading platforms.
    Rows are masked until at least `slow` bars of data are available.
    """
    grp = df.groupby("commodity")["price"]

    ema_fast = grp.transform(lambda x: x.ewm(span=fast, adjust=False).mean())
    ema_slow = grp.transform(lambda x: x.ewm(span=slow, adjust=False).mean())

    df["macd"] = ema_fast - ema_slow
    df["macd_signal"] = df.groupby("commodity")["macd"].transform(
        lambda x: x.ewm(span=signal, adjust=False).mean()
    )
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    # Mask until enough bars are available for the slow EMA
    df.loc[
        df.groupby("commodity").cumcount() < slow, ["macd", "macd_signal", "macd_hist"]
    ] = np.nan

    return df


def _wilder_rsi(series: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    """
    RSI using Wilder's smoothing (RMA) — alpha = 1/period.

    Matches standard trading platforms. Period 14 is the daily standard.
    Early rows are masked until the warmup period is complete.
    """
    delta = series.diff()
    gain = delta.clip(lower=0)  # positive moves only, negatives zeroed
    loss = -delta.clip(upper=0)  # negative moves flipped to positive

    alpha = 1.0 / period
    avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
    avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()

    avg_gain.iloc[:period] = np.nan
    avg_loss.iloc[:period] = np.nan

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def compute_rsi(
    df: pd.DataFrame,
    period: int = RSI_PERIOD,
) -> pd.DataFrame:
    """
    Wilder RSI applied per commodity group.

    reset_index(drop=True) ensures ewm calculates correctly
    without index gaps when groupby splits the series.
    """

    def rsi_per_group(x):
        result = _wilder_rsi(x.reset_index(drop=True), period)
        result.index = x.index  # map result back to original index
        return result

    df["rsi"] = df.groupby("commodity")["price"].transform(rsi_per_group)
    return df


def compute_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply all indicators to the dataframe.
    Expects columns: date, commodity, price.
    Returns dataframe with ma_fast, ma_medium, ma_slow,
    macd, macd_signal, macd_hist, and rsi columns added.
    """
    df = df.copy()
    df = compute_moving_averages(df)
    df = compute_macd(df)
    df = compute_rsi(df)
    return df
