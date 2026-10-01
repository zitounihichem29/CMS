import sqlite3
from pathlib import Path


DATABASE_DIR = (
    Path(__file__).resolve().parent
)

DATABASE_PATH = (
    DATABASE_DIR
    / "rsclub.db"
)


OLD_TERM_NAME = (
    "2025/2026"
)

NEW_TERM_NAME = (
    "2026/2027"
)


def connect():

    conn = sqlite3.connect(
        DATABASE_PATH,
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
    failures,
):

    if not condition:

        failures.append(
            message
        )


conn = connect()

cursor = conn.cursor()

failures = []


# ============================================================
# TERMS
# ============================================================

old_term = cursor.execute(
    """
    SELECT
        term_id,
        name,
        status,
        start_date,
        end_date

    FROM terms

    WHERE name = ?

    LIMIT 1
    """,
    (
        OLD_TERM_NAME,
    ),
).fetchone()


new_term = cursor.execute(
    """
    SELECT
        term_id,
        name,
        status,
        start_date,
        end_date

    FROM terms

    WHERE name = ?

    LIMIT 1
    """,
    (
        NEW_TERM_NAME,
    ),
).fetchone()


require(
    old_term is not None,
    "2025/2026 mandate missing.",
    failures,
)


require(
    new_term is not None,
    "2026/2027 mandate missing.",
    failures,
)


if old_term:

    require(
        old_term[
            "status"
        ]
        == "ARCHIVED",

        (
            "2025/2026 is not ARCHIVED."
        ),

        failures,
    )


if new_term:

    require(
        new_term[
            "status"
        ]
        == "ACTIVE",

        (
            "2026/2027 is not ACTIVE."
        ),

        failures,
    )


# ============================================================
# SINGLE ACTIVE
# ============================================================

active_terms = cursor.execute(
    """
    SELECT
        term_id,
        name

    FROM terms

    WHERE status = 'ACTIVE'
    """
).fetchall()


require(
    len(
        active_terms
    )
    == 1,

    (
        "Exactly one ACTIVE "
        "mandate must exist."
    ),

    failures,
)


if active_terms:

    require(
        active_terms[0][
            "name"
        ]
        == NEW_TERM_NAME,

        (
            "Current ACTIVE mandate "
            "is not 2026/2027."
        ),

        failures,
    )


# ============================================================
# NEW BOARD
# ============================================================

board = []


if new_term:

    board = cursor.execute(
        """
        SELECT
            memberships.membership_id,
            memberships.department_id,

            people.first_name,
            people.last_name,

            roles.name
                AS role_name,

            departments.name
                AS department_name,

            users.username,
            users.is_active

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

        LEFT JOIN users

            ON users.person_id =
               memberships.person_id

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

                WHEN 'MEMBER'
                    THEN 6

                ELSE 7

            END,

            departments.department_id,

            people.first_name,

            people.last_name
        """,
        (
            new_term[
                "term_id"
            ],
        ),
    ).fetchall()


require(
    len(
        board
    )
    > 0,

    (
        "2026/2027 has no memberships."
    ),

    failures,
)


# ============================================================
# REQUIRED LEADERSHIP
# ============================================================

if new_term:

    leadership = cursor.execute(
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
                AS vice_count,


            SUM(
                CASE
                    WHEN roles.name =
                         'SECRETARY_GENERAL'
                    THEN 1
                    ELSE 0
                END
            )
                AS sg_count,


            SUM(
                CASE
                    WHEN roles.name =
                         'HEAD'

                     AND

                         memberships.department_id = 1

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
            new_term[
                "term_id"
            ],
        ),
    ).fetchone()


    require(
        leadership[
            "president_count"
        ]
        == 1,

        (
            "President count is not 1."
        ),

        failures,
    )


    require(
        leadership[
            "vice_count"
        ]
        == 1,

        (
            "Vice President count "
            "is not 1."
        ),

        failures,
    )


    require(
        leadership[
            "sg_count"
        ]
        == 1,

        (
            "Secretary General count "
            "is not 1."
        ),

        failures,
    )


    require(
        leadership[
            "hr_head_count"
        ]
        == 1,

        (
            "HR Head count is not 1."
        ),

        failures,
    )


# ============================================================
# REQUIRED ACCOUNTS
# ============================================================

if new_term:

    required_accounts = (
        cursor.execute(
            """
            SELECT
                people.first_name,
                people.last_name,

                roles.name
                    AS role_name,

                memberships.department_id,

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
                        roles.name =
                            'HEAD'

                        AND

                        memberships.department_id =
                            1
                    )
              )
            """,
            (
                new_term[
                    "term_id"
                ],
            ),
        ).fetchall()
    )


    require(
        len(
            required_accounts
        )
        == 4,

        (
            "Required leadership "
            "account count is not 4."
        ),

        failures,
    )


    for row in (
        required_accounts
    ):

        name = (
            (
                row[
                    "first_name"
                ]
                or ""
            )
            +
            " "
            +
            (
                row[
                    "last_name"
                ]
                or ""
            )
        ).strip()


        require(
            bool(
                row[
                    "user_id"
                ]
                and
                row[
                    "is_active"
                ]
            ),

            (
                f"{name} "
                f"({row['role_name']}) "
                "does not have an active "
                "CMS account."
            ),

            failures,
        )


# ============================================================
# NO ACTIVE ALUMNI ROLE
# ============================================================

