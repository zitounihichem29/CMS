import shutil
import sqlite3
from pathlib import Path

from routes.mandates import (
    get_mandate_election,
    get_mandate_approvals,
    log_mandate_action,
    reset_mandate_approvals,
    get_person_cms_account,
    get_role_holder,
    get_hr_head,
)


# ============================================================
# PATHS
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parent

REAL_DB = (
    BACKEND_DIR.parent
    / "database"
    / "rsclub.db"
)

TEST_DB = (
    BACKEND_DIR.parent
    / "database"
    / "mandate_helpers_test.db"
)


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

cursor = conn.cursor()


try:

    # ========================================================
    # LOAD ACTIVE + DRAFT TERMS
    # ========================================================

    active_term = cursor.execute("""
        SELECT term_id, name

        FROM terms

        WHERE status = 'ACTIVE'

        LIMIT 1
    """).fetchone()


    draft_term = cursor.execute("""
        SELECT term_id, name

        FROM terms

        WHERE status = 'DRAFT'

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


    print(
        "ACTIVE:",
        active_term["name"]
    )

    print(
        "DRAFT:",
        draft_term["name"]
    )


    # ========================================================
    # TEST USER
    # ========================================================

    actor = cursor.execute("""
        SELECT
            user_id,
            username

        FROM users

        WHERE is_active = 1

        ORDER BY user_id

        LIMIT 1
    """).fetchone()


    if actor is None:
        raise RuntimeError(
            "No active user found."
        )


    print(
        "Test actor:",
        actor["username"]
    )


    # ========================================================
    # TEST 1 - GET ELECTION
    # ========================================================

    election = get_mandate_election(
        cursor,
        draft_term["term_id"],
    )


    if election is None:

        print(
            "Election helper: OK "
            "(no election recorded yet)"
        )

    else:

        print(
            "Election helper: OK "
            f"(election_id={election['election_id']})"
        )


    # ========================================================
    # CLEAN TEMP APPROVALS
    # ========================================================

    cursor.execute("""
        DELETE FROM mandate_approvals

        WHERE term_id = ?
    """, (
        draft_term["term_id"],
    ))

    conn.commit()


    # ========================================================
    # TEST 2 - APPROVAL HELPER EMPTY STATE
    # ========================================================

    approvals = get_mandate_approvals(
        cursor,
        draft_term["term_id"],
    )


    if (
        approvals["PRESIDENT"] is not None
        or
        approvals["VICE_PRESIDENT"] is not None
    ):

        raise RuntimeError(
            "Approval helper did not return "
            "an empty state."
        )


    print(
        "Empty approval state: OK"
    )


    # ========================================================
    # TEST 3 - INSERT TWO APPROVALS
    # ========================================================

    cursor.execute("""
        INSERT INTO mandate_approvals (
            term_id,
            approval_type,
            approved_by_user_id
        )

        VALUES (?, 'PRESIDENT', ?)
    """, (
        draft_term["term_id"],
        actor["user_id"],
    ))


    cursor.execute("""
        INSERT INTO mandate_approvals (
            term_id,
            approval_type,
            approved_by_user_id
        )

        VALUES (?, 'VICE_PRESIDENT', ?)
    """, (
        draft_term["term_id"],
        actor["user_id"],
    ))


    conn.commit()


    approvals = get_mandate_approvals(
        cursor,
        draft_term["term_id"],
    )


    if approvals["PRESIDENT"] is None:
        raise RuntimeError(
            "President approval not returned."
        )


    if approvals["VICE_PRESIDENT"] is None:
        raise RuntimeError(
            "Vice-President approval not returned."
        )


    print(
        "Approval retrieval: OK"
    )


    # ========================================================
    # TEST 4 - RESET APPROVALS
    # ========================================================

    reset_result = reset_mandate_approvals(
        cursor=cursor,
        term_id=draft_term["term_id"],
        actor_user_id=actor["user_id"],
        reason="Automated helper test.",
    )

    conn.commit()


    if reset_result is not True:

        raise RuntimeError(
            "Approval reset should have returned True."
        )


    approvals_after_reset = (
        get_mandate_approvals(
            cursor,
            draft_term["term_id"],
        )
    )


    if (
        approvals_after_reset[
            "PRESIDENT"
        ] is not None
        or
        approvals_after_reset[
            "VICE_PRESIDENT"
        ] is not None
    ):

        raise RuntimeError(
            "Approvals were not deleted."
        )


    print(
        "Approval reset: OK"
    )


    # ========================================================
    # TEST 5 - RESET GENERATED AUDIT LOG
    # ========================================================

    reset_log = cursor.execute("""
        SELECT
            action,
            details,
            actor_user_id

        FROM mandate_audit_log

        WHERE term_id = ?
          AND action = 'APPROVALS_RESET'

        ORDER BY log_id DESC

        LIMIT 1
    """, (
        draft_term["term_id"],
    )).fetchone()


    if reset_log is None:

        raise RuntimeError(
            "APPROVALS_RESET audit log "
            "was not created."
        )


    if (
        reset_log["actor_user_id"]
        != actor["user_id"]
    ):

        raise RuntimeError(
            "Incorrect audit actor."
        )


    print(
        "Approval reset audit log: OK"
    )


    # ========================================================
    # TEST 6 - MANUAL AUDIT LOG
    # ========================================================

    log_mandate_action(
        cursor=cursor,
        term_id=draft_term["term_id"],
        actor_user_id=actor["user_id"],
        action="TEST_HELPER_ACTION",
        details="Mandate helper automated test.",
    )

    conn.commit()


    manual_log = cursor.execute("""
        SELECT
            action,
            term_name,
            actor_user_id

        FROM mandate_audit_log

        WHERE term_id = ?
          AND action = 'TEST_HELPER_ACTION'

        ORDER BY log_id DESC

        LIMIT 1
    """, (
        draft_term["term_id"],
    )).fetchone()


    if manual_log is None:

        raise RuntimeError(
            "Manual audit log was not created."
        )


    if (
        manual_log["term_name"]
        != draft_term["name"]
    ):

        raise RuntimeError(
            "Audit term name is incorrect."
        )


    print(
        "Manual audit log: OK"
    )


    # ========================================================
    # TEST 7 - ROLE HOLDER
    # ========================================================

    president = get_role_holder(
        cursor,
        active_term["term_id"],
        "PRESIDENT",
    )


    if president is None:

        raise RuntimeError(
            "ACTIVE President not found."
        )


    print(
        "Role holder helper: OK -",
        president["first_name"],
        president["last_name"]
    )


    # ========================================================
    # TEST 8 - PERSON CMS ACCOUNT
    # ========================================================

    president_account = (
        get_person_cms_account(
            cursor,
            president["person_id"],
        )
    )


    if president_account is None:

        raise RuntimeError(
            "President CMS account not found."
        )


    print(
        "CMS account helper: OK -",
        president_account["username"]
    )


    # ========================================================
    # TEST 9 - HR HEAD
    # ========================================================

    hr_head = get_hr_head(
        cursor,
        active_term["term_id"],
    )


    if hr_head is None:

        raise RuntimeError(
            "ACTIVE HR Head not found."
        )


    print(
        "HR Head helper: OK -",
        hr_head["first_name"],
        hr_head["last_name"]
    )


    # ========================================================
    # FINAL DATABASE CHECKS
    # ========================================================

    integrity = cursor.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]


    foreign_keys = cursor.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()


    if integrity != "ok":

        raise RuntimeError(
            "Integrity check failed."
        )


    if foreign_keys:

        raise RuntimeError(
            "Foreign-key check failed."
        )


    print()
    print(
        "========================================"
    )
    print(
        "MANDATE HELPERS TEST SUCCESSFUL"
    )
    print(
        "========================================"
    )

    print(
        "Election helper: OK"
    )

    print(
        "Approval helpers: OK"
    )

    print(
        "Approval reset: OK"
    )

    print(
        "Audit logging: OK"
    )

    print(
        "Role holder lookup: OK"
    )

    print(
        "CMS account lookup: OK"
    )

    print(
        "HR Head lookup: OK"
    )

    print(
        "Integrity check:",
        integrity
    )

    print(
        "Foreign key check:",
        foreign_keys
    )


finally:

    conn.close()

    if TEST_DB.exists():
        TEST_DB.unlink()

    print(
        "Temporary database deleted."
    )