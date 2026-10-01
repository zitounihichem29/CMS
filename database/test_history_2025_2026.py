import json
import shutil
import sqlite3
from pathlib import Path

from reconstruct_history_2025_2026 import (
    CONFIRMED_ORGANIZATIONS,
    reconstruct_history,
)


DATABASE_DIR = (
    Path(__file__).resolve().parent
)

REAL_DB = (
    DATABASE_DIR
    / "rsclub.db"
)

TEST_DB = (
    DATABASE_DIR
    / "history_2025_2026_test.db"
)

TEST_PENDING = (
    DATABASE_DIR
    / "history_2025_2026_pending_test.json"
)

TEST_REPORT = (
    DATABASE_DIR
    / "history_2025_2026_report_test.txt"
)


# ============================================================
# HELPERS
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


def require(
    condition,
    message,
):

    if not condition:

        raise RuntimeError(
            message
        )


def row_exists(
    conn,
    sql,
    params=(),
):

    return (
        conn.execute(
            sql,
            params,
        ).fetchone()
        is not None
    )


# ============================================================
# CLEAN OLD TEST FILES
# ============================================================

for path in (

    TEST_DB,

    TEST_PENDING,

    TEST_REPORT,

):

    if path.exists():

        path.unlink()


# ============================================================
# COPY REAL DB
# ============================================================

shutil.copy2(
    REAL_DB,
    TEST_DB,
)


