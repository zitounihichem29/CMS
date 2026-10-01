import shutil
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
    / "election_update_test.db"
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


database.DATABASE_PATH = TEST_DB


conn = database.get_db_connection()


try:

    # ========================================================
    # ACTIVE + DRAFT
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
            "No outgoing President found."
        )


    # ========================================================
    # OUTGOING VP
    # ========================================================

    outgoing_vp = conn.execute("""
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
          AND roles.name = 'VICE_PRESIDENT'
          AND users.is_active = 1

        LIMIT 1
    """, (
        active_term["term_id"],
    )).fetchone()


    if outgoing_vp is None:

        raise RuntimeError(
            "No outgoing Vice-President found."
        )


    print(
        "Outgoing President:",
        outgoing_president["username"]
    )

    print(
        "Outgoing VP:",
        outgoing_vp["username"]
    )


    # ========================================================
    # SELECT THREE DIFFERENT PEOPLE
    # ========================================================

    existing_executives = conn.execute("""
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

        ORDER BY
            CASE roles.name
                WHEN 'PRESIDENT' THEN 1
                WHEN 'VICE_PRESIDENT' THEN 2
                WHEN 'SECRETARY_GENERAL' THEN 3
            END
    """, (
        draft_term["term_id"],
    )).fetchall()


    selected_ids = []


    for row in existing_executives:

        if (
            row["person_id"]
            not in selected_ids
        ):

            selected_ids.append(
                row["person_id"]
            )


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


    first_president = selected_ids[0]
    first_vp = selected_ids[1]
    first_sg = selected_ids[2]


    print()
    print(
        "Initial election:"
    )

    print(
        "President person_id:",
        first_president
    )

    print(
        "Vice-President person_id:",
        first_vp
    )

    print(
        "Secretary General person_id:",
        first_sg
    )


finally:

    conn.close()


# ============================================================
# STEP 1
# PRESIDENT RECORDS FIRST ELECTION
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
                str(first_president),

            "vice_president_person_id":
                str(first_vp),

            "secretary_general_person_id":
                str(first_sg),

            "notes":
                "Initial election result.",
        },
        follow_redirects=False,
    )


    print()
    print(
        "Initial election POST:",
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
            "Initial election could not be saved."
        )


# ============================================================
# CAPTURE ORIGINAL MEMBERSHIP IDS
# ============================================================

conn = database.get_db_connection()


try:

    original_memberships = conn.execute("""
        SELECT
            memberships.membership_id,
            memberships.person_id,
            roles.name AS role_name

        FROM memberships

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        WHERE memberships.term_id = ?

          AND memberships.person_id
              IN (?, ?, ?)
    """, (
        draft_term["term_id"],
        first_president,
        first_vp,
        first_sg,
    )).fetchall()


    original_membership_ids = {
        row["person_id"]:
            row["membership_id"]

        for row in original_memberships
    }


    if len(
        original_membership_ids
    ) != 3:

        raise RuntimeError(
            "Initial executive memberships "
            "were not created correctly."
        )


    initial_election = conn.execute("""
        SELECT
            election_id,
            recorded_by_user_id

        FROM mandate_elections

        WHERE term_id = ?
    """, (
        draft_term["term_id"],
    )).fetchone()


    if initial_election is None:

        raise RuntimeError(
            "Initial election record missing."
        )


    initial_election_id = (
        initial_election["election_id"]
    )


    # ========================================================
    # CREATE APPROVAL TO VERIFY UPDATE RESETS IT
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


    print(
        "Temporary approval inserted: OK"
    )


finally:

    conn.close()


# ============================================================
# STEP 2
# VP UPDATES THE EXISTING ELECTION
#
# Swap President and Vice-President.
# Same three people, therefore their existing membership
# rows should be preserved.
# ============================================================

updated_president = first_vp
updated_vp = first_president
updated_sg = first_sg


with app.test_client() as client:

    with client.session_transaction() as session:

        session["user_id"] = (
            outgoing_vp["user_id"]
        )


    response = client.post(
        f"/mandates/{draft_term['term_id']}/election/save",
        data={
            "election_date":
                "2026-09-16",

            "president_person_id":
                str(updated_president),

            "vice_president_person_id":
                str(updated_vp),

            "secretary_general_person_id":
                str(updated_sg),

            "notes":
                "Corrected election result.",
        },
        follow_redirects=False,
    )


    print(
        "Election update POST:",
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
            "Election update failed."
        )


    print(
        "Outgoing VP update permission: OK"
    )


# ============================================================
# VERIFY UPDATE
# ============================================================

conn = database.get_db_connection()


