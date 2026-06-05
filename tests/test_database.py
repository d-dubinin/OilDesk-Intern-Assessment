import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch


from app.database import create_tables, get_connection, get_summary


def test_get_connection_creates_parent_directory():
    """get_connection must create the parent directory if it does not exist"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "nested" / "dir" / "test.db"
        assert not db_path.parent.exists()

        with patch("app.database.DB_PATH", db_path):
            conn = get_connection()
            conn.close()

        assert db_path.parent.exists()
        assert db_path.exists()


def test_get_summary_returns_empty_dict_for_unknown_commodity():
    """get_summary must return an empty dict when the commodity is not in the table"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    create_tables(conn)

    result = get_summary(conn, "nonexistent")
    conn.close()
    db_path.unlink(missing_ok=True)

    assert result == {}
