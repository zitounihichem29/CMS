import shutil
import sqlite3
from pathlib import Path

import database
from app import app


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
    / "election_result_test.db"
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


# Every existing get_db_connection()
# will now use the temporary database.
database.DATABASE_PATH = TEST_DB


conn = database.get_db_connection()


try:

    # ========================================================
    # ACTIVE + DRAFT TERMS
    # ========================================================

    active_term = conn.execute("""
        SELECT
            term_id,
            name

        FROM terms

        WHERE status = 'ACTIVE'

        LIMIT 1
    """).fetchone()


    draft_term = conn.execute("""
        SELECT
            term_id,
            name

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
    # OUTGOING PRESIDENT
    # ========================================================

    outgoing_president = conn.execute("""
        SELECT
            users.user_id,
            users.username

        FROM users

        JOIN people
            ON users.person_id =
               people.person_id

        JOIN memberships
            ON people.person_id =
               memberships.person_id

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        WHERE memberships.term_id = ?
          AND roles.name = 'PRESIDENT'
          AND users.is_active = 1

        LIMIT 1
    """, (
        active_term["term_id"],
    )).fetchone()


    if outgoing_president is None:
        raise RuntimeError(
            "No active outgoing President found."
        )


    print(
        "Outgoing President:",
        outgoing_president["username"]
    )


    # ========================================================
    # HR HEAD - USED TO TEST FORBIDDEN ACCESS
    # ========================================================

    hr_head = conn.execute("""
        SELECT
            users.user_id,
            users.username

        FROM users

        JOIN people
            ON users.person_id =
               people.person_id

        JOIN memberships
            ON people.person_id =
               memberships.person_id

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        WHERE memberships.term_id = ?
          AND roles.name = 'HEAD'
          AND memberships.department_id = 1
          AND users.is_active = 1

        LIMIT 1
    """, (
        active_term["term_id"],
    )).fetchone()


    if hr_head is None:
        raise RuntimeError(
            "No active HR Head found."
        )


    # ========================================================
    # CHOOSE 3 PEOPLE FOR TEST ELECTION
    #
    # Prefer existing DRAFT executives when possible.
    # ========================================================

    draft_executives = conn.execute("""
        SELECT
            memberships.person_id,
            roles.name AS role_name

        FROM memberships

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        WHERE memberships.term_id = ?

          AND roles.name IN (
              'PRESIDENT',
              'VICE_PRESIDENT',
              'SECRETARY_GENERAL'
          )
    """, (
        draft_term["term_id"],
    )).fetchall()


    executive_people = {
        row["role_name"]:
            row["person_id"]

        for row in draft_executives
    }


    selected_ids = []


    for role_name in (
        "PRESIDENT",
        "VICE_PRESIDENT",
        "SECRETARY_GENERAL",
    ):

        person_id = executive_people.get(
            role_name
        )

        if (
            person_id is not None
            and person_id not in selected_ids
        ):

            selected_ids.append(
                person_id
            )


    # If the current DRAFT does not already contain
    # 3 distinct executives, complete the selection
    # with existing people.

    if len(selected_ids) < 3:

        people = conn.execute("""
            SELECT person_id

            FROM people

            ORDER BY person_id
        """).fetchall()


        for person in people:

            if (
                person["person_id"]
                not in selected_ids
            ):

                selected_ids.append(
                    person["person_id"]
                )


            if len(selected_ids) == 3:
                break


    if len(selected_ids) != 3:

        raise RuntimeError(
            "Could not find three different people."
        )


    president_person_id = (
        selected_ids[0]
    )

    vice_president_person_id = (
        selected_ids[1]
    )

    secretary_general_person_id = (
        selected_ids[2]
    )


    # ========================================================
    # DISPLAY SELECTED PEOPLE
    # ========================================================

    selected_people = conn.execute("""
        SELECT
            person_id,
            first_name,
            last_name

        FROM people

        WHERE person_id IN (?, ?, ?)
    """, (
        president_person_id,
        vice_president_person_id,
        secretary_general_person_id,
    )).fetchall()


    print()
    print(
        "Selected election people:"
    )


    for person in selected_people:

        print(
            "-",
            person["person_id"],
            person["first_name"],
            person["last_name"]
        )


    # ========================================================
    # INSERT TEMPORARY APPROVALS
    #
    # Saving the election must remove them.
    # ========================================================

    conn.execute("""
        DELETE FROM mandate_approvals

        WHERE term_id = ?
    """, (
        draft_term["term_id"],
    ))


    conn.execute("""
        INSERT INTO mandate_approvals (
            term_id,
            approval_type,
            approved_by_user_id
        )

        VALUES (?, 'PRESIDENT', ?)
    """, (
        draft_term["term_id"],
        outgoing_president["user_id"],
    ))


    conn.commit()


    print()
    print(
        "Temporary approval inserted: OK"
    )


finally:

    conn.close()


# ============================================================
# TEST 1 - HR MUST BE FORBIDDEN
# ============================================================

with app.test_client() as client:

    with client.session_transaction() as session:

        session["user_id"] = (
            hr_head["user_id"]
        )


    response = client.post(
        f"/mandates/{draft_term['term_id']}/election/save",
        data={
            "election_date":
                "2026-09-15",

            "president_person_id":
                str(
                    president_person_id
                ),

            "vice_president_person_id":
                str(
                    vice_president_person_id
                ),

            "secretary_general_person_id":
                str(
                    secretary_general_person_id
                ),

            "notes":
                "Automated election test.",
        },
        follow_redirects=False,
    )


    print()
    print(
        "HR election POST status:",
        response.status_code
    )


    if response.status_code != 403:

        raise RuntimeError(
            "HR Head was incorrectly allowed "
            "to modify the election."
        )


    print(
        "HR election modification blocked: OK"
    )


# ============================================================
# TEST 2 - OUTGOING PRESIDENT SAVES ELECTION
# ============================================================

with app.test_client() as client:

    with client.session_transaction() as session:

        session["user_id"] = (
            outgoing_president["user_id"]
        )


    response = client.post(
        f"/mandates/{draft_term['term_id']}/election/save",
        data={
            "election_date":
                "2026-09-15",

            "president_person_id":
                str(
                    president_person_id
                ),

            "vice_president_person_id":
                str(
                    vice_president_person_id
                ),

            "secretary_general_person_id":
                str(
                    secretary_general_person_id
                ),

            "notes":
                "Automated election test.",
        },
        follow_redirects=False,
    )


    print(
        "President election POST status:",
        response.status_code
    )


    if response.status_code not in (
        301,
        302,
        303,
        307,
        308,
    ):

        print(
            response.get_data(
                as_text=True
            )[:1000]
        )

        raise RuntimeError(
            "Election result was not saved."
        )


    print(
        "Election route accepted: OK"
    )


# ============================================================
# VERIFY DATABASE RESULT
# ============================================================

conn = database.get_db_connection()


try:

    election = conn.execute("""
        SELECT
            election_date,
            notes,
            recorded_by_user_id

        FROM mandate_elections

        WHERE term_id = ?
    """, (
        draft_term["term_id"],
    )).fetchone()


    if election is None:

        raise RuntimeError(
            "Election record was not created."
        )


    if (
        election["election_date"]
        != "2026-09-15"
    ):

        raise RuntimeError(
            "Election date is incorrect."
        )


    print(
        "Election record created: OK"
    )


    # ========================================================
    # VERIFY EXECUTIVE MEMBERSHIPS
    # ========================================================

    executive_rows = conn.execute("""
        SELECT
            memberships.person_id,
            roles.name AS role_name,
            memberships.department_id

        FROM memberships

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        WHERE memberships.term_id = ?

          AND roles.name IN (
              'PRESIDENT',
              'VICE_PRESIDENT',
              'SECRETARY_GENERAL'
          )
    """, (
        draft_term["term_id"],
    )).fetchall()


    executives = {
        row["role_name"]: row
        for row in executive_rows
    }


    expected = {
        "PRESIDENT":
            president_person_id,

        "VICE_PRESIDENT":
            vice_president_person_id,

        "SECRETARY_GENERAL":
            secretary_general_person_id,
    }


    for role_name, person_id in (
        expected.items()
    ):

        row = executives.get(
            role_name
        )


        if row is None:

            raise RuntimeError(
                f"{role_name} was not created."
            )


        if (
            row["person_id"]
            != person_id
        ):

            raise RuntimeError(
                f"{role_name} has the wrong person."
            )


        if (
            row["department_id"]
            is not None
        ):

            raise RuntimeError(
                f"{role_name} should not "
                "have a department."
            )


    print(
        "Executive memberships: OK"
    )


    # ========================================================
    # APPROVAL MUST HAVE BEEN RESET
    # ========================================================

    approval_count = conn.execute("""
        SELECT COUNT(*)

        FROM mandate_approvals

        WHERE term_id = ?
    """, (
        draft_term["term_id"],
    )).fetchone()[0]


    if approval_count != 0:

        raise RuntimeError(
            "Previous approvals were not reset."
        )


    print(
        "Previous approvals reset: OK"
    )


    # ========================================================
    # AUDIT LOGS
    # ========================================================

    election_log = conn.execute("""
        SELECT action

        FROM mandate_audit_log

        WHERE term_id = ?

          AND action = 'ELECTION_RECORDED'

        ORDER BY log_id DESC

        LIMIT 1
    """, (
        draft_term["term_id"],
    )).fetchone()


    if election_log is None:

        raise RuntimeError(
            "ELECTION_RECORDED audit log "
            "was not created."
        )


    print(
        "Election audit log: OK"
    )


    reset_log = conn.execute("""
        SELECT action

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


    print(
        "Approval reset audit log: OK"
    )


    # ========================================================
    # DATABASE HEALTH
    # ========================================================

    integrity = conn.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]


    foreign_keys = conn.execute(
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
        "ELECTION RESULT TEST SUCCESSFUL"
    )
    print(
        "========================================"
    )

    print(
        "HR permission protection: OK"
    )

    print(
        "Outgoing President permission: OK"
    )

    print(
        "Election record: OK"
    )

    print(
        "Executive memberships: OK"
    )

    print(
        "Approval reset: OK"
    )

    print(
        "Audit logs: OK"
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