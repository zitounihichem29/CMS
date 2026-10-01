import io
import shutil
from pathlib import Path

import database

from app import app


BACKEND_DIR = (
    Path(__file__).resolve().parent
)

REAL_DB = (
    BACKEND_DIR.parent
    / "database"
    / "rsclub.db"
)

TEST_DB = (
    BACKEND_DIR.parent
    / "database"
    / "records_module_test.db"
)

UPLOAD_ROOT = (
    BACKEND_DIR
    / "uploads"
    / "records"
)

created_files = []


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


    active = conn.execute(
        """
        SELECT
            term_id,
            name

        FROM terms

        WHERE status = 'ACTIVE'

        LIMIT 1
        """
    ).fetchone()


    require(
        active is not None,
        "ACTIVE term missing.",
    )


    # ========================================================
    # MANAGER
    # ========================================================

    manager = conn.execute(
        """
        SELECT
            users.user_id,
            users.username,

            people.person_id,

            memberships.membership_id

        FROM users

        JOIN people

            ON people.person_id =
               users.person_id

        JOIN memberships

            ON memberships.person_id =
               people.person_id

           AND memberships.term_id = ?

        WHERE
            users.is_active = 1

          AND users.is_platform_admin = 1

        ORDER BY
            users.user_id

        LIMIT 1
        """,
        (
            active[
                "term_id"
            ],
        ),
    ).fetchone()


    require(
        manager is not None,

        (
            "Active Platform Admin "
            "membership missing."
        ),
    )


    # ========================================================
    # ORDINARY MEMBER
    # ========================================================

    ordinary = conn.execute(
        """
        SELECT
            users.user_id,
            users.username,

            people.person_id,

            memberships.membership_id

        FROM users

        JOIN people

            ON people.person_id =
               users.person_id

        JOIN memberships

            ON memberships.person_id =
               people.person_id

           AND memberships.term_id = ?

        JOIN roles

            ON roles.role_id =
               memberships.role_id

        LEFT JOIN departments

            ON departments.department_id =
               memberships.department_id

        WHERE
            users.is_active = 1

          AND users.is_platform_admin = 0

          AND roles.name = 'MEMBER'

        ORDER BY
            users.user_id

        LIMIT 1
        """,
        (
            active[
                "term_id"
            ],
        ),
    ).fetchone()


    require(
        ordinary is not None,

        (
            "Ordinary active member "
            "missing."
        ),
    )


    # ========================================================
    # KEEP TEST ISOLATED FROM REAL SCHEDULE
    # ========================================================

    conn.execute(
        """
        DELETE FROM annual_schedule

        WHERE term_id = ?
        """,
        (
            active[
                "term_id"
            ],
        ),
    )


    # ========================================================
    # TEMP EVENT
    # ========================================================

    conn.execute(
        """
        INSERT INTO events (
            term_id,
            event_leader_membership_id,
            title,
            event_date
        )

        VALUES (
            ?,
            ?,
            'Task 10 Event',
            '2099-01-10'
        )
        """,
        (
            active[
                "term_id"
            ],

            manager[
                "membership_id"
            ],
        ),
    )


    event_id = (
        conn.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]
    )


    # ========================================================
    # TEMP TRAINING
    # ========================================================

    conn.execute(
        """
        INSERT INTO trainings (
            coach_person_id,
            title,
            training_date
        )

        VALUES (
            ?,
            'Task 10 Training',
            '2099-01-11'
        )
        """,
        (
            manager[
                "person_id"
            ],
        ),
    )


    training_id = (
        conn.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]
    )


    conn.execute(
        """
        INSERT INTO training_terms (
            training_id,
            term_id
        )

        VALUES (?, ?)
        """,
        (
            training_id,

            active[
                "term_id"
            ],
        ),
    )


    # ========================================================
    # TEMP / EXISTING ARTICLE
    # ========================================================

    article = conn.execute(
        """
        SELECT
            scientific_articles.scientific_article_id

        FROM scientific_articles

        JOIN article_terms

            ON article_terms.scientific_article_id =
               scientific_articles.scientific_article_id

        WHERE
            article_terms.term_id = ?

        LIMIT 1
        """,
        (
            active[
                "term_id"
            ],
        ),
    ).fetchone()


    if article is None:

        conn.execute(
            """
            INSERT INTO scientific_articles (
                article_owner_membership_id,
                title,
                status
            )

            VALUES (
                ?,
                'Task 10 Reference Article',
                'active'
            )
            """,
            (
                manager[
                    "membership_id"
                ],
            ),
        )


        article_id = (
            conn.execute(
                "SELECT last_insert_rowid()"
            ).fetchone()[0]
        )


        conn.execute(
            """
            INSERT INTO article_terms (
                scientific_article_id,
                term_id
            )

            VALUES (?, ?)
            """,
            (
                article_id,

                active[
                    "term_id"
                ],
            ),
        )


    else:

        article_id = article[
            "scientific_article_id"
        ]


    conn.commit()

    conn.close()


    print(
        "Records manager:",
        manager[
            "username"
        ],
    )


    print(
        "Ordinary viewer:",
        ordinary[
            "username"
        ],
    )


    # ========================================================
    # ANONYMOUS
    # ========================================================

    with app.test_client() as client:

        response = client.get(
            "/records",
            follow_redirects=False,
        )


        require(
            response.status_code
            == 302,

            (
                "Anonymous /records "
                "was not redirected."
            ),
        )


    print(
        "Anonymous protection: OK"
    )


    # ========================================================
    # ORDINARY MEMBER
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            ordinary[
                "user_id"
            ],
        )


        require(
            client.get(
                "/records"
            ).status_code
            == 200,

            (
                "Ordinary member cannot "
                "view records home."
            ),
        )


        require(
            client.get(
                "/records/member-notes"
            ).status_code
            == 403,

            (
                "Ordinary member can "
                "view private notes."
            ),
        )


        require(
            client.get(
                "/records/attendance"
            ).status_code
            == 403,

            (
                "Ordinary member can "
                "manage attendance."
            ),
        )


    print(
        "View/manage permission split: OK"
    )


    # ========================================================
    # CREATE MEETING
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            manager[
                "user_id"
            ],
        )


        response = client.post(
            "/records/meetings",

            data={

                "title":
                    "Task 10 General Meeting",

                "description":
                    "Temporary test meeting.",

                "meeting_date":
                    "2099-01-12",

                "start_time":
                    "10:00",

                "end_time":
                    "11:00",

                "location":
                    "USTHB",
            },

            follow_redirects=False,
        )


        require(
            redirect_ok(
                response
            ),

            "Meeting creation failed.",
        )


    conn = (
        database.get_db_connection()
    )


    meeting = conn.execute(
        """
        SELECT
            meeting_id,
            term_id

        FROM meetings

        WHERE
            title =
            'Task 10 General Meeting'
        """
    ).fetchone()


    require(

        meeting is not None

        and meeting[
            "term_id"
        ]
        == active[
            "term_id"
        ],

        "Meeting mandate link failed.",
    )


    meeting_id = (
        meeting[
            "meeting_id"
        ]
    )


    conn.close()


    print(
        "General meeting creation: OK"
    )


    # ========================================================
    # MEETING ATTENDANCE
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            manager[
                "user_id"
            ],
        )


        response = client.post(
            (
                f"/records/meetings/"
                f"{meeting_id}/attendance"
            ),

            data={

                (
                    f"status_"
                    f"{manager['membership_id']}"
                ):
                    "present",

                (
                    f"status_"
                    f"{ordinary['membership_id']}"
                ):
                    "late",
            },

            follow_redirects=False,
        )


        require(
            redirect_ok(
                response
            ),

            "Meeting attendance failed.",
        )


    conn = (
        database.get_db_connection()
    )


    meeting_attendance_count = (
        conn.execute(
            """
            SELECT COUNT(*)

            FROM meeting_attendance

            WHERE meeting_id = ?
            """,
            (
                meeting_id,
            ),
        ).fetchone()[0]
    )


    require(
        meeting_attendance_count
        == 2,

        (
            "Meeting attendance "
            "rows incorrect."
        ),
    )


    conn.close()


    print(
        "Meeting attendance: OK"
    )


    # ========================================================
    # EVENT + TRAINING ATTENDANCE
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            manager[
                "user_id"
            ],
        )


        response = client.post(
            (
                "/records/attendance/"
                f"event/{event_id}"
            ),

            data={
                (
                    f"status_"
                    f"{manager['membership_id']}"
                ):
                    "present",
            },

            follow_redirects=False,
        )


        require(
            redirect_ok(
                response
            ),

            "Event attendance failed.",
        )


        response = client.post(
            (
                "/records/attendance/"
                f"training/{training_id}"
            ),

            data={
                (
                    f"status_"
                    f"{ordinary['membership_id']}"
                ):
                    "excused",
            },

            follow_redirects=False,
        )


        require(
            redirect_ok(
                response
            ),

            "Training attendance failed.",
        )


    print(
        "Event/training attendance: OK"
    )


    # ========================================================
    # ANNUAL SCHEDULE
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            manager[
                "user_id"
            ],
        )


        response = client.post(
            "/records/schedule",

            data={

                "title":
                    "Task 10 Annual Schedule",

                "description":
                    "Temporary test schedule.",

                "schedule_file":
                    (
                        io.BytesIO(
                            b"%PDF test schedule"
                        ),
                        "schedule.pdf",
                    ),
            },

            content_type=(
                "multipart/form-data"
            ),

            follow_redirects=False,
        )


        require(
            redirect_ok(
                response
            ),

            "Annual schedule save failed.",
        )


    conn = (
        database.get_db_connection()
    )


    schedule = conn.execute(
        """
        SELECT
            file_path

        FROM annual_schedule

        WHERE term_id = ?
        """,
        (
            active[
                "term_id"
            ],
        ),
    ).fetchone()


    require(

        schedule is not None

        and schedule[
            "file_path"
        ],

        (
            "Annual schedule record/"
            "file path missing."
        ),
    )


    created_files.append(

        UPLOAD_ROOT
        / "schedules"
        / schedule[
            "file_path"
        ]

    )


    conn.close()


    print(
        "Annual schedule: OK"
    )


    # ========================================================
    # MEMBER NOTES
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            manager[
                "user_id"
            ],
        )


        response = client.post(
            "/records/member-notes",

            data={

                "membership_id":
                    str(
                        ordinary[
                            "membership_id"
                        ]
                    ),

                "note_type":
                    "POSITIVE",

                "note":
                    (
                        "Task 10 private "
                        "note test."
                    ),
            },

            follow_redirects=False,
        )


        require(
            redirect_ok(
                response
            ),

            "Member note creation failed.",
        )


    conn = (
        database.get_db_connection()
    )


    note = conn.execute(
        """
        SELECT
            note_type

        FROM member_notes

        WHERE
            note =
            'Task 10 private note test.'
        """
    ).fetchone()


    require(

        note is not None

        and note[
            "note_type"
        ]
        == "POSITIVE",

        "Member note type failed.",
    )


    conn.close()


    print(
        "Private member notes: OK"
    )


    # ========================================================
    # CERTIFICATE
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            manager[
                "user_id"
            ],
        )


        response = client.post(
            "/records/certificates",

            data={

                "name":
                    "Task 10 Certificate",

                "certificate_type":
                    "Participation",

                "issued_date":
                    "2099-01-20",

                "description":
                    (
                        "Temporary "
                        "certificate test."
                    ),

                "recipient_ids":
                    [
                        str(
                            manager[
                                "person_id"
                            ]
                        ),

                        str(
                            ordinary[
                                "person_id"
                            ]
                        ),
                    ],

                "certificate_file":
                    (
                        io.BytesIO(
                            b"%PDF certificate"
                        ),
                        "certificate.pdf",
                    ),
            },

            content_type=(
                "multipart/form-data"
            ),

            follow_redirects=False,
        )


        require(
            redirect_ok(
                response
            ),

            "Certificate creation failed.",
        )


    conn = (
        database.get_db_connection()
    )


    certificate = conn.execute(
        """
        SELECT
            certificate_id,
            file_path

        FROM certificates

        WHERE
            name =
            'Task 10 Certificate'
        """
    ).fetchone()


    require(
        certificate is not None,

        "Certificate record missing.",
    )


    certificate_id = (
        certificate[
            "certificate_id"
        ]
    )


    created_files.append(

        UPLOAD_ROOT
        / "certificates"
        / certificate[
            "file_path"
        ]

    )


    recipients = conn.execute(
        """
        SELECT
            recipient_name_snapshot

        FROM certificate_recipients

        WHERE certificate_id = ?
        """,
        (
            certificate_id,
        ),
    ).fetchall()


    require(

        len(
            recipients
        )
        == 2

        and all(

            row[
                "recipient_name_snapshot"
            ]

            for row
            in recipients

        ),

        (
            "Certificate recipient "
            "snapshots failed."
        ),
    )


    conn.close()


    print(
        "Certificates + recipient snapshots: OK"
    )


    # ========================================================
    # SOURCE REFERENCE
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            manager[
                "user_id"
            ],
        )


        response = client.post(
            "/records/references/new",

            data={

                "title":
                    "Task 10 Source",

                "authors":
                    "Test Author",

                "source_type":
                    "Article",

                "publication_year":
                    "2026",

                "url":
                    "https://example.com/source",

                "doi":
                    "10.0000/task10",
            },

            follow_redirects=False,
        )


        require(
            redirect_ok(
                response
            ),

            (
                "Source reference "
                "creation failed."
            ),
        )


    conn = (
        database.get_db_connection()
    )


    source = conn.execute(
        """
        SELECT
            source_reference_id

        FROM source_references

        WHERE
            title =
            'Task 10 Source'
        """
    ).fetchone()


    require(
        source is not None,

        "Source reference missing.",
    )


    source_id = (
        source[
            "source_reference_id"
        ]
    )


    conn.close()


    # ========================================================
    # LINK SOURCE TO ARTICLE
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            manager[
                "user_id"
            ],
        )


        response = client.post(
            "/records/references/link",

            data={

                "article_id":
                    str(
                        article_id
                    ),

                "source_id":
                    str(
                        source_id
                    ),
            },

            follow_redirects=False,
        )


        require(
            redirect_ok(
                response
            ),

            "Article/source link failed.",
        )


    conn = (
        database.get_db_connection()
    )


    link = conn.execute(
        """
        SELECT
            source_title_snapshot

        FROM article_source_references

        WHERE
            scientific_article_id = ?

          AND source_reference_id = ?
        """,
        (
            article_id,
            source_id,
        ),
    ).fetchone()


    require(

        link is not None

        and link[
            "source_title_snapshot"
        ]
        == "Task 10 Source",

        "Source snapshot failed.",
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


    conn.close()


    require(
        integrity == "ok",

        "Integrity check failed.",
    )


    require(
        not foreign_keys,

        "Foreign key check failed.",
    )


    print(
        "Research source library "
        "+ article link: OK"
    )


    print()

    print(
        "========================================"
    )

    print(
        "CLUB RECORDS MODULE TEST SUCCESSFUL"
    )

    print(
        "========================================"
    )


    print(
        "General meetings: OK"
    )

    print(
        "Meeting attendance: OK"
    )

    print(
        "Event/training attendance: OK"
    )

    print(
        "Annual schedule: OK"
    )

    print(
        "Private member notes: OK"
    )

    print(
        "Certificates: OK"
    )

    print(
        "Research source references: OK"
    )

    print(
        "Permission separation: OK"
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

    for path in created_files:

        if (
            path
            and path.exists()
        ):

            try:

                path.unlink()

            except OSError:

                pass


    if TEST_DB.exists():

        TEST_DB.unlink()


    print(
        "Temporary database deleted."
    )