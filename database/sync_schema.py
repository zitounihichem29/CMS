import shutil
import sqlite3
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

DATABASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = DATABASE_DIR / "rsclub.db"
SCHEMA_PATH = DATABASE_DIR / "schema.sql"

BACKUP_PATH = (
    DATABASE_DIR
    / "schema_backup_before_sync.sql"
)


# ============================================================
# READ REAL DATABASE SCHEMA
# ============================================================

source_conn = sqlite3.connect(
    DATABASE_PATH
)

source_conn.row_factory = sqlite3.Row


objects = source_conn.execute("""
    SELECT
        type,
        name,
        tbl_name,
        sql

    FROM sqlite_master

    WHERE sql IS NOT NULL
      AND name NOT LIKE 'sqlite_%'

    ORDER BY
        CASE type
            WHEN 'table' THEN 1
            WHEN 'index' THEN 2
            WHEN 'view' THEN 3
            WHEN 'trigger' THEN 4
            ELSE 5
        END,
        rowid
""").fetchall()


# ============================================================
# BUILD NEW SCHEMA.SQL
# ============================================================

schema_parts = [
    "-- ============================================================\n"
    "-- ORSC CMS - CANONICAL DATABASE SCHEMA\n"
    "-- Automatically synchronized from rsclub.db\n"
    "-- ============================================================\n\n"
    "PRAGMA foreign_keys = ON;\n\n"
    "BEGIN TRANSACTION;\n\n"
]


for obj in objects:

    schema_parts.append(
        f"-- ============================================================\n"
        f"-- {obj['type'].upper()}: {obj['name']}\n"
        f"-- ============================================================\n\n"
    )

    sql = obj["sql"].strip()

    schema_parts.append(
        sql
        + ";\n\n"
    )


schema_parts.append(
    "COMMIT;\n"
)


new_schema = "".join(
    schema_parts
)


# ============================================================
# TEST GENERATED SCHEMA BEFORE SAVING IT
# ============================================================

test_conn = sqlite3.connect(
    ":memory:"
)

try:

    test_conn.executescript(
        new_schema
    )

except Exception as error:

    test_conn.close()
    source_conn.close()

    raise RuntimeError(
        "Generated schema is invalid: "
        f"{error}"
    )


# ============================================================
# COMPARE TABLES
# ============================================================

source_tables = {
    row["name"]
    for row in source_conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
    """).fetchall()
}


test_tables = {
    row[0]
    for row in test_conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
    """).fetchall()
}


if source_tables != test_tables:

    missing = (
        source_tables
        - test_tables
    )

    extra = (
        test_tables
        - source_tables
    )

    test_conn.close()
    source_conn.close()

    raise RuntimeError(
        "Table comparison failed. "
        f"Missing: {sorted(missing)} | "
        f"Extra: {sorted(extra)}"
    )


# ============================================================
# COMPARE EXPLICIT INDEXES
# ============================================================

source_indexes = {
    row["name"]
    for row in source_conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'index'
          AND sql IS NOT NULL
          AND name NOT LIKE 'sqlite_%'
    """).fetchall()
}


test_indexes = {
    row[0]
    for row in test_conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'index'
          AND sql IS NOT NULL
          AND name NOT LIKE 'sqlite_%'
    """).fetchall()
}


if source_indexes != test_indexes:

    missing = (
        source_indexes
        - test_indexes
    )

    extra = (
        test_indexes
        - source_indexes
    )

    test_conn.close()
    source_conn.close()

    raise RuntimeError(
        "Index comparison failed. "
        f"Missing: {sorted(missing)} | "
        f"Extra: {sorted(extra)}"
    )


# ============================================================
# FOREIGN KEY TEST
# ============================================================

foreign_key_errors = (
    test_conn.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()
)


if foreign_key_errors:

    test_conn.close()
    source_conn.close()

    raise RuntimeError(
        "Foreign-key check failed: "
        f"{foreign_key_errors}"
    )


# ============================================================
# BACKUP OLD SCHEMA.SQL
# ============================================================

if SCHEMA_PATH.exists():

    shutil.copy2(
        SCHEMA_PATH,
        BACKUP_PATH,
    )


# ============================================================
# WRITE NEW CANONICAL SCHEMA
# ============================================================

SCHEMA_PATH.write_text(
    new_schema,
    encoding="utf-8",
)


# ============================================================
# RESULTS
# ============================================================

print(
    "Schema synchronization successful."
)

print(
    f"Tables: {len(source_tables)}"
)

print(
    f"Explicit indexes: "
    f"{len(source_indexes)}"
)

print(
    "Foreign key check: []"
)

print(
    f"New schema: {SCHEMA_PATH}"
)

print(
    f"Backup: {BACKUP_PATH}"
)


test_conn.close()
source_conn.close()