import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

from app.calculations import compute_all_indicators
from app.config import COMMODITIES, YEARS
from app.database import create_tables
from app.pipeline import filter_data, insert_indicators, load_csv, run_pipeline


def test_insert_indicators_without_connection():
    """insert_indicators must open and close its own connection when conn=None."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    try:
        setup_conn = sqlite3.connect(db_path)
        create_tables(setup_conn)
        setup_conn.close()

        df = compute_all_indicators(filter_data(load_csv(), COMMODITIES, YEARS))

        with patch("app.pipeline.get_connection") as mock_get_conn:
            real_conn = sqlite3.connect(db_path, check_same_thread=False)
            real_conn.row_factory = sqlite3.Row
            mock_get_conn.return_value = real_conn

            rows = insert_indicators(df)

        assert rows > 0
    finally:
        db_path.unlink(missing_ok=True)


def test_run_pipeline_end_to_end():
    """run_pipeline must complete without error and populate the indicators table."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    try:
        with patch("app.pipeline.get_connection") as mock_conn:
            real_conn = sqlite3.connect(db_path, check_same_thread=False)
            real_conn.row_factory = sqlite3.Row
            mock_conn.return_value = real_conn

            run_pipeline()

        verify_conn = sqlite3.connect(db_path)
        count = verify_conn.execute("SELECT COUNT(*) FROM indicators").fetchone()[0]
        verify_conn.close()

        assert count > 0
    finally:
        db_path.unlink(missing_ok=True)
