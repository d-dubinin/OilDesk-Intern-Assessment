"""
Create the database tables.
Run this once before the pipeline if the database does not exist yet.

uv run python scripts/init_db.py
"""

from app.database import get_connection, create_tables

conn = get_connection()
create_tables(conn)
conn.close()

print("Database initialised.")
