"""
Load the CSV, compute all indicators, and insert into the database.
Run this after init_db.py to populate the database.

uv run python scripts/run_pipeline.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pipeline import run_pipeline

run_pipeline()
