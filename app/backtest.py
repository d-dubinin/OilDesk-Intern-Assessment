import pandas as pd
import numpy as np

from app.config import (
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    SIGNAL_THRESHOLD,
)


# Signal generation

def signal_price_vs_sma(df: pd.DataFrame) -> pd.Series:
    """
    Signal 1 — Price vs long-term SMA (MA200 by default).
    +1 if price > MA200 (bullish trend)
     0 if price == MA200
    -1 if price < MA200 (bearish trend)
    """
    return np.sign(df["price"] - df["ma_slow"]).fillna(0)


def signal_rsi(df: pd.DataFrame) -> pd.Series:
    """
    Signal 2 — RSI momentum.
    +1 if RSI < oversold threshold (30) — potential bounce
    -1 if RSI > overbought threshold (70) — potential reversal
     0 otherwise — neutral
    """
    signal = pd.Series(0, index=df.index)
    signal[df["rsi"] < RSI_OVERSOLD]   =  1
    signal[df["rsi"] > RSI_OVERBOUGHT] = -1
    return signal.fillna(0)


def signal_sma_cross(df: pd.DataFrame) -> pd.Series:
    """
    Signal 3 — Fast SMA vs medium SMA cross.
    +1 if MA20 > MA50 (short-term momentum bullish)
    -1 if MA20 < MA50 (short-term momentum bearish)
     0 if equal
    """
    return np.sign(df["ma_fast"] - df["ma_medium"]).fillna(0)


def signal_macd(df: pd.DataFrame) -> pd.Series:
    """
    Signal 4 — MACD vs signal line.
    +1 if MACD > signal line (bullish momentum)
    -1 if MACD < signal line (bearish momentum)
     0 if equal
    """
    return np.sign(df["macd"] - df["macd_signal"]).fillna(0)


def compute_composite_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Combine three signals by averaging.
    Average > +SIGNAL_THRESHOLD  -> long (+1)
    Otherwise -> flat (0)
    """
    df = df.copy()

    df["sig1"] = signal_price_vs_sma(df)
    df["sig2"] = signal_rsi(df)
    df["sig3"] = signal_sma_cross(df)

    df["signal_avg"] = df[["sig1", "sig2", "sig3"]].mean(axis=1)

    df["position"] = 0
    df.loc[df["signal_avg"] > SIGNAL_THRESHOLD, "position"] =  1
    df.loc[df["signal_avg"] < -SIGNAL_THRESHOLD, "position"] = 0

    return df


# Backtest engine

def run_backtest(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the composite signal backtest on a single commodity.

    Assumptions:
    - Daily settlement prices — no intraday execution
    - Position is taken at the close of the signal day
    - No transaction costs or slippage
    - Position is +1 (long), or 0 (flat)
    - Returns are log returns for mathematical consistency
    """
    df = compute_composite_signal(df)
    df = df.dropna(subset=["price"]).copy()

    # Daily log returns
    df["log_return"] = np.log(df["price"] / df["price"].shift(1))

    # Strategy return = position from previous day * today's return
    # (position is set at close, return is next day's move)
    df["strategy_return"] = df["position"].shift(1) * df["log_return"]

    # Cumulative PnL
    df["cumulative_return"] = df["log_return"].cumsum().apply(np.exp) - 1
    df["cumulative_strategy_return"] = df["strategy_return"].cumsum().apply(np.exp) - 1

    # Drawdown
    df["equity"] = (1 + df["cumulative_strategy_return"])
    df["peak"] = df["equity"].cummax()
    df["drawdown"] = (df["equity"] - df["peak"]) / df["peak"]

    return df


# Performance metrics

def compute_metrics(df: pd.DataFrame) -> dict:
    """
    Compute summary performance metrics for the backtest.

    - Total return: cumulative strategy return over the period
    - Annualised return: total return scaled to one year
    - Sharpe ratio: annualised return / annualised volatility (risk-free rate = 0)
    - Max drawdown: largest peak-to-trough decline
    - Win rate: percentage of days with positive strategy return
    - Number of trades: number of position changes
    """
    returns = df["strategy_return"].dropna()

    total_return = df["cumulative_strategy_return"].iloc[-1]
    n_days = len(returns)
    annualised_return = (1 + total_return) ** (252 / n_days) - 1
    annualised_vol = returns.std() * np.sqrt(252)
    sharpe = annualised_return / annualised_vol if annualised_vol != 0 else 0
    max_drawdown = df["drawdown"].min()
    win_rate = (returns > 0).sum() / (returns != 0).sum() if (returns != 0).sum() > 0 else 0
    n_trades = df["position"].diff().abs().gt(0).sum()

    return {
        "total_return_pct": round(total_return * 100, 2),
        "annualised_return_pct": round(annualised_return * 100, 2),
        "annualised_vol_pct": round(annualised_vol * 100, 2),
        "sharpe_ratio": round(sharpe, 3),
        "max_drawdown_pct": round(max_drawdown * 100, 2),
        "win_rate_pct": round(win_rate * 100, 2),
        "n_trades": int(n_trades),
        "n_days": int(n_days),
    }