if new_term:

    active_alumni = (
        cursor.execute(
            """
            SELECT COUNT(*)

            FROM memberships

            JOIN roles

                ON roles.role_id =
                   memberships.role_id

            WHERE
                memberships.term_id = ?

              AND roles.name =
                  'ALUMNI'
            """,
            (
                new_term[
                    "term_id"
                ],
            ),
        ).fetchone()[0]
    )


    require(
        active_alumni == 0,

        (
            "2026/2027 contains "
            "legacy ALUMNI memberships."
        ),

        failures,
    )


# ============================================================
# ELECTION + APPROVAL HISTORY
# ============================================================

if new_term:

    election = (
        cursor.execute(
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
                new_term[
                    "term_id"
                ],
            ),
        ).fetchone()
    )


    require(
        election
        is not None,

        (
            "Election record missing."
        ),

        failures,
    )


    if election:

        require(
            bool(
                election[
                    "report_path"
                ]
            ),

            (
                "Election PV path missing."
            ),

            failures,
        )


    approvals = {

        row[
            "approval_type"
        ]

        for row in cursor.execute(
            """
            SELECT
                approval_type

            FROM mandate_approvals

            WHERE term_id = ?
            """,
            (
                new_term[
                    "term_id"
                ],
            ),
        ).fetchall()

    }


    require(
        "PRESIDENT"
        in approvals,

        (
            "President approval history "
            "missing."
        ),

        failures,
    )


    require(
        "VICE_PRESIDENT"
        in approvals,

        (
            "Vice President approval "
            "history missing."
        ),

        failures,
    )


# ============================================================
# ACTIVATION AUDIT
# ============================================================

activation_log = None


if new_term:

    activation_log = (
        cursor.execute(
            """
            SELECT
                mandate_audit_log.log_id,
                mandate_audit_log.action,
                mandate_audit_log.actor_user_id,
                mandate_audit_log.created_at,

                users.username

            FROM mandate_audit_log

            LEFT JOIN users

                ON users.user_id =
                   mandate_audit_log.actor_user_id

            WHERE
                mandate_audit_log.term_id = ?

              AND mandate_audit_log.action =
                  'MANDATE_ACTIVATED'

            ORDER BY
                mandate_audit_log.log_id DESC

            LIMIT 1
            """,
            (
                new_term[
                    "term_id"
                ],
            ),
        ).fetchone()
    )


    require(
        activation_log
        is not None,

        (
            "MANDATE_ACTIVATED audit "
            "entry missing."
        ),

        failures,
    )


# ============================================================
# HISTORICAL IMMUTABILITY
# ============================================================

triggers = {

    row[
        "name"
    ]

    for row in cursor.execute(
        """
        SELECT name

        FROM sqlite_master

        WHERE type = 'trigger'
        """
    ).fetchall()

}


for trigger_name in {

    "trg_archived_terms_no_update",

    "trg_archived_terms_no_delete",

}:

    require(
        trigger_name
        in triggers,

        (
            "Missing historical "
            "protection trigger: "
            f"{trigger_name}"
        ),

        failures,
    )


# ============================================================
# DATABASE HEALTH
# ============================================================

integrity = (
    cursor.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]
)


foreign_keys = (
    cursor.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()
)


require(
    integrity == "ok",

    (
        "Database integrity "
        f"failed: {integrity}"
    ),

    failures,
)


require(
    not foreign_keys,

    (
        "Foreign key violations exist."
    ),

    failures,
)


# ============================================================
# OUTPUT
# ============================================================

print(
    "========================================"
)

print(
    "2026/2027 REAL ACTIVATION VERIFICATION"
)

print(
    "========================================"
)

print()


if old_term:

    print(
        "Previous mandate:",
        old_term[
            "name"
        ],
        "-",
        old_term[
            "status"
        ],
    )


if new_term:

    print(
        "Current mandate:",
        new_term[
            "name"
        ],
        "-",
        new_term[
            "status"
        ],
    )


print()

print(
    "CURRENT 2026/2027 BOARD"
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
        "|",
        (
            row[
                "username"
            ]
            or
            "No CMS account"
        ),
    )


print()

print(
    "Integrity check:",
    integrity,
)

print(
    "Foreign key check:",
    foreign_keys,
)


if activation_log:

    print(
        "Activation recorded by:",
        (
            activation_log[
                "username"
            ]
            or
            (
                "user_id="
                +
                str(
                    activation_log[
                        "actor_user_id"
                    ]
                )
            )
        ),
    )


print()


if failures:

    print(
        "VERIFICATION FAILURES"
    )

    print(
        "----------------------------------------"
    )


    for failure in failures:

        print(
            "-",
            failure,
        )


    print()

    print(
        "========================================"
    )

    print(
        "REAL ACTIVATION VERIFICATION FAILED"
    )

    print(
        "========================================"
    )


    conn.close()


    raise SystemExit(
        1
    )


print(
    "========================================"
)

print(
    "2026/2027 REAL ACTIVATION VERIFIED"
)

print(
    "========================================"
)


print(
    "2025/2026 archived: OK"
)

print(
    "2026/2027 active: OK"
)

print(
    "Single ACTIVE mandate: OK"
)

print(
    "Board structure: OK"
)

print(
    "Required CMS accounts: OK"
)

print(
    "Election history: OK"
)

print(
    "Approval history: OK"
)

print(
    "Activation audit: OK"
)

print(
    "Historical protection: OK"
)

print(
    "Integrity check: ok"
)

print(
    "Foreign key check: []"
)


conn.close()