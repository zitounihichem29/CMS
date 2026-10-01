import argparse
import sqlite3
from pathlib import Path


DATABASE_DIR = (
    Path(__file__).resolve().parent
)

DATABASE_PATH = (
    DATABASE_DIR
    / "rsclub.db"
)

BACKUP_PATH = (
    DATABASE_DIR
    / "rsclub_backup_before_activation_2026_2027.db"
)


CURRENT_TERM_NAME = (
    "2025/2026"
)

TARGET_TERM_NAME = (
    "2026/2027"
)

HR_DEPARTMENT_ID = 1


EXECUTIVE_ROLES = {
    "PRESIDENT",
    "VICE_PRESIDENT",
    "SECRETARY_GENERAL",
}


DEPARTMENT_REQUIRED_ROLES = {
    "MEMBER",
    "SUB_HEAD",
    "HEAD",
}


# ============================================================
# CONNECTION
# ============================================================

def connect(
    path=DATABASE_PATH,
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
# BACKUP
# ============================================================

def create_backup(
    source_path,
    backup_path,
):

    source_path = Path(
        source_path
    )

    backup_path = Path(
        backup_path
    )


    if backup_path.exists():

        print()
        print(
            "Backup already exists:"
        )

        print(
            backup_path
        )

        print(
            "It will NOT be overwritten."
        )

        return backup_path


    source = connect(
        source_path
    )

    destination = (
        sqlite3.connect(
            backup_path
        )
    )


    try:

        source.backup(
            destination
        )


    finally:

        destination.close()
        source.close()


    return backup_path


# ============================================================
# HELPERS
# ============================================================

def get_term_by_name(
    cursor,
    name,
):

    return cursor.execute(
        """
        SELECT
            term_id,
            name,
            start_date,
            end_date,
            status

        FROM terms

        WHERE name = ?

        LIMIT 1
        """,
        (
            name,
        ),
    ).fetchone()


def full_name(
    row,
):

    if row is None:

        return "—"


    return (
        (
            row["first_name"]
            or ""
        ).strip()
        +
        " "
        +
        (
            row["last_name"]
            or ""
        ).strip()
    ).strip()


def get_board(
    cursor,
    term_id,
):

    return cursor.execute(
        """
        SELECT
            memberships.membership_id,
            memberships.person_id,
            memberships.department_id,

            people.first_name,
            people.last_name,

            roles.role_id,
            roles.name
                AS role_name,

            departments.name
                AS department_name,

            users.user_id,
            users.username,

            COALESCE(
                users.is_active,
                0
            )
                AS user_is_active,

            COALESCE(
                users.is_platform_admin,
                0
            )
                AS is_platform_admin

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
            term_id,
        ),
    ).fetchall()


def find_role(
    board,
    role_name,
):

    return [

        row

        for row
        in board

        if row[
            "role_name"
        ]
        == role_name

    ]


def find_hr_head(
    board,
):

    return [

        row

        for row
        in board

        if (
            row[
                "role_name"
            ]
            == "HEAD"

            and

            row[
                "department_id"
            ]
            == HR_DEPARTMENT_ID
        )

    ]


def account_ready(
    row,
):

    return bool(
        row
        and row[
            "user_id"
        ]
        and row[
            "user_is_active"
        ]
    )


# ============================================================
# PREFLIGHT
# ============================================================

def run_preflight(
    db_path=DATABASE_PATH,
    verbose=True,
):

    conn = connect(
        db_path
    )

    cursor = (
        conn.cursor()
    )


    blockers = []
    warnings = []


    # ========================================================
    # DATABASE HEALTH
    # ========================================================

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


    if integrity != "ok":

        blockers.append(
            (
                "Database integrity "
                f"check failed: {integrity}"
            )
        )


    if foreign_keys:

        blockers.append(
            (
                "Foreign key violations "
                "exist in the database."
            )
        )


    # ========================================================
    # CURRENT / TARGET TERMS
    # ========================================================

    current_term = (
        get_term_by_name(
            cursor,
            CURRENT_TERM_NAME,
        )
    )


    target_term = (
        get_term_by_name(
            cursor,
            TARGET_TERM_NAME,
        )
    )


    if current_term is None:

        blockers.append(
            (
                f"{CURRENT_TERM_NAME} "
                "does not exist."
            )
        )


    elif (
        current_term[
            "status"
        ]
        != "ACTIVE"
    ):

        blockers.append(
            (
                f"{CURRENT_TERM_NAME} "
                "must still be ACTIVE "
                "before activation."
            )
        )


    if target_term is None:

        blockers.append(
            (
                f"{TARGET_TERM_NAME} "
                "does not exist."
            )
        )


    elif (
        target_term[
            "status"
        ]
        != "DRAFT"
    ):

        blockers.append(
            (
                f"{TARGET_TERM_NAME} "
                "must be DRAFT before "
                "real activation."
            )
        )


    # ========================================================
    # GLOBAL ACTIVE / DRAFT UNIQUENESS
    # ========================================================

    active_terms = cursor.execute(
        """
        SELECT
            term_id,
            name

        FROM terms

        WHERE status = 'ACTIVE'
        """
    ).fetchall()


    draft_terms = cursor.execute(
        """
        SELECT
            term_id,
            name

        FROM terms

        WHERE status = 'DRAFT'
        """
    ).fetchall()


    if len(
        active_terms
    ) != 1:

        blockers.append(
            (
                "Exactly one ACTIVE "
                "mandate must exist."
            )
        )


    if len(
        draft_terms
    ) != 1:

        blockers.append(
            (
                "Exactly one DRAFT "
                "mandate must exist "
                "before this activation."
            )
        )


    if (
        current_term is None
        or target_term is None
    ):

        conn.close()


        return {
            "ready":
                False,

            "blockers":
                blockers,

            "warnings":
                warnings,

            "integrity":
                integrity,

            "foreign_keys":
                foreign_keys,

            "current_term":
                current_term,

            "target_term":
                target_term,

            "board":
                [],

            "approvals":
                [],
        }


    # ========================================================
    # BASIC DATE VALIDATION
    # ========================================================

    if (
        not target_term[
            "start_date"
        ]
        or
        not target_term[
            "end_date"
        ]
    ):

        blockers.append(
            (
                "2026/2027 start and "
                "end dates are required."
            )
        )


    elif (
        target_term[
            "end_date"
        ]
        <=
        target_term[
            "start_date"
        ]
    ):

        blockers.append(
            (
                "2026/2027 end date "
                "must be after start date."
            )
        )


    # ========================================================
    # ELECTION
    # ========================================================

    election = cursor.execute(
        """
        SELECT
            election_id,
            election_date,
            report_path,
            notes,
            recorded_by_user_id,
            recorded_at,
            updated_by_user_id,
            updated_at

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


    if election is None:

        blockers.append(
            (
                "The official 2026/2027 "
                "election result has not "
                "been recorded."
            )
        )


    else:

        if not election[
            "election_date"
        ]:

            blockers.append(
                (
                    "The election date "
                    "is missing."
                )
            )


        if not election[
            "report_path"
        ]:

            blockers.append(
                (
                    "The official election "
                    "PV/report has not "
                    "been uploaded."
                )
            )


    # ========================================================
    # BOARD
    # ========================================================

    board = get_board(
        cursor,
        target_term[
            "term_id"
        ],
    )


    if not board:

        blockers.append(
            (
                "The 2026/2027 Board "
                "is empty."
            )
        )


    presidents = (
        find_role(
            board,
            "PRESIDENT",
        )
    )


    vice_presidents = (
        find_role(
            board,
            "VICE_PRESIDENT",
        )
    )


    secretary_generals = (
        find_role(
            board,
            "SECRETARY_GENERAL",
        )
    )


    hr_heads = (
        find_hr_head(
            board
        )
    )


    if len(
        presidents
    ) != 1:

        blockers.append(
            (
                "2026/2027 must contain "
                "exactly one President."
            )
        )


    if len(
        vice_presidents
    ) != 1:

        blockers.append(
            (
                "2026/2027 must contain "
                "exactly one Vice President."
            )
        )


    if len(
        secretary_generals
    ) != 1:

        blockers.append(
            (
                "2026/2027 must contain "
                "exactly one Secretary General."
            )
        )


    if len(
        hr_heads
    ) != 1:

        blockers.append(
            (
                "2026/2027 must contain "
                "exactly one Human Resources Head."
            )
        )


    # ========================================================
    # NO LEGACY ALUMNI ROLE
    # ========================================================

    alumni_memberships = [

        row

        for row
        in board

        if row[
            "role_name"
        ]
        == "ALUMNI"

    ]


    if alumni_memberships:

        blockers.append(
            (
                "The DRAFT contains an "
                "ALUMNI membership. "
                "Alumni status must use "
                "alumni_profiles instead."
            )
        )


    # ========================================================
    # DEPARTMENT RULES
    # ========================================================

    for row in board:

        role_name = (
            row[
                "role_name"
            ]
        )


        if (
            role_name
            in DEPARTMENT_REQUIRED_ROLES

            and

            row[
                "department_id"
            ]
            is None
        ):

            blockers.append(
                (
                    f"{full_name(row)} "
                    f"({role_name}) needs "
                    "a department."
                )
            )


    # ========================================================
    # REQUIRED ACCOUNTS
    # ========================================================

    required_accounts = []


    if len(
        presidents
    ) == 1:

        required_accounts.append(
            (
                "Incoming President",
                presidents[0],
            )
        )


    if len(
        vice_presidents
    ) == 1:

        required_accounts.append(
            (
                "Incoming Vice President",
                vice_presidents[0],
            )
        )


    if len(
        secretary_generals
    ) == 1:

        required_accounts.append(
            (
                "Incoming Secretary General",
                secretary_generals[0],
            )
        )


    if len(
        hr_heads
    ) == 1:

        required_accounts.append(
            (
                "Incoming Human Resources Head",
                hr_heads[0],
            )
        )


    for (
        label,
        holder,
    ) in required_accounts:

        if not account_ready(
            holder
        ):

            blockers.append(
                (
                    f"{label} "
                    f"{full_name(holder)} "
                    "must have an active "
                    "CMS account before activation."
                )
            )


    # ========================================================
    # PEOPLE QUALITY
    # ========================================================

    for row in board:

        if (
            not (
                row[
                    "first_name"
                ]
                or ""
            ).strip()

            or

            not (
                row[
                    "last_name"
                ]
                or ""
            ).strip()
        ):

            blockers.append(
                (
                    "Every 2026/2027 "
                    "membership must point "
                    "to a person with a "
                    "first and last name."
                )
            )

            break


    # ========================================================
    # APPROVALS
    # ========================================================

    approvals = cursor.execute(
        """
        SELECT
            mandate_approvals.approval_id,
            mandate_approvals.approval_type,
            mandate_approvals.approved_by_user_id,
            mandate_approvals.approved_at,

            users.username,
            users.is_active,

            people.first_name,
            people.last_name

        FROM mandate_approvals

        JOIN users

            ON users.user_id =
               mandate_approvals.approved_by_user_id

        JOIN people

            ON people.person_id =
               users.person_id

        WHERE
            mandate_approvals.term_id = ?

        ORDER BY
            mandate_approvals.approval_type
        """,
        (
            target_term[
                "term_id"
            ],
        ),
    ).fetchall()


    approval_types = {

        row[
            "approval_type"
        ]

        for row
        in approvals

    }


    if (
        "PRESIDENT"
        not in approval_types
    ):

        blockers.append(
            (
                "Outgoing President "
                "approval is missing."
            )
        )


    if (
        "VICE_PRESIDENT"
        not in approval_types
    ):

        blockers.append(
            (
                "Outgoing Vice President "
                "approval is missing."
            )
        )


    for row in approvals:

        if not row[
            "is_active"
        ]:

            blockers.append(
                (
                    "A mandate approval "
                    "was recorded by an "
                    "inactive CMS account."
                )
            )


    # ========================================================
    # OUTGOING PRESIDENT
    # Needed for normal activation.
    # ========================================================

    outgoing_president = (
        cursor.execute(
            """
            SELECT
                memberships.membership_id,

                people.person_id,
                people.first_name,
                people.last_name,

                users.user_id,
                users.username,
                users.is_active

            FROM memberships

            JOIN people

                ON people.person_id =
                   memberships.person_id

            JOIN roles

                ON roles.role_id =
                   memberships.role_id

            LEFT JOIN users

                ON users.person_id =
                   people.person_id

            WHERE
                memberships.term_id = ?

              AND roles.name =
                  'PRESIDENT'

            LIMIT 1
            """,
            (
                current_term[
                    "term_id"
                ],
            ),
        ).fetchone()
    )


    if outgoing_president is None:

        blockers.append(
            (
                "The outgoing 2025/2026 "
                "President membership "
                "is missing."
            )
        )


    elif (
        not outgoing_president[
            "user_id"
        ]
        or
        not outgoing_president[
            "is_active"
        ]
    ):

        warnings.append(
            (
                "The outgoing President "
                "does not have an active "
                "CMS account. Normal "
                "activation will therefore "
                "not be possible; only the "
                "Platform Admin emergency "
                "path could be used."
            )
        )


    # ========================================================
    # EXPECTED DB PROTECTIONS
    # ========================================================

    required_indexes = {

        "idx_terms_single_active",

        "idx_terms_single_draft",

    }


    database_indexes = {

        row[
            "name"
        ]

        for row in cursor.execute(
            """
            SELECT name

            FROM sqlite_master

            WHERE type = 'index'
            """
        ).fetchall()

    }


    for index_name in (
        required_indexes
    ):

        if (
            index_name
            not in database_indexes
        ):

            blockers.append(
                (
                    "Missing mandate safety "
                    f"index: {index_name}"
                )
            )


    required_triggers = {

        "trg_archived_terms_no_update",

        "trg_archived_terms_no_delete",

    }


    database_triggers = {

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


    for trigger_name in (
        required_triggers
    ):

        if (
            trigger_name
            not in database_triggers
        ):

            blockers.append(
                (
                    "Missing historical "
                    "immutability trigger: "
                    f"{trigger_name}"
                )
            )


    conn.close()


    result = {

        "ready":
            len(
                blockers
            )
            == 0,

        "blockers":
            blockers,

        "warnings":
            warnings,

        "integrity":
            integrity,

        "foreign_keys":
            foreign_keys,

        "current_term":
            current_term,

        "target_term":
            target_term,

        "board":
            board,

        "approvals":
            approvals,

        "election":
            election,

        "outgoing_president":
            outgoing_president,
    }


    # ========================================================
    # OUTPUT
    # ========================================================

    if verbose:

        print(
            "========================================"
        )

        print(
            "2026/2027 ACTIVATION PREFLIGHT"
        )

        print(
            "========================================"
        )

        print()


        print(
            "Current mandate:",
            current_term[
                "name"
            ],
            "-",
            current_term[
                "status"
            ],
        )


        print(
            "Target mandate:",
            target_term[
                "name"
            ],
            "-",
            target_term[
                "status"
            ],
        )


        print()

        print(
            "2026/2027 BOARD"
        )

        print(
            "----------------------------------------"
        )


        if board:

            for row in board:

                department = (
                    row[
                        "department_name"
                    ]
                    or
                    "Executive"
                )


                account = (
                    row[
                        "username"
                    ]
                    if row[
                        "user_is_active"
                    ]
                    else
                    "NO ACTIVE CMS ACCOUNT"
                )


                print(
                    f"- {full_name(row)}"
                    f" | {row['role_name']}"
                    f" | {department}"
                    f" | {account}"
                )


        else:

            print(
                "No members."
            )


        print()

        print(
            "APPROVALS"
        )

        print(
            "----------------------------------------"
        )


        if approvals:

            for row in approvals:

                print(
                    "-",
                    row[
                        "approval_type"
                    ],
                    ":",
                    (
                        row[
                            "first_name"
                        ]
                        +
                        " "
                        +
                        row[
                            "last_name"
                        ]
                    ),
                    "(",
                    row[
                        "username"
                    ],
                    ")",
                )


        else:

            print(
                "No approvals recorded."
            )


        print()

        print(
            "DATABASE"
        )

        print(
            "----------------------------------------"
        )

        print(
            "Integrity check:",
            integrity,
        )

        print(
            "Foreign key check:",
            foreign_keys,
        )

        print()


        if warnings:

            print(
                "WARNINGS"
            )

            print(
                "----------------------------------------"
            )


            for warning in warnings:

                print(
                    "-",
                    warning,
                )


            print()


        if blockers:

            print(
                "BLOCKERS"
            )

            print(
                "----------------------------------------"
            )


            for blocker in blockers:

                print(
                    "-",
                    blocker,
                )


            print()

            print(
                "========================================"
            )

            print(
                "ACTIVATION STATUS: NOT READY"
            )

            print(
                "========================================"
            )


        else:

            print(
                "========================================"
            )

            print(
                "ACTIVATION STATUS: READY"
            )

            print(
                "========================================"
            )


    return result


# ============================================================
# MAIN
# ============================================================

def main():

    parser = (
        argparse.ArgumentParser(
            description=(
                "Validate the real "
                "2026/2027 mandate before "
                "activation."
            )
        )
    )


    parser.add_argument(
        "--backup",
        action="store_true",
        help=(
            "Create the final pre-activation "
            "database backup, but only if "
            "all blockers are resolved."
        ),
    )


    arguments = (
        parser.parse_args()
    )


    result = (
        run_preflight()
    )


    if not result[
        "ready"
    ]:

        raise SystemExit(
            1
        )


    if arguments.backup:

        backup = create_backup(
            DATABASE_PATH,
            BACKUP_PATH,
        )


        print()

        print(
            "Pre-activation backup:"
        )

        print(
            backup
        )


        print()

        print(
            "BACKUP READY."
        )


if __name__ == "__main__":

    main()