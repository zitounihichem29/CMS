import sqlite3
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

DATABASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = (
    DATABASE_DIR
    / "rsclub.db"
)

BACKUP_PATH = (
    DATABASE_DIR
    / "rsclub_backup_before_mandates_v2.db"
)


# ============================================================
# BACKUP
# ============================================================

if not BACKUP_PATH.exists():

    source = sqlite3.connect(
        DATABASE_PATH
    )

    backup = sqlite3.connect(
        BACKUP_PATH
    )

    source.backup(
        backup
    )

    backup.close()
    source.close()

    print(
        "Backup created:",
        BACKUP_PATH
    )

else:

    print(
        "Existing pre-migration backup preserved:",
        BACKUP_PATH
    )


# ============================================================
# DATABASE CONNECTION
# ============================================================

conn = sqlite3.connect(
    DATABASE_PATH
)

conn.row_factory = sqlite3.Row

conn.execute(
    "PRAGMA foreign_keys = ON"
)


try:

    # ========================================================
    # PRE-MIGRATION CHECKS
    # ========================================================

    active_count = conn.execute("""
        SELECT COUNT(*)
        FROM terms
        WHERE status = 'ACTIVE'
    """).fetchone()[0]


    draft_count = conn.execute("""
        SELECT COUNT(*)
        FROM terms
        WHERE status = 'DRAFT'
    """).fetchone()[0]


    print(
        "ACTIVE mandates:",
        active_count
    )

    print(
        "DRAFT mandates:",
        draft_count
    )


    if active_count > 1:

        raise RuntimeError(
            "Migration stopped: "
            "more than one ACTIVE mandate exists."
        )


    if draft_count > 1:

        raise RuntimeError(
            "Migration stopped: "
            "more than one DRAFT mandate exists."
        )


    # ========================================================
    # BEGIN TRANSACTION
    # ========================================================

    conn.execute(
        "BEGIN IMMEDIATE"
    )


    # ========================================================
    # 1. MANDATE ELECTIONS
    # ========================================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS mandate_elections (

            election_id INTEGER PRIMARY KEY,

            term_id INTEGER NOT NULL UNIQUE,

            election_date DATE NOT NULL,

            report_path TEXT,

            notes TEXT,

            recorded_by_user_id INTEGER,

            recorded_at TEXT
                NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            updated_by_user_id INTEGER,

            updated_at TEXT,

            FOREIGN KEY (term_id)
                REFERENCES terms(term_id)
                ON DELETE CASCADE,

            FOREIGN KEY (recorded_by_user_id)
                REFERENCES users(user_id)
                ON DELETE SET NULL,

            FOREIGN KEY (updated_by_user_id)
                REFERENCES users(user_id)
                ON DELETE SET NULL
        )
    """)


    # ========================================================
    # 2. MANDATE APPROVALS
    # ========================================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS mandate_approvals (

            approval_id INTEGER PRIMARY KEY,

            term_id INTEGER NOT NULL,

            approval_type TEXT NOT NULL,

            approved_by_user_id INTEGER NOT NULL,

            approved_at TEXT
                NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (term_id)
                REFERENCES terms(term_id)
                ON DELETE CASCADE,

            FOREIGN KEY (approved_by_user_id)
                REFERENCES users(user_id),

            CHECK (
                approval_type IN (
                    'PRESIDENT',
                    'VICE_PRESIDENT'
                )
            ),

            UNIQUE (
                term_id,
                approval_type
            )
        )
    """)


    # ========================================================
    # 3. MANDATE AUDIT LOG
    # ========================================================

    conn.execute("""
        CREATE TABLE IF NOT EXISTS mandate_audit_log (

            log_id INTEGER PRIMARY KEY,

            term_id INTEGER,

            term_name TEXT NOT NULL,

            actor_user_id INTEGER,

            action TEXT NOT NULL,

            details TEXT,

            emergency_reason TEXT,

            created_at TEXT
                NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (term_id)
                REFERENCES terms(term_id)
                ON DELETE SET NULL,

            FOREIGN KEY (actor_user_id)
                REFERENCES users(user_id)
                ON DELETE SET NULL
        )
    """)


    # ========================================================
    # 4. ONE DRAFT MAXIMUM
    # ========================================================

    conn.execute("""
        CREATE UNIQUE INDEX
        IF NOT EXISTS idx_terms_single_draft

        ON terms(status)

        WHERE status = 'DRAFT'
    """)


    # ========================================================
    # USEFUL INDEXES
    # ========================================================

    conn.execute("""
        CREATE INDEX
        IF NOT EXISTS idx_mandate_approvals_term

        ON mandate_approvals(term_id)
    """)


    conn.execute("""
        CREATE INDEX
        IF NOT EXISTS idx_mandate_audit_log_term

        ON mandate_audit_log(term_id)
    """)


    conn.execute("""
        CREATE INDEX
        IF NOT EXISTS idx_mandate_audit_log_created_at

        ON mandate_audit_log(created_at)
    """)


    # ========================================================
    # COMMIT
    # ========================================================

    conn.commit()


except Exception:

    conn.rollback()
    conn.close()

    print(
        "Migration failed. "
        "Database changes rolled back."
    )

    raise


# ============================================================
# POST-MIGRATION VERIFICATION
# ============================================================

tables = {
    row[0]
    for row in conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
    """).fetchall()
}


required_tables = {
    "mandate_elections",
    "mandate_approvals",
    "mandate_audit_log",
}


missing_tables = (
    required_tables
    - tables
)


if missing_tables:

    conn.close()

    raise RuntimeError(
        "Missing mandate tables: "
        f"{sorted(missing_tables)}"
    )


indexes = {
    row[0]
    for row in conn.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'index'
    """).fetchall()
}


if "idx_terms_single_draft" not in indexes:

    conn.close()

    raise RuntimeError(
        "idx_terms_single_draft "
        "was not created."
    )


integrity = conn.execute(
    "PRAGMA integrity_check"
).fetchone()[0]


foreign_key_errors = conn.execute(
    "PRAGMA foreign_key_check"
).fetchall()


print()
print(
    "========================================"
)
print(
    "MANDATES V2 MIGRATION SUCCESSFUL"
)
print(
    "========================================"
)

print(
    "mandate_elections: OK"
)

print(
    "mandate_approvals: OK"
)

print(
    "mandate_audit_log: OK"
)

print(
    "Single DRAFT protection: OK"
)

print(
    "Integrity check:",
    integrity
)

print(
    "Foreign key check:",
    foreign_key_errors
)


conn.close()


if integrity != "ok":

    raise RuntimeError(
        "Database integrity check failed."
    )


if foreign_key_errors:

    raise RuntimeError(
        "Foreign-key check failed."
    )