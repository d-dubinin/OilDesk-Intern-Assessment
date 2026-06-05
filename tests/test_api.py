import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.config import COMMODITIES
from app.main import app, get_db


def test_health(client):
    """API and database are reachable."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_commodities_returns_expected_list(client):
    """All three commodities from the pipeline are present."""
    res = client.get("/commodities")
    assert res.status_code == 200
    assert set(res.json()["commodities"]) == set(COMMODITIES)


def test_prices_returns_data(client):
    """The /prices endpoint returns rows for all commodities."""
    res = client.get("/prices")
    assert res.status_code == 200
    assert len(res.json()["data"]) > 0


@pytest.mark.parametrize("commodity", COMMODITIES)
def test_prices_by_commodity(client, commodity):
    """/prices/{commodity} returns only rows for that commodity."""
    res = client.get(f"/prices/{commodity}")
    assert res.status_code == 200
    data = res.json()
    assert data["commodity"] == commodity
    assert all(row["commodity"] == commodity for row in data["data"])


@pytest.mark.parametrize("commodity", COMMODITIES)
def test_indicators_returns_expected_fields(client, commodity):
    """/indicators/{commodity} response contains all indicator columns."""
    res = client.get(f"/indicators/{commodity}")
    assert res.status_code == 200
    record = res.json()["data"][0]
    for field in [
        "date",
        "price",
        "ma_fast",
        "ma_medium",
        "ma_slow",
        "macd",
        "macd_signal",
        "rsi",
    ]:
        assert field in record


@pytest.mark.parametrize("commodity", COMMODITIES)
def test_summary_returns_required_fields(client, commodity):
    """/summary/{commodity} returns all key statistics."""
    res = client.get(f"/summary/{commodity}")
    assert res.status_code == 200
    summary = res.json()["summary"]
    for field in [
        "latest_price",
        "min_price",
        "max_price",
        "avg_price",
        "start_date",
        "end_date",
    ]:
        assert field in summary


@pytest.mark.parametrize("commodity", COMMODITIES)
def test_backtest_returns_metrics_and_series(client, commodity):
    """/backtest/{commodity} returns both a metrics block and a time series."""
    res = client.get(f"/backtest/{commodity}")
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert "series" in data
    for field in [
        "sharpe_ratio",
        "max_drawdown_pct",
        "total_return_pct",
        "win_rate_pct",
    ]:
        assert field in data["metrics"]


def test_invalid_commodity_returns_404(client):
    """Requesting a commodity that does not exist must return 404."""
    res = client.get("/prices/gold")
    assert res.status_code == 404


def test_404_error_message_lists_available_commodities(client):
    """
    The 404 error message should name the invalid commodity and list
    what is actually available — so the caller knows what to use.
    """
    res = client.get("/prices/gold")
    detail = res.json()["detail"]
    assert "gold" in detail
    assert "copper" in detail


def test_health_returns_500_on_database_error():
    """/health must return 500 with a database error message when the DB raises."""

    def broken_db():
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row

        def bad_execute(sql, *args, **kwargs):
            raise sqlite3.OperationalError("simulated database failure")

        conn.execute = bad_execute
        try:
            yield conn
        finally:
            conn.close()

    app.dependency_overrides[get_db] = broken_db
    try:
        with TestClient(app, raise_server_exceptions=False) as c:
            res = c.get("/health")
        assert res.status_code == 500
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize(
    "endpoint",
    [
        "/prices/gold",
        "/indicators/gold",
        "/summary/gold",
        "/backtest/gold",
    ],
)
def test_unknown_commodity_returns_404(client, endpoint):
    """Every commodity endpoint must return 404 for an unknown commodity."""
    res = client.get(endpoint)
    assert res.status_code == 404
    assert "gold" in res.json()["detail"]