try:

    # ========================================================
    # ONLY ONE ELECTION RECORD
    # ========================================================

    election_count = conn.execute("""
        SELECT COUNT(*)

        FROM mandate_elections

        WHERE term_id = ?
    """, (
        draft_term["term_id"],
    )).fetchone()[0]


    if election_count != 1:

        raise RuntimeError(
            "Election update created "
            "a duplicate election record."
        )


    print(
        "Single election record: OK"
    )


    # ========================================================
    # SAME ELECTION ID
    # ========================================================

    updated_election = conn.execute("""
        SELECT
            election_id,
            election_date,
            notes,
            recorded_by_user_id,
            updated_by_user_id,
            updated_at

        FROM mandate_elections

        WHERE term_id = ?
    """, (
        draft_term["term_id"],
    )).fetchone()


    if (
        updated_election["election_id"]
        != initial_election_id
    ):

        raise RuntimeError(
            "Election ID changed during update."
        )


    print(
        "Election ID preserved: OK"
    )


    # ========================================================
    # UPDATED DATA
    # ========================================================

    if (
        updated_election[
            "election_date"
        ]
        != "2026-09-16"
    ):

        raise RuntimeError(
            "Election date was not updated."
        )


    if (
        updated_election["notes"]
        != "Corrected election result."
    ):

        raise RuntimeError(
            "Election notes were not updated."
        )


    if (
        updated_election[
            "recorded_by_user_id"
        ]
        != outgoing_president[
            "user_id"
        ]
    ):

        raise RuntimeError(
            "Original recorder was changed."
        )


    if (
        updated_election[
            "updated_by_user_id"
        ]
        != outgoing_vp["user_id"]
    ):

        raise RuntimeError(
            "Updater was not recorded correctly."
        )


    if (
        updated_election["updated_at"]
        is None
    ):

        raise RuntimeError(
            "Election update timestamp missing."
        )


    print(
        "Election update metadata: OK"
    )


    # ========================================================
    # EXECUTIVE ROLES UPDATED
    # ========================================================

    rows = conn.execute("""
        SELECT
            memberships.membership_id,
            memberships.person_id,
            memberships.department_id,
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


    executives = {
        row["role_name"]:
            row

        for row in rows
    }


    expected_roles = {
        "PRESIDENT":
            updated_president,

        "VICE_PRESIDENT":
            updated_vp,

        "SECRETARY_GENERAL":
            updated_sg,
    }


    for role_name, person_id in (
        expected_roles.items()
    ):

        row = executives.get(
            role_name
        )


        if row is None:

            raise RuntimeError(
                f"{role_name} missing "
                "after election update."
            )


        if (
            row["person_id"]
            != person_id
        ):

            raise RuntimeError(
                f"{role_name} was not updated."
            )


        if row["department_id"] is not None:

            raise RuntimeError(
                f"{role_name} unexpectedly "
                "has a department."
            )


    print(
        "Updated executive roles: OK"
    )


    # ========================================================
    # MEMBERSHIP IDS MUST BE PRESERVED
    # ========================================================

    current_rows = conn.execute("""
        SELECT
            membership_id,
            person_id

        FROM memberships

        WHERE term_id = ?

          AND person_id IN (?, ?, ?)
    """, (
        draft_term["term_id"],
        first_president,
        first_vp,
        first_sg,
    )).fetchall()


    current_membership_ids = {
        row["person_id"]:
            row["membership_id"]

        for row in current_rows
    }


    if (
        current_membership_ids
        != original_membership_ids
    ):

        raise RuntimeError(
            "Existing membership IDs "
            "were not preserved."
        )


    print(
        "Membership IDs preserved: OK"
    )


    # ========================================================
    # APPROVAL RESET
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
            "Election update did not "
            "reset previous approvals."
        )


    print(
        "Approvals reset after update: OK"
    )


    # ========================================================
    # AUDIT LOG
    # ========================================================

    updated_log = conn.execute("""
        SELECT
            action,
            actor_user_id

        FROM mandate_audit_log

        WHERE term_id = ?
          AND action = 'ELECTION_UPDATED'

        ORDER BY log_id DESC

        LIMIT 1
    """, (
        draft_term["term_id"],
    )).fetchone()


    if updated_log is None:

        raise RuntimeError(
            "ELECTION_UPDATED audit log missing."
        )


    if (
        updated_log["actor_user_id"]
        != outgoing_vp["user_id"]
    ):

        raise RuntimeError(
            "Election update audit actor "
            "is incorrect."
        )


    print(
        "Election update audit log: OK"
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
        "ELECTION UPDATE TEST SUCCESSFUL"
    )
    print(
        "========================================"
    )

    print(
        "Outgoing VP update permission: OK"
    )

    print(
        "Single election record: OK"
    )

    print(
        "Election ID preserved: OK"
    )

    print(
        "Election metadata update: OK"
    )

    print(
        "Executive role update: OK"
    )

    print(
        "Membership IDs preserved: OK"
    )

    print(
        "Approval reset: OK"
    )

    print(
        "ELECTION_UPDATED audit log: OK"
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