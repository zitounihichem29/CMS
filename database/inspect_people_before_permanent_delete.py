import sqlite3
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = DATABASE_DIR / "rsclub.db"


TARGET_PEOPLE = [
    ("asma", "benaoudia"),
    ("chouayb", "mokrani"),
    ("fadoua", "slimani"),
    ("merazga", "safouane"),
    ("serine", "mekdad"),
]


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


def quote_identifier(value):

    return (
        '"'
        + value.replace(
            '"',
            '""',
        )
        + '"'
    )


conn = connect()

cursor = conn.cursor()


print(
    "========================================"
)

print(
    "PERMANENT PERSON DELETE INSPECTION"
)

print(
    "========================================"
)

print()


# ============================================================
# FIND ALL TABLES REFERENCING PEOPLE
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


people_references = []


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
            == "people"
        ):

            people_references.append(
                {
                    "table":
                        table_name,

                    "column":
                        foreign_key["from"],
                }
            )


print(
    "Tables/columns referencing PEOPLE:",
    len(people_references),
)

print()


# ============================================================
# INSPECT EACH TARGET PERSON
# ============================================================

safe_count = 0
blocked_count = 0
missing_count = 0


for (
    first_name,
    last_name,
) in TARGET_PEOPLE:

    rows = cursor.execute(
        """
        SELECT
            person_id,
            first_name,
            last_name,
            email,
            phone

        FROM people

        WHERE
            LOWER(TRIM(first_name)) = LOWER(?)

          AND LOWER(TRIM(last_name)) = LOWER(?)

        ORDER BY person_id
        """,
        (
            first_name,
            last_name,
        ),
    ).fetchall()


    print(
        "----------------------------------------"
    )

    print(
        "Target:",
        first_name,
        last_name,
    )


    if not rows:

        missing_count += 1

        print(
            "STATUS: PERSON NOT FOUND"
        )

        print()

        continue


    if len(rows) > 1:

        print(
            "WARNING:",
            len(rows),
            "matching PEOPLE rows found."
        )


    for person in rows:

        person_id = (
            person["person_id"]
        )


        print()

        print(
            "Person ID:",
            person_id,
        )

        print(
            "Name:",
            person["first_name"],
            person["last_name"],
        )

        print(
            "Email:",
            person["email"],
        )

        print(
            "Phone:",
            person["phone"],
        )


        dependencies = []


        for reference in (
            people_references
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
                    person_id,
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


        if dependencies:

            blocked_count += 1

            print(
                "DELETE STATUS: BLOCKED"
            )

            print(
                "Direct references:"
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


                # --------------------------------------------
                # SHOW APPLICATION DETAILS
                # --------------------------------------------

                if (
                    dependency["table"]
                    == "applications"
                ):

                    application_rows = (
                        cursor.execute(
                            """
                            SELECT
                                applications.application_id,
                                applications.status,
                                applications.submitted_at,

                                application_periods.name
                                    AS period_name,

                                terms.name
                                    AS term_name,

                                terms.status
                                    AS term_status

                            FROM applications

                            JOIN application_periods

                                ON application_periods.application_period_id =
                                   applications.application_period_id

                            JOIN terms

                                ON terms.term_id =
                                   application_periods.term_id

                            WHERE
                                applications.person_id = ?

                            ORDER BY
                                applications.application_id
                            """,
                            (
                                person_id,
                            ),
                        ).fetchall()
                    )


                    for application in (
                        application_rows
                    ):

                        print(
                            "      Application:",
                            application[
                                "application_id"
                            ],
                            "|",
                            application[
                                "period_name"
                            ],
                            "|",
                            application[
                                "term_name"
                            ],
                            application[
                                "term_status"
                            ],
                            "|",
                            application[
                                "status"
                            ],
                            "|",
                            application[
                                "submitted_at"
                            ],
                        )


                # --------------------------------------------
                # SHOW MEMBERSHIP DETAILS
                # --------------------------------------------

                if (
                    dependency["table"]
                    == "memberships"
                ):

                    membership_rows = (
                        cursor.execute(
                            """
                            SELECT
                                memberships.membership_id,

                                terms.name
                                    AS term_name,

                                terms.status
                                    AS term_status,

                                roles.name
                                    AS role_name,

                                departments.name
                                    AS department_name

                            FROM memberships

                            JOIN terms

                                ON terms.term_id =
                                   memberships.term_id

                            JOIN roles

                                ON roles.role_id =
                                   memberships.role_id

                            LEFT JOIN departments

                                ON departments.department_id =
                                   memberships.department_id

                            WHERE
                                memberships.person_id = ?

                            ORDER BY
                                terms.start_date
                            """,
                            (
                                person_id,
                            ),
                        ).fetchall()
                    )


                    for membership in (
                        membership_rows
                    ):

                        print(
                            "      Membership:",
                            membership[
                                "membership_id"
                            ],
                            "|",
                            membership[
                                "term_name"
                            ],
                            membership[
                                "term_status"
                            ],
                            "|",
                            membership[
                                "role_name"
                            ],
                            "|",
                            (
                                membership[
                                    "department_name"
                                ]
                                or
                                "Executive"
                            ),
                        )


                # --------------------------------------------
                # SHOW USER DETAILS
                # --------------------------------------------

                if (
                    dependency["table"]
                    == "users"
                ):

                    user_rows = (
                        cursor.execute(
                            """
                            SELECT
                                user_id,
                                username,
                                is_active,
                                is_platform_admin

                            FROM users

                            WHERE person_id = ?
                            """,
                            (
                                person_id,
                            ),
                        ).fetchall()
                    )


                    for user in user_rows:

                        print(
                            "      User:",
                            user["user_id"],
                            "| @",
                            user["username"],
                            "| active=",
                            user["is_active"],
                            "| platform_admin=",
                            user[
                                "is_platform_admin"
                            ],
                        )


        else:

            safe_count += 1

            print(
                "DELETE STATUS: SAFE"
            )

            print(
                "No direct database references."
            )


    print()


# ============================================================
# DATABASE HEALTH
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
    "Safe PEOPLE rows:",
    safe_count,
)

print(
    "Blocked PEOPLE rows:",
    blocked_count,
)

print(
    "Targets not found:",
    missing_count,
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