import shutil
import sqlite3
from pathlib import Path

from reconstruct_2025_2026 import (
    reconstruct_database,
)


# ============================================================
# PATHS
# ============================================================

DATABASE_DIR = (
    Path(__file__).resolve().parent
)

REAL_DB = (
    DATABASE_DIR
    / "rsclub.db"
)

TEST_DB = (
    DATABASE_DIR
    / "reconstruction_2025_2026_test.db"
)


# ============================================================
# CONNECTION
# ============================================================

def connect(
    path,
):

    conn = sqlite3.connect(
        path,
        timeout=10,
    )

    conn.row_factory = (
        sqlite3.Row
    )

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# ============================================================
# ASSERTION
# ============================================================

def require(
    condition,
    message,
):

    if not condition:

        raise RuntimeError(
            message
        )


# ============================================================
# PREPARE TEMP DATABASE
# ============================================================

if TEST_DB.exists():

    TEST_DB.unlink()


shutil.copy2(
    REAL_DB,
    TEST_DB,
)


try:

    # ========================================================
    # SNAPSHOT DRAFT BEFORE TEST
    # ========================================================

    before = connect(
        TEST_DB
    )


    draft_before = (
        before.execute(
            """
            SELECT
                term_id,
                status

            FROM terms

            WHERE name =
                  '2026/2027'
            """
        ).fetchone()
    )


    require(
        draft_before is not None,
        "2026/2027 DRAFT missing.",
    )


    draft_memberships_before = (
        before.execute(
            """
            SELECT
                membership_id,
                person_id,
                role_id,
                department_id

            FROM memberships

            WHERE term_id = ?

            ORDER BY
                membership_id
            """,
            (
                draft_before[
                    "term_id"
                ],
            ),
        ).fetchall()
    )


    draft_snapshot_before = [

        tuple(
            row
        )

        for row
        in draft_memberships_before

    ]


    before.close()


    # ========================================================
    # RUN RECONSTRUCTION ON TEMP COPY
    # ========================================================

    reconstruct_database(

        db_path=TEST_DB,

        create_backup_file=False,

        verbose=False,

    )


    conn = connect(
        TEST_DB
    )


    # ========================================================
    # TERM STATUS
    # ========================================================

    active = (
        conn.execute(
            """
            SELECT
                term_id,
                status

            FROM terms

            WHERE name =
                  '2025/2026'
            """
        ).fetchone()
    )


    draft = (
        conn.execute(
            """
            SELECT
                term_id,
                status

            FROM terms

            WHERE name =
                  '2026/2027'
            """
        ).fetchone()
    )


    require(

        active is not None

        and

        active[
            "status"
        ] == "ACTIVE",

        "2025/2026 is not ACTIVE "
        "after reconstruction.",

    )


    require(

        draft is not None

        and

        draft[
            "status"
        ] == "DRAFT",

        "2026/2027 is not DRAFT "
        "after reconstruction.",

    )


    # ========================================================
    # EXPECTED REAL BOARD
    # ========================================================

    expected = [

        (
            "Yasmine",
            "HAMMA",
            "PRESIDENT",
            None,
        ),

        (
            "Nour el Houda",
            "AMELLAL",
            "VICE_PRESIDENT",
            None,
        ),

        (
            "Farah",
            "DJERMOUNE",
            "SECRETARY_GENERAL",
            None,
        ),

        (
            "Sarah",
            "BELHADJ",
            "HEAD",
            "Projects & Activities",
        ),

        (
            "Wissal",
            "SOUILAH",
            "HEAD",
            "External Relations",
        ),

        (
            "Abd el Ouadoud",
            "BENANTAR",
            "HEAD",
            "Communication & Marketing",
        ),

        (
            "Karim",
            "TAMDA",
            "HEAD",
            "Communication & Marketing",
        ),

        (
            "Mohamed",
            "MASMOUDI",
            "HEAD",
            "Human Resources",
        ),

    ]


    # ========================================================
    # VERIFY BOARD
    # ========================================================

    for (
        first_name,
        last_name,
        role_name,
        department_name,
    ) in expected:

        row = (
            conn.execute(
                """
                SELECT
                    people.first_name,
                    people.last_name,

                    roles.name
                        AS role_name,

                    departments.name
                        AS department_name

                FROM memberships


                JOIN people

                    ON memberships.person_id =
                       people.person_id


                JOIN roles

                    ON memberships.role_id =
                       roles.role_id


                LEFT JOIN departments

                    ON memberships.department_id =
                       departments.department_id


                WHERE memberships.term_id = ?

                  AND LOWER(
                      people.first_name
                  ) = LOWER(?)

                  AND LOWER(
                      people.last_name
                  ) = LOWER(?)


                LIMIT 1
                """,
                (
                    active[
                        "term_id"
                    ],

                    first_name,

                    last_name,
                ),
            ).fetchone()
        )


        require(
            row is not None,

            "Missing board member: "
            f"{first_name} "
            f"{last_name}",
        )


        require(
            row[
                "role_name"
            ] == role_name,

            "Wrong role for "
            f"{first_name} "
            f"{last_name}",
        )


        require(
            row[
                "department_name"
            ] == department_name,

            "Wrong department for "
            f"{first_name} "
            f"{last_name}",
        )


    # ========================================================
    # EXACT EXECUTIVE COUNTS
    # ========================================================

    for role_name in (

        "PRESIDENT",

        "VICE_PRESIDENT",

        "SECRETARY_GENERAL",

    ):

        count = (
            conn.execute(
                """
                SELECT
                    COUNT(*)

                FROM memberships


                JOIN roles

                    ON memberships.role_id =
                       roles.role_id


                WHERE memberships.term_id = ?

                  AND roles.name = ?
                """,
                (
                    active[
                        "term_id"
                    ],

                    role_name,
                ),
            ).fetchone()[0]
        )


        require(
            count == 1,

            "Invalid count for "
            f"{role_name}: "
            f"{count}",
        )


    # ========================================================
    # NO ALUMNI IN ACTIVE ROSTER
    # ========================================================

    alumni_count = (
        conn.execute(
            """
            SELECT
                COUNT(*)

            FROM memberships


            JOIN roles

                ON memberships.role_id =
                   roles.role_id


            WHERE memberships.term_id = ?

              AND roles.name = 'ALUMNI'
            """,
            (
                active[
                    "term_id"
                ],
            ),
        ).fetchone()[0]
    )


    require(
        alumni_count == 0,

        "ALUMNI still exists "
        "in active roster.",
    )


    # ========================================================
    # OLD WRONG WALID SG ASSIGNMENT REMOVED
    # ========================================================

    wrong_walid = (
        conn.execute(
            """
            SELECT
                COUNT(*)

            FROM memberships


            JOIN people

                ON memberships.person_id =
                   people.person_id


            JOIN roles

                ON memberships.role_id =
                   roles.role_id


            WHERE memberships.term_id = ?

              AND LOWER(
                  people.first_name
              ) = 'walid'

              AND LOWER(
                  people.last_name
              ) = 'benidir'

              AND roles.name =
                  'SECRETARY_GENERAL'
            """,
            (
                active[
                    "term_id"
                ],
            ),
        ).fetchone()[0]
    )


    require(
        wrong_walid == 0,

        "Old Walid Secretary General "
        "assignment still exists.",
    )


    # ========================================================
    # OLD WRONG KARIM VP ASSIGNMENT REMOVED
    # ========================================================

    wrong_karim = (
        conn.execute(
            """
            SELECT
                COUNT(*)

            FROM memberships


            JOIN people

                ON memberships.person_id =
                   people.person_id


            JOIN roles

                ON memberships.role_id =
                   roles.role_id


            WHERE memberships.term_id = ?

              AND LOWER(
                  people.first_name
              ) = 'karim'

              AND LOWER(
                  people.last_name
              ) = 'tamda'

              AND roles.name =
                  'VICE_PRESIDENT'
            """,
            (
                active[
                    "term_id"
                ],
            ),
        ).fetchone()[0]
    )


    require(
        wrong_karim == 0,

        "Old Karim Vice President "
        "assignment still exists.",
    )


    # ========================================================
    # PRESERVE EXISTING NON-EXECUTIVE MEMBERS
    #
    # Task 4 must not blindly delete people whose real status
    # has not been contradicted by the authoritative board.
    # ========================================================

    for (
        first_name,
        last_name,
    ) in (

        (
            "Anis",
            "KAOUANE",
        ),

        (
            "asma",
            "benaoudia",
        ),

        (
            "serine",
            "mekdad",
        ),

        (
            "fadoua",
            "slimani",
        ),

        (
            "merazga",
            "safouane",
        ),

        (
            "chouayb",
            "mokrani",
        ),

    ):

        count = (
            conn.execute(
                """
                SELECT
                    COUNT(*)

                FROM memberships


                JOIN people

                    ON memberships.person_id =
                       people.person_id


                WHERE memberships.term_id = ?

                  AND LOWER(
                      people.first_name
                  ) = LOWER(?)

                  AND LOWER(
                      people.last_name
                  ) = LOWER(?)
                """,
                (
                    active[
                        "term_id"
                    ],

                    first_name,

                    last_name,
                ),
            ).fetchone()[0]
        )


        require(
            count == 1,

            "Existing non-executive "
            "membership was unexpectedly "
            "removed: "
            f"{first_name} "
            f"{last_name}",
        )


    # ========================================================
    # DRAFT 2026/2027 MUST BE UNTOUCHED
    # ========================================================

    draft_memberships_after = (
        conn.execute(
            """
            SELECT
                membership_id,
                person_id,
                role_id,
                department_id

            FROM memberships

            WHERE term_id = ?

            ORDER BY
                membership_id
            """,
            (
                draft[
                    "term_id"
                ],
            ),
        ).fetchall()
    )


    draft_snapshot_after = [

        tuple(
            row
        )

        for row
        in draft_memberships_after

    ]


    require(
        draft_snapshot_after
        == draft_snapshot_before,

        "2026/2027 DRAFT "
        "memberships were modified "
        "by Task 4.",
    )


    # ========================================================
    # KNOWN TEST ACCOUNTS
    # ========================================================

    for username in (

        "yacine_alumni",

        "belhadj_sarah2",

        "belhadj_sarah3",

        "smith_anais",

    ):

        row = (
            conn.execute(
                """
                SELECT
                    user_id,
                    is_active

                FROM users

                WHERE LOWER(username) =
                      LOWER(?)
                """,
                (
                    username,
                ),
            ).fetchone()
        )


        if row is not None:

            require(
                row[
                    "is_active"
                ] == 0,

                "Known test account "
                "is still active: "
                f"{username}",
            )


    # ========================================================
    # DATABASE HEALTH
    # ========================================================

    integrity = (
        conn.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]
    )


    foreign_keys = (
        conn.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()
    )


    require(
        integrity == "ok",
        "Integrity check failed.",
    )


    require(
        not foreign_keys,
        "Foreign key check failed.",
    )


    conn.close()


    # ========================================================
    # IDEMPOTENCY
    #
    # Running the reconstruction twice must not:
    # - duplicate people
    # - duplicate memberships
    # - break database
    # ========================================================

    reconstruct_database(

        db_path=TEST_DB,

        create_backup_file=False,

        verbose=False,

    )


    conn = connect(
        TEST_DB
    )


    integrity_second = (
        conn.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]
    )


    foreign_keys_second = (
        conn.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()
    )


    conn.close()


    require(
        integrity_second == "ok",

        "Second-run integrity "
        "check failed.",
    )


    require(
        not foreign_keys_second,

        "Second-run foreign key "
        "check failed.",
    )


    # ========================================================
    # SUCCESS
    # ========================================================

    print(
        "========================================"
    )

    print(
        "2025/2026 RECONSTRUCTION TEST SUCCESSFUL"
    )

    print(
        "========================================"
    )


    print(
        "Real executive board reconstructed: OK"
    )

    print(
        "Nour el Houda AMELLAL "
        "as Vice President: OK"
    )

    print(
        "Farah DJERMOUNE "
        "as Secretary General: OK"
    )

    print(
        "Karim TAMDA as "
        "Communication & Marketing Head: OK"
    )

    print(
        "Abd el Ouadoud BENANTAR as "
        "Communication & Marketing Head: OK"
    )

    print(
        "Wrong executive assignments removed: OK"
    )

    print(
        "ALUMNI removed from active roster: OK"
    )

    print(
        "Existing ordinary memberships preserved: OK"
    )

    print(
        "Known test accounts deactivated safely: OK"
    )

    print(
        "2026/2027 DRAFT untouched: OK"
    )

    print(
        "Idempotency: OK"
    )

    print(
        "Integrity check:",
        integrity_second,
    )

    print(
        "Foreign key check:",
        foreign_keys_second,
    )


finally:

    if TEST_DB.exists():

        TEST_DB.unlink()

        print(
            "Temporary database deleted."
        )