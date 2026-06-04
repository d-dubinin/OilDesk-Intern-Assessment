import sqlite3
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.calculations import compute_all_indicators
from app.config import COMMODITIES, YEARS
from app.database import create_tables
from app.main import app, get_db
from app.pipeline import filter_data, insert_indicators, load_csv


@pytest.fixture(scope="module")
def client():
    """
    Build a temporary SQLite database populated with real pipeline data,
    override the FastAPI get_db dependency to point at it, then yield a
    TestClient. Everything is torn down after the test module finishes.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    try:
        conn = sqlite3.connect(db_path)
        create_tables(conn)
        df = compute_all_indicators(filter_data(load_csv(), COMMODITIES, YEARS))
        insert_indicators(df, conn=conn)
        conn.close()

        def override_get_db():
            c = sqlite3.connect(db_path, check_same_thread=False)
            c.row_factory = sqlite3.Row
            try:
                yield c
            finally:
                c.close()

        app.dependency_overrides[get_db] = override_get_db

        with TestClient(app) as test_client:
            yield test_client

    finally:
        app.dependency_overrides.clear()
        db_path.unlink(missing_ok=True)
