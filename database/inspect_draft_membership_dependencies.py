import sqlite3
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = DATABASE_DIR / "rsclub.db"

TARGET_TERM_NAME = "2026/2027"


def connect():

    conn = sqlite3.connect(
        DATABASE_PATH,
        timeout=10,
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


def quote_identifier(name):

    return (
        '"'
        +
        name.replace(
            '"',
            '""',
        )
        +
        '"'
    )


conn = connect()

cursor = conn.cursor()


# ============================================================
# TARGET TERM
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
        TARGET_TERM_NAME,
    ),
).fetchone()


if term is None:

    conn.close()

    raise SystemExit(
        "2026/2027 mandate not found."
    )


print(
    "========================================"
)

print(
    "DRAFT MEMBERSHIP DEPENDENCY INSPECTION"
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
# FIND EVERY TABLE THAT REFERENCES memberships
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


membership_references = []


for table_row in tables:

    table_name = table_row["name"]

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

            membership_references.append(
                {
                    "table":
                        table_name,

                    "column":
                        foreign_key["from"],

                    "target_column":
                        foreign_key["to"],
                }
            )


print(
    "Tables referencing memberships:",
    len(
        membership_references
    ),
)

print()


# ============================================================
# DRAFT MEMBERSHIPS
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
        memberships.membership_id
    """,
    (
        term["term_id"],
    ),
).fetchall()


# ============================================================
# INSPECT EACH MEMBERSHIP
# ============================================================

blocked_count = 0
clean_count = 0


for membership in memberships:

    membership_id = (
        membership[
            "membership_id"
        ]
    )

    dependencies = []


    for reference in (
        membership_references
    ):

        table_name = (
            reference["table"]
        )

        column_name = (
            reference["column"]
        )


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
                membership_id,
            ),
        ).fetchone()[0]


        if count:

            dependencies.append(
                {
                    "table":
                        table_name,

                    "column":
                        column_name,

                    "count":
                        count,
                }
            )


    print(
        "----------------------------------------"
    )

    print(
        "Membership ID:",
        membership_id,
    )

    print(
        "Person:",
        membership["first_name"],
        membership["last_name"],
    )

    print(
        "Username:",
        (
            membership["username"]
            or "No account"
        ),
    )

    print(
        "Account:",
        (
            "Active"
            if membership["is_active"]
            else "Inactive / none"
        ),
    )

    print(
        "Role:",
        membership["role_name"],
    )

    print(
        "Department:",
        (
            membership[
                "department_name"
            ]
            or "Executive"
        ),
    )


    if dependencies:

        blocked_count += 1

        print(
            "DELETE STATUS: BLOCKED"
        )

        print(
            "Referenced by:"
        )


        for dependency in dependencies:

            print(
                "  -",
                dependency["table"],
                ".",
                dependency["column"],
                ":",
                dependency["count"],
                "row(s)",
            )


    else:

        clean_count += 1

        print(
            "DELETE STATUS: SAFE"
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
    "Draft memberships:",
    len(
        memberships
    ),
)

print(
    "Safe to remove:",
    clean_count,
)

print(
    "Referenced / blocked:",
    blocked_count,
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