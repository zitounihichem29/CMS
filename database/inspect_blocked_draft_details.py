import sqlite3
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = DATABASE_DIR / "rsclub.db"

TERM_NAME = "2026/2027"


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


def q(identifier):

    return (
        '"'
        + identifier.replace(
            '"',
            '""',
        )
        + '"'
    )


def print_separator():

    print(
        "----------------------------------------"
    )


def print_term_links(
    cursor,
    table_name,
    item_id,
):

    if table_name == "projects":

        rows = cursor.execute(
            """
            SELECT
                terms.name,
                terms.status

            FROM project_terms

            JOIN terms
                ON terms.term_id =
                   project_terms.term_id

            WHERE project_terms.project_id = ?
            """,
            (
                item_id,
            ),
        ).fetchall()


    elif table_name == "scientific_articles":

        rows = cursor.execute(
            """
            SELECT
                terms.name,
                terms.status

            FROM article_terms

            JOIN terms
                ON terms.term_id =
                   article_terms.term_id

            WHERE
                article_terms.scientific_article_id = ?
            """,
            (
                item_id,
            ),
        ).fetchall()


    else:

        return


    if rows:

        print(
            "    Mandate links:"
        )


        for row in rows:

            print(
                "      -",
                row["name"],
                row["status"],
            )


def describe_task(
    cursor,
    task_id,
):

    task = cursor.execute(
        """
        SELECT *

        FROM tasks

        WHERE task_id = ?
        """,
        (
            task_id,
        ),
    ).fetchone()


    if task is None:

        return


    print(
        "    Task:",
        dict(task),
    )


def describe_announcement(
    cursor,
    announcement_id,
):

    row = cursor.execute(
        """
        SELECT *

        FROM announcements

        WHERE announcement_id = ?
        """,
        (
            announcement_id,
        ),
    ).fetchone()


    if row:

        print(
            "    Announcement:",
            dict(row),
        )


def describe_article(
    cursor,
    article_id,
):

    article = cursor.execute(
        """
        SELECT *

        FROM scientific_articles

        WHERE scientific_article_id = ?
        """,
        (
            article_id,
        ),
    ).fetchone()


    if article:

        print(
            "    Article:",
            dict(article),
        )


        print_term_links(
            cursor,
            "scientific_articles",
            article_id,
        )


def describe_project(
    cursor,
    project_id,
):

    project = cursor.execute(
        """
        SELECT *

        FROM projects

        WHERE project_id = ?
        """,
        (
            project_id,
        ),
    ).fetchone()


    if project:

        print(
            "    Project:",
            dict(project),
        )


        print_term_links(
            cursor,
            "projects",
            project_id,
        )


def describe_application_meeting(
    cursor,
    meeting_id,
):

    meeting = cursor.execute(
        """
        SELECT *

        FROM application_meetings

        WHERE meeting_id = ?
        """,
        (
            meeting_id,
        ),
    ).fetchone()


    if meeting is None:

        return


    print(
        "    Application meeting:",
        dict(meeting),
    )


    application = cursor.execute(
        """
        SELECT
            applications.*,

            application_periods.name
                AS period_name,

            application_periods.term_id,

            terms.name
                AS term_name,

            terms.status
                AS term_status,

            people.first_name,
            people.last_name

        FROM applications

        JOIN application_periods

            ON application_periods.application_period_id =
               applications.application_period_id

        JOIN terms

            ON terms.term_id =
               application_periods.term_id

        JOIN people

            ON people.person_id =
               applications.person_id

        WHERE
            applications.application_id = ?
        """,
        (
            meeting[
                "application_id"
            ],
        ),
    ).fetchone()


    if application:

        print(
            "    Application:",
            dict(application),
        )


def describe_organization(
    cursor,
    organization_id,
):

    organization = cursor.execute(
        """
        SELECT *

        FROM organizations

        WHERE organization_id = ?
        """,
        (
            organization_id,
        ),
    ).fetchone()


    if organization:

        print(
            "    Organization:",
            dict(organization),
        )


    relations = cursor.execute(
        """
        SELECT
            organization_relations.*,

            terms.name
                AS term_name,

            terms.status
                AS term_status

        FROM organization_relations

        JOIN terms

            ON terms.term_id =
               organization_relations.term_id

        WHERE
            organization_relations.organization_id = ?
        """,
        (
            organization_id,
        ),
    ).fetchall()


    if relations:

        print(
            "    Organization relations:"
        )


        for relation in relations:

            print(
                "      ",
                dict(relation),
            )


