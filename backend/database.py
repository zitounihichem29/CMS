import sqlite3
from pathlib import Path


# ============================================================
# DATABASE PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = (
    BASE_DIR.parent
    / "database"
    / "rsclub.db"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():

    conn = sqlite3.connect(
        DATABASE_PATH,
        timeout=10,
    )

    conn.row_factory = sqlite3.Row

    # SQLite does not enable foreign-key enforcement
    # automatically for every connection.
    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn