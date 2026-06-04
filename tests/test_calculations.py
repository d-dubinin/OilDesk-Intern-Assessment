import pandas as pd
import pytest
from app.calculations import compute_all_indicators
from app.pipeline import load_csv, filter_data
from app.config import COMMODITIES, YEARS


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
    assert pd.notna(df["ma_fast"].iloc[19])
    assert df["ma_medium"].iloc[:49].isna().all()
    assert df["ma_slow"].iloc[:199].isna().all()


def test_macd_warmup():
    """
    MACD should be null until at least 26 bars of data are available.
    """
    df = compute_all_indicators(make_test_df())
    assert df["macd"].iloc[:26].isna().all()


def test_macd_signal_starts_from_first_valid_macd():
    """
    With MACD masked before computing the signal, the signal EWM starts
    fresh from the first non-NaN MACD value. That means macd_signal at
    the first valid row must equal macd at that row exactly — there is no
    prior history for the EWM to draw on.

    Before the masking-order fix this would fail: the signal EWM was
    warmed up on unreliable pre-26-bar MACD values, so signal[26] != macd[26].
    """
    df = compute_all_indicators(make_test_df())
    first_idx = df["macd"].first_valid_index()
    assert df.loc[first_idx, "macd_signal"] == pytest.approx(df.loc[first_idx, "macd"])


def test_macd_histogram_sign():
    """
    In a rising market MACD line should eventually cross above signal,
    making the histogram positive.
    """
    df = compute_all_indicators(make_test_df())
    assert df["macd_hist"].dropna().iloc[-1] > 0


def test_indicators_independent_per_commodity():
    """
    Indicators for one commodity must not bleed into another.

    We put a rising series (copper) and a flat series (zinc) in the same
    dataframe. After compute_all_indicators, all zinc MAs must equal exactly
    100 — the flat price. If groupby isolation is broken, zinc would pick up
    copper's rising prices and the MAs would be wrong.
    """
    dates = pd.date_range("2020-01-01", periods=250, freq="B")
    df = pd.DataFrame(
        {
            "date": list(dates) * 2,
            "commodity": ["copper"] * 250 + ["zinc"] * 250,
            "price": list(range(1, 251)) + [100.0] * 250,
        }
    )
    result = compute_all_indicators(df)
    zinc = result[result["commodity"] == "zinc"]

    assert (zinc["ma_fast"].dropna() == 100.0).all()
    assert (zinc["ma_medium"].dropna() == 100.0).all()


def test_no_duplicate_date_commodity_pairs():
    """
    The pipeline must produce unique (date, commodity) combinations.

    The database has a UNIQUE(date, commodity) constraint so duplicates would
    be silently dropped on insert. This test catches the problem earlier
    at the transformation stage before it reaches the database.
    """
    df = filter_data(load_csv(), COMMODITIES, YEARS)
    dupes = df.duplicated(subset=["date", "commodity"])
    assert not dupes.any(), f"{dupes.sum()} duplicate (date, commodity) pairs found"


def test_rsi_flat_prices():
    """RSI on a flat price series has no gains or losses — result should be NaN."""
    dates = pd.date_range("2020-01-01", periods=50, freq="B")
    df = pd.DataFrame({"date": dates, "commodity": "copper", "price": 100.0})
    result = compute_all_indicators(df)
    assert result["rsi"].dropna().empty
