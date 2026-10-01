import shutil
import sqlite3
from pathlib import Path

from migrate_records_v1 import (
    migrate_database,
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
    / "records_migration_test.db"
)


def connect(path):

    conn = sqlite3.connect(
        path,
        timeout=10,
    )

    conn.row_factory = sqlite3.Row

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


def blocked(
    action,
    message,
):

    try:

        action()

    except sqlite3.IntegrityError:

        return


    raise RuntimeError(
        message
    )


if TEST_DB.exists():

    TEST_DB.unlink()


shutil.copy2(
    REAL_DB,
    TEST_DB,
)


try:

    migrate_database(
        db_path=TEST_DB,
        create_backup_file=False,
        verbose=False,
    )


    conn = connect(
        TEST_DB
    )

    cursor = conn.cursor()


    meeting_columns = {

        row["name"]

        for row in cursor.execute(
            'PRAGMA table_info("meetings")'
        )

    }


    schedule_columns = {

        row["name"]

        for row in cursor.execute(
            'PRAGMA table_info("annual_schedule")'
        )

    }


    certificate_columns = {

        row["name"]

        for row in cursor.execute(
            'PRAGMA table_info("certificates")'
        )

    }


    recipient_columns = {

        row["name"]

        for row in cursor.execute(
            'PRAGMA table_info("certificate_recipients")'
        )

    }


    note_columns = {

        row["name"]

        for row in cursor.execute(
            'PRAGMA table_info("member_notes")'
        )

    }


    article_ref_columns = {

        row["name"]

        for row in cursor.execute(
            'PRAGMA table_info("article_source_references")'
        )

    }


    require(
        "term_id"
        in meeting_columns,

        "meetings.term_id missing.",
    )


    require(
        "original_filename"
        in schedule_columns,

        (
            "annual_schedule."
            "original_filename missing."
        ),
    )


    require(

        {
            "term_id",
            "created_by_membership_id",
            "original_filename",
        }
        <= certificate_columns,

        "Certificate metadata columns missing.",
    )


    require(
        "recipient_name_snapshot"
        in recipient_columns,

        (
            "Certificate recipient "
            "snapshot missing."
        ),
    )


    require(
        "note_type"
        in note_columns,

        "member_notes.note_type missing.",
    )


    require(

        {
            "source_title_snapshot",
            "source_authors_snapshot",
            "source_type_snapshot",
            "source_publication_year_snapshot",
            "source_url_snapshot",
            "source_doi_snapshot",
        }
        <= article_ref_columns,

        "Article source snapshots missing.",
    )


    indexes = {

        row["name"]

        for row in cursor.execute(
            """
            SELECT name

            FROM sqlite_master

            WHERE
                type = 'index'

              AND sql IS NOT NULL
            """
        )

    }


    for index_name in {

        "idx_meetings_term_date",

        "idx_member_notes_membership_created",

        "idx_certificates_term_date",

    }:

        require(

            index_name in indexes,

            f"Missing index: {index_name}",
        )


    active = cursor.execute(
        """
        SELECT term_id

        FROM terms

        WHERE status = 'ACTIVE'

        LIMIT 1
        """
    ).fetchone()


    archived = cursor.execute(
        """
        SELECT term_id

        FROM terms

        WHERE status = 'ARCHIVED'

        LIMIT 1
        """
    ).fetchone()


    require(
        active is not None,
        "ACTIVE term missing.",
    )


    require(
        archived is not None,
        "ARCHIVED term missing.",
    )


    active_member = cursor.execute(
        """
        SELECT
            membership_id,
            person_id

        FROM memberships

        WHERE term_id = ?

        LIMIT 1
        """,
        (
            active[
                "term_id"
            ],
        ),
    ).fetchone()


    archived_member = cursor.execute(
        """
        SELECT
            membership_id,
            person_id

        FROM memberships

        WHERE term_id = ?

        LIMIT 1
        """,
        (
            archived[
                "term_id"
            ],
        ),
    ).fetchone()


    require(
        active_member
        is not None,

        "Active membership missing.",
    )


    require(
        archived_member
        is not None,

        "Archived membership missing.",
    )


    # ========================================================
    # MEETING
    # ========================================================

    cursor.execute(
        """
        INSERT INTO meetings (
            organizer_membership_id,
            title,
            meeting_date,
            term_id
        )

        VALUES (
            ?,
            'Task 10 Migration Meeting',
            '2099-02-01',
            ?
        )
        """,
        (
            active_member[
                "membership_id"
            ],

            active[
                "term_id"
            ],
        ),
    )


    meeting_id = (
        cursor.lastrowid
    )


    blocked(

        lambda:

            cursor.execute(
                """
                INSERT INTO meeting_attendance (
                    meeting_id,
                    membership_id,
                    attendance_status
                )

                VALUES (
                    ?,
                    ?,
                    'invalid'
                )
                """,
                (
                    meeting_id,

                    active_member[
                        "membership_id"
                    ],
                ),
            ),

        (
            "Invalid meeting attendance "
            "status was allowed."
        ),
    )


    # ========================================================
    # MEMBER NOTE
    # ========================================================

    blocked(

        lambda:

            cursor.execute(
                """
                INSERT INTO member_notes (
                    membership_id,
                    given_by_membership_id,
                    note,
                    note_type
                )

                VALUES (
                    ?,
                    ?,
                    'x',
                    'INVALID'
                )
                """,
                (
                    active_member[
                        "membership_id"
                    ],

                    active_member[
                        "membership_id"
                    ],
                ),
            ),

        (
            "Invalid member note type "
            "was allowed."
        ),
    )


    # ========================================================
    # CERTIFICATE
    # ========================================================

    cursor.execute(
        """
        INSERT INTO certificates (
            name,
            term_id,
            created_by_membership_id
        )

        VALUES (
            'Task 10 Migration Certificate',
            ?,
            ?
        )
        """,
        (
            active[
                "term_id"
            ],

            active_member[
                "membership_id"
            ],
        ),
    )


    certificate_id = (
        cursor.lastrowid
    )


    cursor.execute(
        """
        INSERT INTO certificate_recipients (
            certificate_id,
            person_id
        )

        VALUES (?, ?)
        """,
        (
            certificate_id,

            active_member[
                "person_id"
            ],
        ),
    )


    snapshot = cursor.execute(
        """
        SELECT
            recipient_name_snapshot

        FROM certificate_recipients

        WHERE certificate_id = ?
        """,
        (
            certificate_id,
        ),
    ).fetchone()[
        "recipient_name_snapshot"
    ]


    require(
        snapshot,

        (
            "Certificate recipient "
            "name snapshot failed."
        ),
    )


    # ========================================================
    # SOURCE REFERENCE
    # ========================================================

    cursor.execute(
        """
        INSERT INTO source_references (
            title
        )

        VALUES (
            'Task 10 Migration Source'
        )
        """
    )


    source_id = (
        cursor.lastrowid
    )


    article = cursor.execute(
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

        cursor.execute(
            """
            INSERT INTO scientific_articles (
                article_owner_membership_id,
                title,
                status
            )

            VALUES (
                ?,
                'Task 10 Migration Article',
                'active'
            )
            """,
            (
                active_member[
                    "membership_id"
                ],
            ),
        )


        article_id = (
            cursor.lastrowid
        )


        cursor.execute(
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


    cursor.execute(
        """
        INSERT INTO article_source_references (
            scientific_article_id,
            source_reference_id
        )

        VALUES (?, ?)
        """,
        (
            article_id,
            source_id,
        ),
    )


    source_snapshot = cursor.execute(
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
    ).fetchone()[
        "source_title_snapshot"
    ]


    require(

        source_snapshot
        ==
        "Task 10 Migration Source",

        "Article source snapshot failed.",
    )


    # ========================================================
    # ARCHIVED PROTECTION
    # ========================================================

    blocked(

        lambda:

            cursor.execute(
                """
                INSERT INTO meetings (
                    organizer_membership_id,
                    title,
                    meeting_date,
                    term_id
                )

                VALUES (
                    ?,
                    'Archived Meeting',
                    '2020-01-01',
                    ?
                )
                """,
                (
                    archived_member[
                        "membership_id"
                    ],

                    archived[
                        "term_id"
                    ],
                ),
            ),

        (
            "Archived meeting creation "
            "was allowed."
        ),
    )


    blocked(

        lambda:

            cursor.execute(
                """
                INSERT INTO certificates (
                    name,
                    term_id,
                    created_by_membership_id
                )

                VALUES (
                    'Archived Certificate',
                    ?,
                    ?
                )
                """,
                (
                    archived[
                        "term_id"
                    ],

                    archived_member[
                        "membership_id"
                    ],
                ),
            ),

        (
            "Archived certificate creation "
            "was allowed."
        ),
    )


    # ========================================================
    # HEALTH
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


    require(
        integrity == "ok",

        "Integrity check failed.",
    )


    require(
        not foreign_keys,

        "Foreign key check failed.",
    )


    conn.rollback()

    conn.close()


    # ========================================================
    # IDEMPOTENCY
    # ========================================================

    migrate_database(
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

        "Second migration integrity failed.",
    )


    require(
        not foreign_keys_second,

        (
            "Second migration "
            "foreign keys failed."
        ),
    )


    print(
        "========================================"
    )

    print(
        "CLUB RECORDS MIGRATION TEST SUCCESSFUL"
    )

    print(
        "========================================"
    )


    print(
        "Meeting mandate model: OK"
    )

    print(
        "Attendance constraints: OK"
    )

    print(
        "Member note types: OK"
    )

    print(
        "Annual schedule metadata: OK"
    )

    print(
        "Certificate history snapshots: OK"
    )

    print(
        "Article source history snapshots: OK"
    )

    print(
        "Archived records protected: OK"
    )

    print(
        "Migration idempotency: OK"
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