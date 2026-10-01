import sqlite3
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = (
    DATABASE_DIR
    / "rsclub.db"
)

TERM_NAME = "2025/2026"


OFFICIAL_BOARD = {

    "hamma_yasmine",

    "masmoudi_mohamed",

    "belhadj_sarah",

    "souilah_wissal",

    "benantar_wadoud",

    "tamda_karim",
}


OFFICIAL_BOARD_NAMES = {

    (
        "nour el houda",
        "amellal",
    ),

    (
        "farah",
        "djermoune",
    ),
}


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


def quote_identifier(
    value,
):

    return (
        '"'
        +
        value.replace(
            '"',
            '""',
        )
        +
        '"'
    )


def normalized(
    value,
):

    return (
        value
        or ""
    ).strip().lower()


conn = connect()

cursor = conn.cursor()


# ============================================================
# TERM
# ============================================================

term = cursor.execute(
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
        TERM_NAME,
    ),
).fetchone()


if term is None:

    conn.close()

    raise SystemExit(
        "2025/2026 mandate not found."
    )


print(
    "========================================"
)

print(
    "2025/2026 MEMBERSHIP CLEANUP INSPECTION"
)

print(
    "========================================"
)

print()

print(
    "Mandate:",
    term["name"],
    "-",
    term["status"],
)

print()


# ============================================================
# TABLES REFERENCING MEMBERSHIPS
# ============================================================

tables = cursor.execute(
    """
    SELECT name

    FROM sqlite_master

    WHERE
        type = 'table'

      AND name NOT LIKE 'sqlite_%'

    ORDER BY name
    """
).fetchall()


references = []


for table in tables:

    table_name = (
        table["name"]
    )


    foreign_keys = cursor.execute(
        f"""
        PRAGMA foreign_key_list(
            {quote_identifier(table_name)}
        )
        """
    ).fetchall()


    for foreign_key in foreign_keys:

        if (
            foreign_key["table"]
            == "memberships"
        ):

            references.append(
                (
                    table_name,
                    foreign_key["from"],
                )
            )


# ============================================================
# MEMBERSHIPS
# ============================================================

memberships = cursor.execute(
    """
    SELECT
        memberships.membership_id,
        memberships.person_id,
        memberships.department_id,

        people.first_name,
        people.last_name,

        roles.name
            AS role_name,

        departments.name
            AS department_name,

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

        people.first_name,

        people.last_name
    """,
    (
        term["term_id"],
    ),
).fetchall()


board_count = 0
other_count = 0


for membership in memberships:

    username = normalized(
        membership[
            "username"
        ]
    )


    name_key = (
        normalized(
            membership[
                "first_name"
            ]
        ),

        normalized(
            membership[
                "last_name"
            ]
        ),
    )


    is_board = (
        username
        in OFFICIAL_BOARD

        or

        name_key
        in OFFICIAL_BOARD_NAMES
    )


    if is_board:

        board_count += 1

    else:

        other_count += 1


    dependency_count = 0

    dependencies = []


    for (
        table_name,
        column_name,
    ) in references:

        count = cursor.execute(
            f"""
            SELECT COUNT(*)

            FROM
                {quote_identifier(table_name)}

            WHERE
                {quote_identifier(column_name)}
                = ?
            """,
            (
                membership[
                    "membership_id"
                ],
            ),
        ).fetchone()[0]


        if count:

            dependency_count += (
                count
            )

            dependencies.append(
                (
                    table_name,
                    column_name,
                    count,
                )
            )


    print(
        "----------------------------------------"
    )

    print(
        "Membership ID:",
        membership[
            "membership_id"
        ],
    )

    print(
        "Person:",
        membership[
            "first_name"
        ],
        membership[
            "last_name"
        ],
    )

    print(
        "Username:",
        (
            membership[
                "username"
            ]
            or
            "No CMS account"
        ),
    )

    print(
        "Role:",
        membership[
            "role_name"
        ],
    )

    print(
        "Department:",
        (
            membership[
                "department_name"
            ]
            or
            "Executive"
        ),
    )


    if is_board:

        print(
            "CLEANUP DECISION: KEEP — OFFICIAL BOARD"
        )

    else:

        print(
            "CLEANUP DECISION: REMOVE FROM 2025/2026"
        )


    if dependencies:

        print(
            "References:"
        )


        for (
            table_name,
            column_name,
            count,
        ) in dependencies:

            print(
                "  -",
                table_name,
                ".",
                column_name,
                ":",
                count,
                "row(s)",
            )


    else:

        print(
            "References: none"
        )


    print()


# ============================================================
# HEALTH
# ============================================================

integrity = cursor.execute(
    "PRAGMA integrity_check"
).fetchone()[0]


foreign_keys = cursor.execute(
    "PRAGMA foreign_key_check"
).fetchall()


print(
    "========================================"
)

print(
    "SUMMARY"
)

print(
    "========================================"
)

print(
    "Official board memberships:",
    board_count,
)

print(
    "Other memberships to review/remove:",
    other_count,
)

print(
    "Total memberships:",
    len(
        memberships
    ),
)

print(
    "Integrity check:",
    integrity,
)

print(
    "Foreign key check:",
    foreign_keys,
)


conn.close()