try:

    before = connect(
        TEST_DB
    )


    # ========================================================
    # TERMS
    # ========================================================

    active_before = (
        before.execute(
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

        active_before is not None

        and

        active_before[
            "status"
        ] == "ACTIVE",

        "2025/2026 ACTIVE missing.",

    )


    require(

        draft_before is not None

        and

        draft_before[
            "status"
        ] == "DRAFT",

        "2026/2027 DRAFT missing.",

    )


    # ========================================================
    # DRAFT MEMBERSHIP SNAPSHOT
    # ========================================================

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


    # ========================================================
    # PLAUSIBLE RECORDS
    #
    # They must NOT be deleted simply because
    # their exact historical status is not yet confirmed.
    # ========================================================

    preserved_before = {

        "python_training":

            row_exists(
                before,

                """
                SELECT 1

                FROM trainings

                WHERE LOWER(
                    TRIM(title)
                ) = 'python'

                LIMIT 1
                """,
            ),


        "netcom_project":

            row_exists(
                before,

                """
                SELECT 1

                FROM projects

                WHERE LOWER(
                    TRIM(name)
                ) = 'netcom project'

                LIMIT 1
                """,
            ),


        "cutting_stock":

            row_exists(
                before,

                """
                SELECT 1

                FROM scientific_articles

                WHERE LOWER(
                    TRIM(title)
                ) = 'cutting stock problem'

                LIMIT 1
                """,
            ),


        "optimisation_combinatoire":

            row_exists(
                before,

                """
                SELECT 1

                FROM scientific_articles

                WHERE LOWER(
                    TRIM(title)
                ) = 'optimisation combinatoire'

                LIMIT 1
                """,
            ),

    }


    before.close()


    # ========================================================
    # RUN TASK 8 ON TEMP DB
    # ========================================================

    reconstruct_history(

        db_path=TEST_DB,

        create_backup_file=False,

        pending_path=TEST_PENDING,

        report_path=TEST_REPORT,

        verbose=False,

    )


    conn = connect(
        TEST_DB
    )


    # ========================================================
    # TERM STATUS
    # ========================================================

    active_after = (
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


    draft_after = (
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

        active_after[
            "status"
        ] == "ACTIVE",

        "2025/2026 status changed.",

    )


    require(

        draft_after[
            "status"
        ] == "DRAFT",

        "2026/2027 status changed.",

    )


    # ========================================================
    # DRAFT MEMBERSHIPS UNCHANGED
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
                draft_after[
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
        ==
        draft_snapshot_before,

        "2026/2027 DRAFT "
        "memberships changed.",

    )


    # ========================================================
    # FAKE TRAINING REMOVED
    # ========================================================

    for title in (
        "jhgf",
    ):

        count = (

            conn.execute(
                """
                SELECT
                    COUNT(*)

                FROM trainings

                WHERE LOWER(
                    TRIM(title)
                ) = LOWER(?)
                """,
                (
                    title,
                ),
            ).fetchone()[0]

        )


        require(

            count == 0,

            "Fake training still exists: "
            f"{title}",

        )


    # ========================================================
    # FAKE PROJECTS REMOVED
    # ========================================================

    for name in (
        "kkf",
        ";hekawjh",
    ):

        count = (

            conn.execute(
                """
                SELECT
                    COUNT(*)

                FROM projects

                WHERE LOWER(
                    TRIM(name)
                ) = LOWER(?)
                """,
                (
                    name,
                ),
            ).fetchone()[0]

        )


        require(

            count == 0,

            "Fake project still exists: "
            f"{name}",

        )


    # ========================================================
    # FAKE ARTICLES REMOVED
    # ========================================================

    for title in (

        "PDF Article Test",

        "hgfkfm",

        "kejfhkjwfhlgf",

    ):

        count = (

            conn.execute(
                """
                SELECT
                    COUNT(*)

                FROM scientific_articles

                WHERE LOWER(
                    TRIM(title)
                ) = LOWER(?)
                """,
                (
                    title,
                ),
            ).fetchone()[0]

        )


        require(

            count == 0,

            "Fake article still exists: "
            f"{title}",

        )


    # ========================================================
    # PLAUSIBLE DATA PRESERVED
    # ========================================================

    if preserved_before[
        "python_training"
    ]:

        require(

            row_exists(
                conn,

                """
                SELECT 1

                FROM trainings

                WHERE LOWER(
                    TRIM(title)
                ) = 'python'

                LIMIT 1
                """,
            ),

            "Plausible Python "
            "training was removed.",

        )


    if preserved_before[
        "netcom_project"
    ]:

        require(

            row_exists(
                conn,

                """
                SELECT 1

                FROM projects

                WHERE LOWER(
                    TRIM(name)
                ) = 'netcom project'

                LIMIT 1
                """,
            ),

            "Netcom project was removed.",

        )


    if preserved_before[
        "cutting_stock"
    ]:

        require(

            row_exists(
                conn,

                """
                SELECT 1

                FROM scientific_articles

                WHERE LOWER(
                    TRIM(title)
                ) = 'cutting stock problem'

                LIMIT 1
                """,
            ),

            "Cutting Stock article "
            "was removed.",

        )


    if preserved_before[
        "optimisation_combinatoire"
    ]:

        require(

            row_exists(
                conn,

                """
                SELECT 1

                FROM scientific_articles

                WHERE LOWER(
                    TRIM(title)
                ) =
                    'optimisation combinatoire'

                LIMIT 1
                """,
            ),

            "Optimisation combinatoire "
            "article was removed.",

        )


    # ========================================================
    # ORGANIZATIONS
    # ========================================================

    for item in (
        CONFIRMED_ORGANIZATIONS
    ):

        row = (
            conn.execute(
                """
                SELECT
                    organizations.organization_id,

                    organization_relations.organization_relation_id

                FROM organizations


                JOIN organization_relations

                    ON organizations.organization_id =
                       organization_relations.organization_id


                WHERE LOWER(
                    organizations.name
                ) = LOWER(?)

                  AND organization_relations.term_id = ?

                LIMIT 1
                """,
                (
                    item[
                        "name"
                    ],

                    active_after[
                        "term_id"
                    ],
                ),
            ).fetchone()
        )


        require(

            row is not None,

            "Missing 2025/2026 "
            "organization relation: "
            f"{item['name']}",

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
    # PENDING FILE
    # ========================================================

    require(
        TEST_PENDING.exists(),

        "Pending history JSON "
        "was not created.",
    )


    require(
        TEST_REPORT.exists(),

        "History report was "
        "not created.",
    )


    pending = json.loads(
        TEST_PENDING.read_text(
            encoding="utf-8"
        )
    )


    require(

        pending[
            "term"
        ] == "2025/2026",

        "Pending history "
        "term is wrong.",

    )


    require(

        len(
            pending[
                "events"
            ]
        )
        >= 6,

        "Pending event "
        "history is incomplete.",

    )


    require(

        len(
            pending[
                "trainings"
            ]
        )
        >= 5,

        "Pending training "
        "history is incomplete.",

    )


    require(

        len(
            pending[
                "projects"
            ]
        )
        >= 6,

        "Pending project "
        "history is incomplete.",

    )


    # ========================================================
    # IDEMPOTENCY
    # ========================================================

    reconstruct_history(

        db_path=TEST_DB,

        create_backup_file=False,

        pending_path=TEST_PENDING,

        report_path=TEST_REPORT,

        verbose=False,

    )


    conn = connect(
        TEST_DB
    )


    duplicate_relations = (
        conn.execute(
            """
            SELECT
                organization_id,
                term_id,
                COUNT(*) AS total

            FROM organization_relations

            WHERE term_id = ?

            GROUP BY
                organization_id,
                term_id

            HAVING
                COUNT(*) > 1
            """,
            (
                active_after[
                    "term_id"
                ],
            ),
        ).fetchall()
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

        not duplicate_relations,

        "Second run created duplicate "
        "organization relations.",

    )


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
        "2025/2026 HISTORY TEST SUCCESSFUL"
    )

    print(
        "========================================"
    )


    print(
        "Obvious fake history cleaned: OK"
    )

    print(
        "Plausible/real records preserved: OK"
    )

    print(
        "Confirmed organization history linked: OK"
    )

    print(
        "Incomplete facts preserved without fabrication: OK"
    )

    print(
        "2026/2027 DRAFT memberships untouched: OK"
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

    for path in (

        TEST_DB,

        TEST_PENDING,

        TEST_REPORT,

    ):

        if path.exists():

            path.unlink()


    print(
        "Temporary Task 8 files deleted."
    )