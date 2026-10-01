import shutil
import sqlite3
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parent

REAL_DB = DATABASE_DIR / "rsclub.db"
TEST_DB = DATABASE_DIR / "mandates_v2_constraints_test.db"


# ============================================================
# PREPARE TEMPORARY DATABASE
# ============================================================

if TEST_DB.exists():
    TEST_DB.unlink()

shutil.copy2(
    REAL_DB,
    TEST_DB
)


conn = sqlite3.connect(
    TEST_DB
)

conn.row_factory = sqlite3.Row

conn.execute(
    "PRAGMA foreign_keys = ON"
)


try:

    # ========================================================
    # CURRENT STATE
    # ========================================================

    active_term = conn.execute("""
        SELECT term_id, name
        FROM terms
        WHERE status = 'ACTIVE'
        LIMIT 1
    """).fetchone()


    draft_term = conn.execute("""
        SELECT term_id, name
        FROM terms
        WHERE status = 'DRAFT'
        LIMIT 1
    """).fetchone()


    user = conn.execute("""
        SELECT user_id, username
        FROM users
        WHERE is_active = 1
        ORDER BY user_id
        LIMIT 1
    """).fetchone()


    if active_term is None:
        raise RuntimeError(
            "No ACTIVE mandate found."
        )

    if draft_term is None:
        raise RuntimeError(
            "No DRAFT mandate found."
        )

    if user is None:
        raise RuntimeError(
            "No active user found."
        )


    print(
        "ACTIVE:",
        active_term["name"]
    )

    print(
        "DRAFT:",
        draft_term["name"]
    )

    print(
        "Test user:",
        user["username"]
    )


    # ========================================================
    # TEST 1 - SECOND DRAFT MUST FAIL
    # ========================================================

    try:

        conn.execute("""
            INSERT INTO terms (
                name,
                start_date,
                end_date,
                status
            )
            VALUES (
                'TEST-DRAFT',
                '2099-01-01',
                '2099-12-31',
                'DRAFT'
            )
        """)

        raise RuntimeError(
            "ERROR: SQLite allowed a second DRAFT."
        )

    except sqlite3.IntegrityError:

        conn.rollback()

        print(
            "Second DRAFT rejected: OK"
        )


    # ========================================================
    # TEST 2 - SECOND ACTIVE MUST FAIL
    # ========================================================

    try:

        conn.execute("""
            INSERT INTO terms (
                name,
                start_date,
                end_date,
                status
            )
            VALUES (
                'TEST-ACTIVE',
                '2098-01-01',
                '2098-12-31',
                'ACTIVE'
            )
        """)

        raise RuntimeError(
            "ERROR: SQLite allowed a second ACTIVE."
        )

    except sqlite3.IntegrityError:

        conn.rollback()

        print(
            "Second ACTIVE rejected: OK"
        )


    # ========================================================
    # TEST 3 - INVALID APPROVAL TYPE MUST FAIL
    # ========================================================

    try:

        conn.execute("""
            INSERT INTO mandate_approvals (
                term_id,
                approval_type,
                approved_by_user_id
            )
            VALUES (?, ?, ?)
        """, (
            draft_term["term_id"],
            "HEAD",
            user["user_id"],
        ))

        raise RuntimeError(
            "ERROR: invalid approval type accepted."
        )

    except sqlite3.IntegrityError:

        conn.rollback()

        print(
            "Invalid approval type rejected: OK"
        )


    # ========================================================
    # TEST 4 - ONE PRESIDENT APPROVAL PER TERM
    # ========================================================

    conn.execute("""
        INSERT INTO mandate_approvals (
            term_id,
            approval_type,
            approved_by_user_id
        )
        VALUES (?, ?, ?)
    """, (
        draft_term["term_id"],
        "PRESIDENT",
        user["user_id"],
    ))

    conn.commit()


    try:

        conn.execute("""
            INSERT INTO mandate_approvals (
                term_id,
                approval_type,
                approved_by_user_id
            )
            VALUES (?, ?, ?)
        """, (
            draft_term["term_id"],
            "PRESIDENT",
            user["user_id"],
        ))

        raise RuntimeError(
            "ERROR: duplicate President approval accepted."
        )

    except sqlite3.IntegrityError:

        conn.rollback()

        print(
            "Duplicate President approval rejected: OK"
        )


    # ========================================================
    # TEST 5 - ONE ELECTION RECORD PER TERM
    # ========================================================

    conn.execute("""
        INSERT INTO mandate_elections (
            term_id,
            election_date,
            recorded_by_user_id
        )
        VALUES (?, ?, ?)
    """, (
        draft_term["term_id"],
        "2099-09-15",
        user["user_id"],
    ))

    conn.commit()


    try:

        conn.execute("""
            INSERT INTO mandate_elections (
                term_id,
                election_date,
                recorded_by_user_id
            )
            VALUES (?, ?, ?)
        """, (
            draft_term["term_id"],
            "2099-09-16",
            user["user_id"],
        ))

        raise RuntimeError(
            "ERROR: duplicate election accepted."
        )

    except sqlite3.IntegrityError:

        conn.rollback()

        print(
            "Duplicate election rejected: OK"
        )


    # ========================================================
    # FINAL CHECKS
    # ========================================================

    integrity = conn.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]


    foreign_keys = conn.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()


    print()
    print(
        "========================================"
    )
    print(
        "MANDATES V2 CONSTRAINT TEST SUCCESSFUL"
    )
    print(
        "========================================"
    )

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


finally:

    conn.close()

    if TEST_DB.exists():
        TEST_DB.unlink()

    print(
        "Temporary database deleted."
    )