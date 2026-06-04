import sqlite3

from app.config import DB_PATH


def get_connection() -> sqlite3.Connection:
    """Return a connection to the SQLite database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    """Create all tables if they do not already exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            date       TEXT    NOT NULL,
            commodity  TEXT    NOT NULL,
            price      REAL    NOT NULL,
            source     TEXT    NOT NULL DEFAULT 'Bloomberg',
            created_at TEXT    NOT NULL DEFAULT (datetime('now')),
            UNIQUE(date, commodity)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            commodity TEXT NOT NULL,
            price REAL,
            ma_fast REAL,
            ma_medium REAL,
            ma_slow REAL,
            macd REAL,
            macd_signal REAL,
            macd_hist REAL,
            rsi REAL,
            source TEXT NOT NULL DEFAULT 'Bloomberg',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(date, commodity)
        )
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_indicators_commodity_date
        ON indicators(commodity, date)
    """)

    conn.commit()


def get_commodities(conn: sqlite3.Connection) -> list:
    """Return a list of distinct commodities in the indicators table."""
    rows = conn.execute(
        "SELECT DISTINCT commodity FROM indicators ORDER BY commodity"
    ).fetchall()
    return [row["commodity"] for row in rows]


def get_indicator_rows(conn: sqlite3.Connection, commodity: str = None) -> list:
    """Return indicator rows from the indicators table, optionally filtered by commodity."""
    if commodity:
        rows = conn.execute(
            "SELECT * FROM indicators WHERE commodity = ? ORDER BY date", (commodity,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM indicators ORDER BY commodity, date"
        ).fetchall()
    return [dict(row) for row in rows]


def get_indicators(conn: sqlite3.Connection, commodity: str) -> list:
    """Return indicator data for a specific commodity."""
    rows = conn.execute(
        """
        SELECT date, commodity, price, ma_fast, ma_medium, ma_slow,
               macd, macd_signal, macd_hist, rsi
        FROM indicators
        WHERE commodity = ?
        ORDER BY date
        """,
        (commodity,),
    ).fetchall()
    return [dict(row) for row in rows]


def get_summary(conn: sqlite3.Connection, commodity: str) -> dict:
    """Return price statistics summary for a specific commodity."""
    row = conn.execute(
        """
        SELECT
            commodity,
            COUNT(*) AS total_rows,
            ROUND(MIN(price), 2) AS min_price,
            ROUND(MAX(price), 2) AS max_price,
            ROUND(AVG(price), 2) AS avg_price,
            MIN(date) AS start_date,
            MAX(date) AS end_date,
            ROUND((SELECT price FROM indicators
                   WHERE commodity = i.commodity
                   ORDER BY date DESC LIMIT 1), 2) AS latest_price,
            ROUND((SELECT price FROM indicators
                   WHERE commodity = i.commodity
                   ORDER BY date ASC LIMIT 1), 2) AS first_price,
            ROUND((SELECT rsi FROM indicators
                   WHERE commodity = i.commodity
                   AND rsi IS NOT NULL
                   ORDER BY date DESC LIMIT 1), 2) AS latest_rsi,
            ROUND((SELECT macd FROM indicators
                   WHERE commodity = i.commodity
                   AND macd IS NOT NULL
                   ORDER BY date DESC LIMIT 1), 2) AS latest_macd,
            ROUND((SELECT price FROM indicators
                   WHERE commodity = i.commodity
                   ORDER BY date DESC LIMIT 1 OFFSET 1), 2) AS prev_day_price,
            ROUND((SELECT price FROM indicators
                   WHERE commodity = i.commodity
                   ORDER BY date DESC LIMIT 1 OFFSET 4), 2) AS prev_week_price
        FROM indicators i
        WHERE commodity = ?
        GROUP BY commodity
        """,
        (commodity,),
    ).fetchone()

    if not row:
        return {}

    result = dict(row)

    # Period return
    if result["first_price"] and result["latest_price"]:
        result["period_change_pct"] = round(
            ((result["latest_price"] - result["first_price"]) / result["first_price"])
            * 100,
            2,
        )

    # Daily change
    if result["prev_day_price"] and result["latest_price"]:
        result["daily_change_pct"] = round(
            (
                (result["latest_price"] - result["prev_day_price"])
                / result["prev_day_price"]
            )
            * 100,
            2,
        )

    # Weekly change
    if result["prev_week_price"] and result["latest_price"]:
        result["weekly_change_pct"] = round(
            (
                (result["latest_price"] - result["prev_week_price"])
                / result["prev_week_price"]
            )
            * 100,
            2,
        )

    return result
