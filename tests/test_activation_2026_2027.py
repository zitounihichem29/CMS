import shutil
import sqlite3
from pathlib import Path

import database

from app import app


BACKEND_DIR = (
    Path(__file__).resolve().parent
)

DATABASE_DIR = (
    BACKEND_DIR.parent
    / "database"
)

REAL_DB = (
    DATABASE_DIR
    / "rsclub.db"
)

TEST_DB = (
    DATABASE_DIR
    / "activation_2026_2027_test.db"
)


CURRENT_TERM_NAME = (
    "2025/2026"
)

TARGET_TERM_NAME = (
    "2026/2027"
)


def require(
    condition,
    message,
):

    if not condition:

        raise RuntimeError(
            message
        )


def login(
    client,
    user_id,
):

    with client.session_transaction() as session:

        session[
            "user_id"
        ] = user_id


def redirect_ok(
    response,
):

    return (
        response.status_code
        in {
            301,
            302,
            303,
            307,
            308,
        }
    )


# ============================================================
# TEMP DATABASE
# ============================================================

if TEST_DB.exists():

    TEST_DB.unlink()


shutil.copy2(
    REAL_DB,
    TEST_DB,
)


database.DATABASE_PATH = (
    TEST_DB
)


try:

    conn = (
        database.get_db_connection()
    )


    # ========================================================
    # TERMS
    # ========================================================

    current_term = (
        conn.execute(
            """
            SELECT
                term_id,
                name,
                status

            FROM terms

            WHERE name = ?

            LIMIT 1
            """,
            (
                CURRENT_TERM_NAME,
            ),
        ).fetchone()
    )


    target_term = (
        conn.execute(
            """
            SELECT
                term_id,
                name,
                status

            FROM terms

            WHERE name = ?

            LIMIT 1
            """,
            (
                TARGET_TERM_NAME,
            ),
        ).fetchone()
    )


    require(
        current_term
        is not None,

        (
            "2025/2026 mandate "
            "is missing."
        ),
    )


    require(
        target_term
        is not None,

        (
            "2026/2027 mandate "
            "is missing."
        ),
    )


    require(
        current_term[
            "status"
        ]
        == "ACTIVE",

        (
            "2025/2026 is not "
            "ACTIVE before test."
        ),
    )


    require(
        target_term[
            "status"
        ]
        == "DRAFT",

        (
            "2026/2027 is not "
            "DRAFT before test."
        ),
    )


    # ========================================================
    # REQUIRED ELECTION
    # ========================================================

    election = (
        conn.execute(
            """
            SELECT
                election_id,
                election_date,
                report_path

            FROM mandate_elections

            WHERE term_id = ?

            LIMIT 1
            """,
            (
                target_term[
                    "term_id"
                ],
            ),
        ).fetchone()
    )


    require(
        election
        is not None,

        (
            "2026/2027 election "
            "has not been recorded."
        ),
    )


    # ========================================================
    # REQUIRED APPROVALS
    # ========================================================

    approvals = {

        row[
            "approval_type"
        ]

        for row in conn.execute(
            """
            SELECT
                approval_type

            FROM mandate_approvals

            WHERE term_id = ?
            """,
            (
                target_term[
                    "term_id"
                ],
            ),
        ).fetchall()

    }


    require(
        "PRESIDENT"
        in approvals,

        (
            "Outgoing President "
            "approval missing."
        ),
    )


    require(
        "VICE_PRESIDENT"
        in approvals,

        (
            "Outgoing Vice President "
            "approval missing."
        ),
    )


    # ========================================================
    # REQUIRED BOARD
    # ========================================================

    required_board = (
        conn.execute(
            """
            SELECT

                SUM(
                    CASE
                        WHEN roles.name =
                             'PRESIDENT'
                        THEN 1
                        ELSE 0
                    END
                )
                    AS president_count,


                SUM(
                    CASE
                        WHEN roles.name =
                             'VICE_PRESIDENT'
                        THEN 1
                        ELSE 0
                    END
                )
                    AS vice_president_count,


                SUM(
                    CASE
                        WHEN roles.name =
                             'SECRETARY_GENERAL'
                        THEN 1
                        ELSE 0
                    END
                )
                    AS secretary_general_count,


                SUM(
                    CASE
                        WHEN roles.name =
                             'HEAD'

                         AND
                             memberships.department_id =
                             1

                        THEN 1
                        ELSE 0
                    END
                )
                    AS hr_head_count

            FROM memberships

            JOIN roles

                ON roles.role_id =
                   memberships.role_id

            WHERE
                memberships.term_id = ?
            """,
            (
                target_term[
                    "term_id"
                ],
            ),
        ).fetchone()
    )


    require(
        required_board[
            "president_count"
        ]
        == 1,

        (
            "2026/2027 requires "
            "exactly one President."
        ),
    )


    require(
        required_board[
            "vice_president_count"
        ]
        == 1,

        (
            "2026/2027 requires "
            "exactly one Vice President."
        ),
    )


    require(
        required_board[
            "secretary_general_count"
        ]
        == 1,

        (
            "2026/2027 requires "
            "exactly one Secretary General."
        ),
    )


    require(
        required_board[
            "hr_head_count"
        ]
        == 1,

        (
            "2026/2027 requires "
            "exactly one HR Head."
        ),
    )


    # ========================================================
    # OUTGOING PRESIDENT
    # ========================================================

    outgoing_president = (
        conn.execute(
            """
            SELECT
                users.user_id,
                users.username,

                people.first_name,
                people.last_name

            FROM memberships

            JOIN roles

                ON roles.role_id =
                   memberships.role_id

            JOIN people

                ON people.person_id =
                   memberships.person_id

            JOIN users

                ON users.person_id =
                   people.person_id

            WHERE
                memberships.term_id = ?

              AND roles.name =
                  'PRESIDENT'

              AND users.is_active = 1

            LIMIT 1
            """,
            (
                current_term[
                    "term_id"
                ],
            ),
        ).fetchone()
    )


    require(
        outgoing_president
        is not None,

        (
            "Outgoing President "
            "does not have an active "
            "CMS account."
        ),
    )


    print(
        "Outgoing President:",
        outgoing_president[
            "username"
        ],
    )


    print(
        "Current mandate:",
        current_term[
            "name"
        ],
    )


    print(
        "Target mandate:",
        target_term[
            "name"
        ],
    )


    conn.close()


    # ========================================================
    # ACTIVATE WITH THE REAL FLASK ROUTE
    # TEMP DATABASE ONLY
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            outgoing_president[
                "user_id"
            ],
        )


        response = client.post(
            (
                "/mandates/"
                f"{target_term['term_id']}"
                "/activate"
            ),

            follow_redirects=False,
        )


        if not redirect_ok(
            response
        ):

            print()

            print(
                "Activation response:"
            )

            print(
                response.status_code
            )

            print(
                response.get_data(
                    as_text=True
                )
            )


        require(
            redirect_ok(
                response
            ),

            (
                "Real Flask activation "
                "route rejected the "
                "2026/2027 mandate."
            ),
        )


    # ========================================================
    # VERIFY TRANSITION
    # ========================================================

    conn = (
        database.get_db_connection()
    )


    old_status = (
        conn.execute(
            """
            SELECT status

            FROM terms

            WHERE term_id = ?
            """,
            (
                current_term[
                    "term_id"
                ],
            ),
        ).fetchone()[0]
    )


    new_status = (
        conn.execute(
            """
            SELECT status

            FROM terms

            WHERE term_id = ?
            """,
            (
                target_term[
                    "term_id"
                ],
            ),
        ).fetchone()[0]
    )


    require(
        old_status
        == "ARCHIVED",

        (
            "2025/2026 was not "
            "archived."
        ),
    )


    require(
        new_status
        == "ACTIVE",

        (
            "2026/2027 was not "
            "activated."
        ),
    )


    active_count = (
        conn.execute(
            """
            SELECT COUNT(*)

            FROM terms

            WHERE status = 'ACTIVE'
            """
        ).fetchone()[0]
    )


    require(
        active_count == 1,

        (
            "There is not exactly "
            "one ACTIVE mandate "
            "after activation."
        ),
    )


    current_active = (
        conn.execute(
            """
            SELECT
                term_id,
                name

            FROM terms

            WHERE status = 'ACTIVE'

            LIMIT 1
            """
        ).fetchone()
    )


    require(
        current_active[
            "name"
        ]
        == TARGET_TERM_NAME,

        (
            "The application current "
            "mandate is not 2026/2027."
        ),
    )


    # ========================================================
    # AUDIT
    # ========================================================

    activation_log = (
        conn.execute(
            """
            SELECT
                action,
                actor_user_id,
                created_at

            FROM mandate_audit_log

            WHERE
                term_id = ?

              AND action =
                  'MANDATE_ACTIVATED'

            ORDER BY
                log_id DESC

            LIMIT 1
            """,
            (
                target_term[
                    "term_id"
                ],
            ),
        ).fetchone()
    )


    require(
        activation_log
        is not None,

        (
            "MANDATE_ACTIVATED "
            "audit entry missing."
        ),
    )


    # ========================================================
    # INCOMING REQUIRED ACCOUNTS
    # ========================================================

    incoming_required = (
        conn.execute(
            """
            SELECT
                roles.name
                    AS role_name,

                memberships.department_id,

                people.first_name,
                people.last_name,

                users.user_id,
                users.username,
                users.is_active

            FROM memberships

            JOIN roles

                ON roles.role_id =
                   memberships.role_id

            JOIN people

                ON people.person_id =
                   memberships.person_id

            LEFT JOIN users

                ON users.person_id =
                   people.person_id

            WHERE
                memberships.term_id = ?

              AND (

                    roles.name IN (
                        'PRESIDENT',
                        'VICE_PRESIDENT',
                        'SECRETARY_GENERAL'
                    )

                    OR

                    (
                        roles.name = 'HEAD'

                        AND

                        memberships.department_id = 1
                    )
              )
            """,
            (
                target_term[
                    "term_id"
                ],
            ),
        ).fetchall()
    )


    require(
        len(
            incoming_required
        )
        == 4,

        (
            "Required incoming "
            "leadership count is not 4."
        ),
    )


    for row in incoming_required:

        require(
            row[
                "user_id"
            ]
            and row[
                "is_active"
            ],

            (
                "Incoming leadership "
                "contains an account "
                "that is not active."
            ),
        )


    # ========================================================
    # OLD MANDATE IS REALLY IMMUTABLE
    # ========================================================

    archive_lock_ok = False


    try:

        conn.execute(
            """
            UPDATE terms

            SET name = name

            WHERE term_id = ?
            """,
            (
                current_term[
                    "term_id"
                ],
            ),
        )


    except sqlite3.IntegrityError:

        archive_lock_ok = True

        conn.rollback()


    require(
        archive_lock_ok,

        (
            "Archived 2025/2026 "
            "mandate was still editable."
        ),
    )


    # ========================================================
    # HEALTH
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

        (
            "Integrity check failed."
        ),
    )


    require(
        not foreign_keys,

        (
            "Foreign key check failed."
        ),
    )


    # ========================================================
    # PRINT NEW BOARD
    # ========================================================

    board = (
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

                ON people.person_id =
                   memberships.person_id

            JOIN roles

                ON roles.role_id =
                   memberships.role_id

            LEFT JOIN departments

                ON departments.department_id =
                   memberships.department_id

            WHERE
                memberships.term_id = ?

            ORDER BY

                CASE roles.name

                    WHEN 'PRESIDENT'
                        THEN 1

                    WHEN 'VICE_PRESIDENT'
                        THEN 2

                    WHEN 'SECRETARY_GENERAL'
                        THEN 3

                    WHEN 'HEAD'
                        THEN 4

                    WHEN 'SUB_HEAD'
                        THEN 5

                    ELSE 6

                END,

                departments.department_id,

                people.first_name
            """,
            (
                target_term[
                    "term_id"
                ],
            ),
        ).fetchall()
    )


    conn.close()


    print()

    print(
        "2026/2027 BOARD AFTER TEMP ACTIVATION"
    )

    print(
        "----------------------------------------"
    )


    for row in board:

        print(
            "-",
            row[
                "first_name"
            ],
            row[
                "last_name"
            ],
            "|",
            row[
                "role_name"
            ],
            "|",
            (
                row[
                    "department_name"
                ]
                or
                "Executive"
            ),
        )


    print()

    print(
        "========================================"
    )

    print(
        "2026/2027 ACTIVATION TEST SUCCESSFUL"
    )

    print(
        "========================================"
    )


    print(
        "2025/2026 archived: OK"
    )

    print(
        "2026/2027 activated: OK"
    )

    print(
        "Single ACTIVE mandate: OK"
    )

    print(
        "Required incoming accounts: OK"
    )

    print(
        "Activation audit: OK"
    )

    print(
        "Historical immutability: OK"
    )

    print(
        "Integrity check:",
        integrity,
    )

    print(
        "Foreign key check:",
        foreign_keys,
    )


finally:

    if TEST_DB.exists():

        TEST_DB.unlink()


    print(
        "Temporary activation database deleted."
    )