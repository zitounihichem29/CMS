import sqlite3
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parent

SOURCE_DB = DATABASE_DIR / "rsclub.db"
SCHEMA_FILE = DATABASE_DIR / "schema.sql"
TEST_DB = DATABASE_DIR / "schema_test.db"


# ============================================================
# REMOVE OLD TEST DATABASE
# ============================================================

if TEST_DB.exists():
    TEST_DB.unlink()


# ============================================================
# CREATE FRESH DATABASE FROM schema.sql
# ============================================================

schema_sql = SCHEMA_FILE.read_text(
    encoding="utf-8"
)

test_conn = sqlite3.connect(TEST_DB)

test_conn.execute(
    "PRAGMA foreign_keys = ON"
)

test_conn.executescript(
    schema_sql
)


# ============================================================
# OPEN REAL DATABASE
# ============================================================

source_conn = sqlite3.connect(SOURCE_DB)


# ============================================================
# COMPARE TABLES
# ============================================================

def get_tables(conn):

    return {
        row[0]
        for row in conn.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
        """).fetchall()
    }


source_tables = get_tables(source_conn)
test_tables = get_tables(test_conn)


print(
    "Source tables:",
    len(source_tables)
)

print(
    "Test tables:",
    len(test_tables)
)


if source_tables != test_tables:

    print(
        "Missing tables:",
        sorted(source_tables - test_tables)
    )

    print(
        "Extra tables:",
        sorted(test_tables - source_tables)
    )

    raise RuntimeError(
        "Table comparison failed."
    )


# ============================================================
# COMPARE TABLE STRUCTURES
# ============================================================

for table in sorted(source_tables):

    source_columns = source_conn.execute(
        f'PRAGMA table_info("{table}")'
    ).fetchall()

    test_columns = test_conn.execute(
        f'PRAGMA table_info("{table}")'
    ).fetchall()

    if source_columns != test_columns:

        raise RuntimeError(
            f"Column mismatch in table: {table}"
        )


# ============================================================
# COMPARE FOREIGN KEYS
# ============================================================

for table in sorted(source_tables):

    source_fk = source_conn.execute(
        f'PRAGMA foreign_key_list("{table}")'
    ).fetchall()

    test_fk = test_conn.execute(
        f'PRAGMA foreign_key_list("{table}")'
    ).fetchall()

    if source_fk != test_fk:

        raise RuntimeError(
            f"Foreign-key mismatch in table: {table}"
        )


# ============================================================
# COMPARE EXPLICIT INDEXES
# ============================================================

def get_explicit_indexes(conn):

    return {
        row[0]
        for row in conn.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'index'
              AND sql IS NOT NULL
              AND name NOT LIKE 'sqlite_%'
        """).fetchall()
    }


source_indexes = get_explicit_indexes(
    source_conn
)

test_indexes = get_explicit_indexes(
    test_conn
)


print(
    "Source explicit indexes:",
    len(source_indexes)
)

print(
    "Test explicit indexes:",
    len(test_indexes)
)


if source_indexes != test_indexes:

    raise RuntimeError(
        "Explicit index comparison failed."
    )


# ============================================================
# IMPORTANT OBJECTS
# ============================================================

if "training_attendance" not in test_tables:

    raise RuntimeError(
        "training_attendance is missing."
    )


if "idx_terms_single_active" not in test_indexes:

    raise RuntimeError(
        "idx_terms_single_active is missing."
    )


# ============================================================
# DATABASE CHECKS
# ============================================================

integrity = test_conn.execute(
    "PRAGMA integrity_check"
).fetchone()[0]


foreign_keys = test_conn.execute(
    "PRAGMA foreign_key_check"
).fetchall()


print(
    "Integrity check:",
    integrity
)

print(
    "Foreign key check:",
    foreign_keys
)


if integrity != "ok":

    raise RuntimeError(
        "Integrity check failed."
    )


if foreign_keys:

    raise RuntimeError(
        "Foreign-key check failed."
    )


# ============================================================
# SUCCESS
# ============================================================

print()
print(
    "========================================"
)
print(
    "SCHEMA REBUILD TEST SUCCESSFUL"
)
print(
    "========================================"
)

print(
    "training_attendance: OK"
)

print(
    "idx_terms_single_active: OK"
)

print(
    "All table structures: OK"
)

print(
    "All foreign keys: OK"
)

print(
    "Fresh database creation: OK"
)


source_conn.close()
test_conn.close()


# ============================================================
# REMOVE TEST DATABASE
# ============================================================

TEST_DB.unlink()

print()
print(
    "Temporary schema_test.db deleted."
)