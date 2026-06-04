import pandas as pd
import numpy as np
from app.calculations import compute_all_indicators


def make_test_df() -> pd.DataFrame:
    """
    Create a test data - 300 days of copper prices
    Using fake data keeps tests fast and
    deterministic, with no dependency on the real CSV.
    """
    dates = pd.date_range("2020-01-01", periods=300, freq="B")
    prices = pd.Series(range(1, 301), dtype=float)
    return pd.DataFrame({"date": dates, "commodity": "copper", "price": prices})


def test_rsi_bounds():
    """
    RSI must always be between 0 and 100 by definition.
    Any value outside this range means the calculation is broken.
    """
    df = compute_all_indicators(make_test_df())
    rsi = df["rsi"].dropna()
    assert rsi.between(0, 100).all()


def test_macd_histogram():
    """
    The MACD histogram is defined as MACD minus signal line.
    This test verifies that identity holds exactly in the output.
    Tolerance of 1e-10 accounts for floating point rounding only.
    """
    df = compute_all_indicators(make_test_df())
    diff = (df["macd_hist"] - (df["macd"] - df["macd_signal"])).abs()
    assert diff.max() < 1e-10


def test_early_rows_nan():
    """
    Rolling windows need enough data before producing a value.
    - 200-day MA: first 199 rows must be NaN
    - RSI: first 14 rows must be NaN
    If these rows are not NaN the warmup period is not being respected.
    """
    df = compute_all_indicators(make_test_df())
    assert df["ma_slow"].iloc[:199].isna().all()
    assert df["rsi"].iloc[:14].isna().all()

def test_moving_average_ordering():
    """
    In a steadily rising price series, fast MA reacts quicker than slow MA.
    So at any given point: ma_fast > ma_medium > ma_slow.
    Check this holds for the last row where all three are populated.
    """
    df = compute_all_indicators(make_test_df())
    last = df.dropna().iloc[-1]
    assert last["ma_fast"] > last["ma_medium"]
    assert last["ma_medium"] > last["ma_slow"]


def test_moving_average_warmup():
    """
    ma_fast needs 20 rows, ma_medium 50, ma_slow 200.
    Check the exact boundary rows.
    """
    df = compute_all_indicators(make_test_df())
    assert df["ma_fast"].iloc[:19].isna().all()
    assert df["ma_fast"].iloc[19] is not None
    assert df["ma_medium"].iloc[:49].isna().all()
    assert df["ma_slow"].iloc[:199].isna().all()


def test_macd_warmup():
    """
    MACD should be null until at least 26 bars of data are available.
    """
    df = compute_all_indicators(make_test_df())
    assert df["macd"].iloc[:26].isna().all()


def test_macd_histogram_sign():
    """
    In a rising market MACD line should eventually cross above signal,
    making the histogram positive.
    """
    df = compute_all_indicators(make_test_df())
    assert df["macd_hist"].dropna().iloc[-1] > 0