conn = connect()

cursor = conn.cursor()


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
        "2026/2027 mandate not found."
    )


tables = cursor.execute(
    """
    SELECT name

    FROM sqlite_master

    WHERE
        type = 'table'

      AND name NOT LIKE 'sqlite_%'
    """
).fetchall()


references = []


for table in tables:

    table_name = table["name"]


    foreign_keys = cursor.execute(
        f"""
        PRAGMA foreign_key_list(
            {q(table_name)}
        )
        """
    ).fetchall()


    for fk in foreign_keys:

        if (
            fk["table"]
            == "memberships"
        ):

            references.append(
                (
                    table_name,
                    fk["from"],
                )
            )


memberships = cursor.execute(
    """
    SELECT
        memberships.membership_id,
        memberships.person_id,

        people.first_name,
        people.last_name,

        roles.name
            AS role_name,

        departments.name
            AS department_name,

        users.username

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


print(
    "========================================"
)

print(
    "BLOCKED DRAFT REFERENCES — DETAILS"
)

print(
    "========================================"
)


for membership in memberships:

    membership_id = (
        membership[
            "membership_id"
        ]
    )


    dependencies = []


    for (
        table_name,
        column_name,
    ) in references:

        rows = cursor.execute(
            f"""
            SELECT *

            FROM {q(table_name)}

            WHERE
                {q(column_name)} = ?
            """,
            (
                membership_id,
            ),
        ).fetchall()


        if rows:

            dependencies.append(
                (
                    table_name,
                    column_name,
                    rows,
                )
            )


    if not dependencies:

        continue


    print()

    print_separator()

    print(
        "Membership:",
        membership_id,
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
            or "No account"
        ),
    )

    print(
        "Draft assignment:",
        membership[
            "role_name"
        ],
        "/",
        (
            membership[
                "department_name"
            ]
            or "Executive"
        ),
    )


    # Show this person's memberships
    # in all other mandates.

    other_memberships = cursor.execute(
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
            membership[
                "person_id"
            ],
        ),
    ).fetchall()


    print(
        "Membership history:"
    )


    for history in other_memberships:

        print(
            "  - membership_id=",
            history[
                "membership_id"
            ],
            "|",
            history[
                "term_name"
            ],
            history[
                "term_status"
            ],
            "|",
            history[
                "role_name"
            ],
            "|",
            (
                history[
                    "department_name"
                ]
                or "Executive"
            ),
        )


    print(
        "References:"
    )


    for (
        table_name,
        column_name,
        rows,
    ) in dependencies:

        print()

        print(
            "  TABLE:",
            table_name,
        )

        print(
            "  COLUMN:",
            column_name,
        )

        print(
            "  ROWS:",
            len(rows),
        )


        for row in rows:

            data = dict(
                row
            )


            print(
                "   ",
                data,
            )


            if (
                "task_id"
                in data

                and

                data[
                    "task_id"
                ]
                is not None
            ):

                describe_task(
                    cursor,
                    data[
                        "task_id"
                    ],
                )


            if (
                "announcement_id"
                in data

                and

                data[
                    "announcement_id"
                ]
                is not None
            ):

                describe_announcement(
                    cursor,
                    data[
                        "announcement_id"
                    ],
                )


            if (
                "scientific_article_id"
                in data

                and

                data[
                    "scientific_article_id"
                ]
                is not None
            ):

                describe_article(
                    cursor,
                    data[
                        "scientific_article_id"
                    ],
                )


            if (
                "project_id"
                in data

                and

                data[
                    "project_id"
                ]
                is not None
            ):

                describe_project(
                    cursor,
                    data[
                        "project_id"
                    ],
                )


            if (
                table_name
                ==
                "application_meeting_participants"

                and

                data.get(
                    "meeting_id"
                )
                is not None
            ):

                describe_application_meeting(
                    cursor,
                    data[
                        "meeting_id"
                    ],
                )


            if (
                "organization_id"
                in data

                and

                data[
                    "organization_id"
                ]
                is not None
            ):

                describe_organization(
                    cursor,
                    data[
                        "organization_id"
                    ],
                )


print()

print(
    "========================================"
)

print(
    "DATABASE HEALTH"
)

print(
    "========================================"
)


print(
    "Integrity check:",
    cursor.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0],
)


print(
    "Foreign key check:",
    cursor.execute(
        "PRAGMA foreign_key_check"
    ).fetchall(),
)


conn.close()