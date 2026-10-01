import sqlite3
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = DATABASE_DIR / "rsclub.db"

BACKUP_PATH = (
    DATABASE_DIR
    / "rsclub_backup_before_records_v1.db"
)


ATTENDANCE_STATUSES = {
    "present",
    "absent",
    "late",
    "excused",
}

NOTE_TYPES = {
    "REMARK",
    "WARNING",
    "SANCTION",
    "POSITIVE",
}


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


def create_backup(
    source_path,
    backup_path,
):

    if backup_path.exists():

        backup_path.unlink()


    source = connect(
        source_path
    )

    destination = sqlite3.connect(
        backup_path
    )


    try:

        source.backup(
            destination
        )

    finally:

        destination.close()
        source.close()


def columns(
    cursor,
    table_name,
):

    return {

        row["name"]

        for row in cursor.execute(
            f'''
            PRAGMA table_info(
                "{table_name}"
            )
            '''
        ).fetchall()

    }


def add_column_if_missing(
    cursor,
    table_name,
    column_name,
    ddl,
):

    if column_name not in columns(
        cursor,
        table_name,
    ):

        cursor.execute(
            f'''
            ALTER TABLE "{table_name}"
            ADD COLUMN
                {column_name}
                {ddl}
            '''
        )


def create_trigger(
    cursor,
    name,
    sql,
):

    cursor.execute(
        f"DROP TRIGGER IF EXISTS {name}"
    )

    cursor.execute(
        sql
    )


def migrate_database(
    db_path=DATABASE_PATH,
    create_backup_file=True,
    verbose=True,
):

    db_path = Path(
        db_path
    )


    if not db_path.exists():

        raise FileNotFoundError(
            f"Database not found: {db_path}"
        )


    # ========================================================
    # BACKUP
    # ========================================================

    if create_backup_file:

        create_backup(
            db_path,
            BACKUP_PATH,
        )


        if verbose:

            print(
                "Backup created:",
                BACKUP_PATH.name,
            )


    conn = connect(
        db_path
    )

    cursor = conn.cursor()


    try:

        conn.execute(
            "BEGIN IMMEDIATE"
        )


        # ====================================================
        # MEETINGS
        # ====================================================

        add_column_if_missing(
            cursor,
            "meetings",
            "term_id",
            (
                "INTEGER "
                "REFERENCES terms(term_id)"
            ),
        )


        # Existing meetings inherit the term
        # of their organizer.

        cursor.execute(
            """
            UPDATE meetings

            SET term_id = (

                SELECT
                    memberships.term_id

                FROM memberships

                WHERE
                    memberships.membership_id =
                    meetings.organizer_membership_id
            )

            WHERE term_id IS NULL
            """
        )


        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_meetings_term_date

            ON meetings(
                term_id,
                meeting_date,
                start_time
            )
            """
        )


        create_trigger(
            cursor,

            "trg_meetings_term_required_insert",

            """
            CREATE TRIGGER
                trg_meetings_term_required_insert

            BEFORE INSERT
            ON meetings

            FOR EACH ROW

            WHEN NEW.term_id IS NULL

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Meeting term is required'
                );

            END
            """,
        )


        create_trigger(
            cursor,

            "trg_meetings_term_required_update",

            """
            CREATE TRIGGER
                trg_meetings_term_required_update

            BEFORE UPDATE OF term_id
            ON meetings

            FOR EACH ROW

            WHEN NEW.term_id IS NULL

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Meeting term is required'
                );

            END
            """,
        )


        # Organizer must belong to same term.

        create_trigger(
            cursor,

            "trg_meetings_organizer_same_term_insert",

            """
            CREATE TRIGGER
                trg_meetings_organizer_same_term_insert

            BEFORE INSERT
            ON meetings

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM memberships

                WHERE
                    membership_id =
                    NEW.organizer_membership_id

                  AND term_id =
                      NEW.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Meeting organizer must belong to the same mandate'
                );

            END
            """,
        )


        create_trigger(
            cursor,

            "trg_meetings_organizer_same_term_update",

            """
            CREATE TRIGGER
                trg_meetings_organizer_same_term_update

            BEFORE UPDATE OF
                organizer_membership_id,
                term_id

            ON meetings

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM memberships

                WHERE
                    membership_id =
                    NEW.organizer_membership_id

                  AND term_id =
                      NEW.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Meeting organizer must belong to the same mandate'
                );

            END
            """,
        )


        # ====================================================
        # MEETING HISTORICAL IMMUTABILITY
        # ====================================================

        create_trigger(
            cursor,

            "trg_archived_meetings_no_insert",

            """
            CREATE TRIGGER
                trg_archived_meetings_no_insert

            BEFORE INSERT
            ON meetings

            FOR EACH ROW

            WHEN EXISTS (

                SELECT 1

                FROM terms

                WHERE
                    term_id =
                    NEW.term_id

                  AND status =
                      'ARCHIVED'
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'HISTORICAL_IMMUTABILITY: archived meeting cannot be created'
                );

            END
            """,
        )


        create_trigger(
            cursor,

            "trg_archived_meetings_no_update",

            """
            CREATE TRIGGER
                trg_archived_meetings_no_update

            BEFORE UPDATE
            ON meetings

            FOR EACH ROW

            WHEN EXISTS (

                SELECT 1

                FROM terms

                WHERE
                    term_id IN (
                        OLD.term_id,
                        NEW.term_id
                    )

                  AND status =
                      'ARCHIVED'
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'HISTORICAL_IMMUTABILITY: archived meeting cannot be modified'
                );

            END
            """,
        )


        create_trigger(
            cursor,

            "trg_archived_meetings_no_delete",

            """
            CREATE TRIGGER
                trg_archived_meetings_no_delete

            BEFORE DELETE
            ON meetings

            FOR EACH ROW

            WHEN EXISTS (

                SELECT 1

                FROM terms

                WHERE
                    term_id =
                    OLD.term_id

                  AND status =
                      'ARCHIVED'
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'HISTORICAL_IMMUTABILITY: archived meeting cannot be deleted'
                );

            END
            """,
        )


        # ====================================================
        # ATTENDANCE VALIDATION
        # ====================================================

        for table in (

            "meeting_attendance",

            "event_attendance",

            "training_attendance",

        ):

            create_trigger(
                cursor,

                f"trg_{table}_status_insert",

                f"""
                CREATE TRIGGER
                    trg_{table}_status_insert

                BEFORE INSERT
                ON {table}

                FOR EACH ROW

                WHEN LOWER(
                    NEW.attendance_status
                )
                NOT IN (
                    'present',
                    'absent',
                    'late',
                    'excused'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'Invalid attendance status'
                    );

                END
                """,
            )


            create_trigger(
                cursor,

                f"trg_{table}_status_update",

                f"""
                CREATE TRIGGER
                    trg_{table}_status_update

                BEFORE UPDATE OF
                    attendance_status

                ON {table}

                FOR EACH ROW

                WHEN LOWER(
                    NEW.attendance_status
                )
                NOT IN (
                    'present',
                    'absent',
                    'late',
                    'excused'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'Invalid attendance status'
                    );

                END
                """,
            )


        # ====================================================
        # MEETING ATTENDANCE SAME TERM
        # ====================================================

        create_trigger(
            cursor,

            "trg_meeting_attendance_same_term_insert",

            """
            CREATE TRIGGER
                trg_meeting_attendance_same_term_insert

            BEFORE INSERT
            ON meeting_attendance

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM meetings

                JOIN memberships

                    ON memberships.membership_id =
                       NEW.membership_id

                WHERE
                    meetings.meeting_id =
                    NEW.meeting_id

                  AND memberships.term_id =
                      meetings.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Meeting attendance member must belong to the meeting mandate'
                );

            END
            """,
        )


        create_trigger(
            cursor,

            "trg_meeting_attendance_same_term_update",

            """
            CREATE TRIGGER
                trg_meeting_attendance_same_term_update

            BEFORE UPDATE OF
                meeting_id,
                membership_id

            ON meeting_attendance

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM meetings

                JOIN memberships

                    ON memberships.membership_id =
                       NEW.membership_id

                WHERE
                    meetings.meeting_id =
                    NEW.meeting_id

                  AND memberships.term_id =
                      meetings.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Meeting attendance member must belong to the meeting mandate'
                );

            END
            """,
        )


        for event in (
            "INSERT",
            "DELETE",
        ):

            alias = (
                "NEW"
                if event == "INSERT"
                else "OLD"
            )


            create_trigger(
                cursor,

                (
                    "trg_archived_"
                    "meeting_attendance_"
                    f"{event.lower()}"
                ),

                f"""
                CREATE TRIGGER
                    trg_archived_meeting_attendance_{event.lower()}

                BEFORE {event}
                ON meeting_attendance

                FOR EACH ROW

                WHEN EXISTS (

                    SELECT 1

                    FROM meetings

                    JOIN terms

                        ON terms.term_id =
                           meetings.term_id

                    WHERE
                        meetings.meeting_id =
                        {alias}.meeting_id

                      AND terms.status =
                          'ARCHIVED'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'HISTORICAL_IMMUTABILITY: archived meeting attendance cannot be modified'
                    );

                END
                """,
            )


        create_trigger(
            cursor,

            "trg_archived_meeting_attendance_update",

            """
            CREATE TRIGGER
                trg_archived_meeting_attendance_update

            BEFORE UPDATE
            ON meeting_attendance

            FOR EACH ROW

            WHEN EXISTS (

                SELECT 1

                FROM meetings

                JOIN terms

                    ON terms.term_id =
                       meetings.term_id

                WHERE
                    meetings.meeting_id
                    IN (
                        OLD.meeting_id,
                        NEW.meeting_id
                    )

                  AND terms.status =
                      'ARCHIVED'
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'HISTORICAL_IMMUTABILITY: archived meeting attendance cannot be modified'
                );

            END
            """,
        )


        # ====================================================
        # EVENT ATTENDANCE SAME TERM
        # ====================================================

        create_trigger(
            cursor,

            "trg_event_attendance_same_term_insert",

            """
            CREATE TRIGGER
                trg_event_attendance_same_term_insert

            BEFORE INSERT
            ON event_attendance

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM events

                JOIN memberships

                    ON memberships.membership_id =
                       NEW.membership_id

                WHERE
                    events.event_id =
                    NEW.event_id

                  AND memberships.term_id =
                      events.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Event attendance member must belong to the event mandate'
                );

            END
            """,
        )


        create_trigger(
            cursor,

            "trg_event_attendance_same_term_update",

            """
            CREATE TRIGGER
                trg_event_attendance_same_term_update

            BEFORE UPDATE OF
                event_id,
                membership_id

            ON event_attendance

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM events

                JOIN memberships

                    ON memberships.membership_id =
                       NEW.membership_id

                WHERE
                    events.event_id =
                    NEW.event_id

                  AND memberships.term_id =
                      events.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Event attendance member must belong to the event mandate'
                );

            END
            """,
        )


        # ====================================================
        # TRAINING ATTENDANCE SAME TERM
        # ====================================================

        create_trigger(
            cursor,

            "trg_training_attendance_same_term_insert",

            """
            CREATE TRIGGER
                trg_training_attendance_same_term_insert

            BEFORE INSERT
            ON training_attendance

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM training_terms

                JOIN memberships

                    ON memberships.membership_id =
                       NEW.membership_id

                WHERE
                    training_terms.training_id =
                    NEW.training_id

                  AND memberships.term_id =
                      training_terms.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Training attendance member must belong to the training mandate'
                );

            END
            """,
        )


        create_trigger(
            cursor,

            "trg_training_attendance_same_term_update",

            """
            CREATE TRIGGER
                trg_training_attendance_same_term_update

            BEFORE UPDATE OF
                training_id,
                membership_id

            ON training_attendance

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM training_terms

                JOIN memberships

                    ON memberships.membership_id =
                       NEW.membership_id

                WHERE
                    training_terms.training_id =
                    NEW.training_id

                  AND memberships.term_id =
                      training_terms.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Training attendance member must belong to the training mandate'
                );

            END
            """,
        )


        # ====================================================
        # MEMBER NOTES
        # ====================================================

        add_column_if_missing(
            cursor,
            "member_notes",
            "note_type",
            (
                "TEXT NOT NULL "
                "DEFAULT 'REMARK'"
            ),
        )


        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_member_notes_membership_created

            ON member_notes(
                membership_id,
                created_at
            )
            """
        )


        for event in (
            "INSERT",
            "UPDATE",
        ):

            create_trigger(
                cursor,

                (
                    "trg_member_notes_type_"
                    f"{event.lower()}"
                ),

                f"""
                CREATE TRIGGER
                    trg_member_notes_type_{event.lower()}

                BEFORE {event}
                ON member_notes

                FOR EACH ROW

                WHEN UPPER(
                    NEW.note_type
                )
                NOT IN (
                    'REMARK',
                    'WARNING',
                    'SANCTION',
                    'POSITIVE'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'Invalid member note type'
                    );

                END
                """,
            )


        create_trigger(
            cursor,

            "trg_member_notes_same_term_insert",

            """
            CREATE TRIGGER
                trg_member_notes_same_term_insert

            BEFORE INSERT
            ON member_notes

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM memberships
                    AS target

                JOIN memberships
                    AS giver

                    ON giver.membership_id =
                       NEW.given_by_membership_id

                WHERE
                    target.membership_id =
                    NEW.membership_id

                  AND target.term_id =
                      giver.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Member note author and target must belong to the same mandate'
                );

            END
            """,
        )


        create_trigger(
            cursor,

            "trg_member_notes_same_term_update",

            """
            CREATE TRIGGER
                trg_member_notes_same_term_update

            BEFORE UPDATE OF
                membership_id,
                given_by_membership_id

            ON member_notes

            FOR EACH ROW

            WHEN NOT EXISTS (

                SELECT 1

                FROM memberships
                    AS target

                JOIN memberships
                    AS giver

                    ON giver.membership_id =
                       NEW.given_by_membership_id

                WHERE
                    target.membership_id =
                    NEW.membership_id

                  AND target.term_id =
                      giver.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Member note author and target must belong to the same mandate'
                );

            END
            """,
        )


        for event in (
            "INSERT",
            "DELETE",
        ):

            alias = (
                "NEW"
                if event == "INSERT"
                else "OLD"
            )


            create_trigger(
                cursor,

                (
                    "trg_archived_"
                    "member_notes_"
                    f"{event.lower()}"
                ),

                f"""
                CREATE TRIGGER
                    trg_archived_member_notes_{event.lower()}

                BEFORE {event}
                ON member_notes

                FOR EACH ROW

                WHEN EXISTS (

                    SELECT 1

                    FROM memberships

                    JOIN terms

                        ON terms.term_id =
                           memberships.term_id

                    WHERE
                        memberships.membership_id =
                        {alias}.membership_id

                      AND terms.status =
                          'ARCHIVED'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'HISTORICAL_IMMUTABILITY: archived member note cannot be modified'
                    );

                END
                """,
            )


        create_trigger(
            cursor,

            "trg_archived_member_notes_update",

            """
            CREATE TRIGGER
                trg_archived_member_notes_update

            BEFORE UPDATE
            ON member_notes

            FOR EACH ROW

            WHEN EXISTS (

                SELECT 1

                FROM memberships

                JOIN terms

                    ON terms.term_id =
                       memberships.term_id

                WHERE
                    memberships.membership_id
                    IN (
                        OLD.membership_id,
                        NEW.membership_id
                    )

                  AND terms.status =
                      'ARCHIVED'
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'HISTORICAL_IMMUTABILITY: archived member note cannot be modified'
                );

            END
            """,
        )


        # ====================================================
        # ANNUAL SCHEDULE
        # ====================================================

        add_column_if_missing(
            cursor,
            "annual_schedule",
            "original_filename",
            "TEXT",
        )


        # ====================================================
        # CERTIFICATES
        # ====================================================

        add_column_if_missing(
            cursor,
            "certificates",
            "term_id",
            (
                "INTEGER "
                "REFERENCES terms(term_id)"
            ),
        )


        add_column_if_missing(
            cursor,
            "certificates",
            "created_by_membership_id",
            (
                "INTEGER "
                "REFERENCES memberships(membership_id)"
            ),
        )


        add_column_if_missing(
            cursor,
            "certificates",
            "original_filename",
            "TEXT",
        )


        add_column_if_missing(
            cursor,
            "certificate_recipients",
            "recipient_name_snapshot",
            "TEXT",
        )


        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_certificates_term_date

            ON certificates(
                term_id,
                issued_date,
                certificate_id
            )
            """
        )


        create_trigger(
            cursor,

            "trg_certificates_term_required_insert",

            """
            CREATE TRIGGER
                trg_certificates_term_required_insert

            BEFORE INSERT
            ON certificates

            FOR EACH ROW

            WHEN NEW.term_id IS NULL

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Certificate mandate is required'
                );

            END
            """,
        )


        create_trigger(
            cursor,

            "trg_certificates_creator_same_term_insert",

            """
            CREATE TRIGGER
                trg_certificates_creator_same_term_insert

            BEFORE INSERT
            ON certificates

            FOR EACH ROW

            WHEN
                NEW.created_by_membership_id
                IS NOT NULL

            AND NOT EXISTS (

                SELECT 1

                FROM memberships

                WHERE
                    membership_id =
                    NEW.created_by_membership_id

                  AND term_id =
                      NEW.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Certificate creator must belong to the same mandate'
                );

            END
            """,
        )


        create_trigger(
            cursor,

            "trg_certificates_creator_same_term_update",

            """
            CREATE TRIGGER
                trg_certificates_creator_same_term_update

            BEFORE UPDATE OF
                term_id,
                created_by_membership_id

            ON certificates

            FOR EACH ROW

            WHEN
                NEW.created_by_membership_id
                IS NOT NULL

            AND NOT EXISTS (

                SELECT 1

                FROM memberships

                WHERE
                    membership_id =
                    NEW.created_by_membership_id

                  AND term_id =
                      NEW.term_id
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'Certificate creator must belong to the same mandate'
                );

            END
            """,
        )


        for event in (
            "INSERT",
            "DELETE",
        ):

            alias = (
                "NEW"
                if event == "INSERT"
                else "OLD"
            )


            create_trigger(
                cursor,

                (
                    "trg_archived_"
                    "certificates_"
                    f"{event.lower()}"
                ),

                f"""
                CREATE TRIGGER
                    trg_archived_certificates_{event.lower()}

                BEFORE {event}
                ON certificates

                FOR EACH ROW

                WHEN EXISTS (

                    SELECT 1

                    FROM terms

                    WHERE
                        term_id =
                        {alias}.term_id

                      AND status =
                          'ARCHIVED'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'HISTORICAL_IMMUTABILITY: archived certificate cannot be modified'
                    );

                END
                """,
            )


        create_trigger(
            cursor,

            "trg_archived_certificates_update",

            """
            CREATE TRIGGER
                trg_archived_certificates_update

            BEFORE UPDATE
            ON certificates

            FOR EACH ROW

            WHEN EXISTS (

                SELECT 1

                FROM terms

                WHERE
                    term_id IN (
                        OLD.term_id,
                        NEW.term_id
                    )

                  AND status =
                      'ARCHIVED'
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'HISTORICAL_IMMUTABILITY: archived certificate cannot be modified'
                );

            END
            """,
        )


        # Recipient name snapshot.

        create_trigger(
            cursor,

            "trg_certificate_recipient_snapshot_insert",

            """
            CREATE TRIGGER
                trg_certificate_recipient_snapshot_insert

            AFTER INSERT
            ON certificate_recipients

            FOR EACH ROW

            BEGIN

                UPDATE certificate_recipients

                SET
                    recipient_name_snapshot = (

                        SELECT
                            TRIM(
                                first_name
                                || ' '
                                || last_name
                            )

                        FROM people

                        WHERE
                            person_id =
                            NEW.person_id
                    )

                WHERE
                    certificate_recipient_id =
                    NEW.certificate_recipient_id;

            END
            """,
        )


        for event in (
            "INSERT",
            "DELETE",
        ):

            alias = (
                "NEW"
                if event == "INSERT"
                else "OLD"
            )


            create_trigger(
                cursor,

                (
                    "trg_archived_"
                    "certificate_recipients_"
                    f"{event.lower()}"
                ),

                f"""
                CREATE TRIGGER
                    trg_archived_certificate_recipients_{event.lower()}

                BEFORE {event}
                ON certificate_recipients

                FOR EACH ROW

                WHEN EXISTS (

                    SELECT 1

                    FROM certificates

                    JOIN terms

                        ON terms.term_id =
                           certificates.term_id

                    WHERE
                        certificates.certificate_id =
                        {alias}.certificate_id

                      AND terms.status =
                          'ARCHIVED'
                )

                BEGIN

                    SELECT RAISE(
                        ABORT,
                        'HISTORICAL_IMMUTABILITY: archived certificate recipients cannot be modified'
                    );

                END
                """,
            )


        create_trigger(
            cursor,

            "trg_archived_certificate_recipients_update",

            """
            CREATE TRIGGER
                trg_archived_certificate_recipients_update

            BEFORE UPDATE
            ON certificate_recipients

            FOR EACH ROW

            WHEN EXISTS (

                SELECT 1

                FROM certificates

                JOIN terms

                    ON terms.term_id =
                       certificates.term_id

                WHERE
                    certificates.certificate_id
                    IN (
                        OLD.certificate_id,
                        NEW.certificate_id
                    )

                  AND terms.status =
                      'ARCHIVED'
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'HISTORICAL_IMMUTABILITY: archived certificate recipients cannot be modified'
                );

            END
            """,
        )


        # ====================================================
        # ARTICLE SOURCE SNAPSHOTS
        # ====================================================

        source_snapshot_columns = {

            "source_title_snapshot":
                "TEXT",

            "source_authors_snapshot":
                "TEXT",

            "source_type_snapshot":
                "TEXT",

            "source_publication_year_snapshot":
                "INTEGER",

            "source_url_snapshot":
                "TEXT",

            "source_doi_snapshot":
                "TEXT",
        }


        for (
            column_name,
            ddl,
        ) in source_snapshot_columns.items():

            add_column_if_missing(
                cursor,
                "article_source_references",
                column_name,
                ddl,
            )


        # Existing references receive snapshots.

        cursor.execute(
            """
            UPDATE article_source_references

            SET

                source_title_snapshot = (

                    SELECT title

                    FROM source_references

                    WHERE
                        source_reference_id =
                        article_source_references.source_reference_id
                ),


                source_authors_snapshot = (

                    SELECT authors

                    FROM source_references

                    WHERE
                        source_reference_id =
                        article_source_references.source_reference_id
                ),


                source_type_snapshot = (

                    SELECT source_type

                    FROM source_references

                    WHERE
                        source_reference_id =
                        article_source_references.source_reference_id
                ),


                source_publication_year_snapshot = (

                    SELECT publication_year

                    FROM source_references

                    WHERE
                        source_reference_id =
                        article_source_references.source_reference_id
                ),


                source_url_snapshot = (

                    SELECT url

                    FROM source_references

                    WHERE
                        source_reference_id =
                        article_source_references.source_reference_id
                ),


                source_doi_snapshot = (

                    SELECT doi

                    FROM source_references

                    WHERE
                        source_reference_id =
                        article_source_references.source_reference_id
                )


            WHERE
                source_title_snapshot
                IS NULL
            """
        )


        create_trigger(
            cursor,

            "trg_article_source_snapshot_insert",

            """
            CREATE TRIGGER
                trg_article_source_snapshot_insert

            AFTER INSERT
            ON article_source_references

            FOR EACH ROW

            BEGIN

                UPDATE article_source_references

                SET

                    source_title_snapshot = (

                        SELECT title

                        FROM source_references

                        WHERE
                            source_reference_id =
                            NEW.source_reference_id
                    ),


                    source_authors_snapshot = (

                        SELECT authors

                        FROM source_references

                        WHERE
                            source_reference_id =
                            NEW.source_reference_id
                    ),


                    source_type_snapshot = (

                        SELECT source_type

                        FROM source_references

                        WHERE
                            source_reference_id =
                            NEW.source_reference_id
                    ),


                    source_publication_year_snapshot = (

                        SELECT publication_year

                        FROM source_references

                        WHERE
                            source_reference_id =
                            NEW.source_reference_id
                    ),


                    source_url_snapshot = (

                        SELECT url

                        FROM source_references

                        WHERE
                            source_reference_id =
                            NEW.source_reference_id
                    ),


                    source_doi_snapshot = (

                        SELECT doi

                        FROM source_references

                        WHERE
                            source_reference_id =
                            NEW.source_reference_id
                    )


                WHERE
                    article_source_reference_id =
                    NEW.article_source_reference_id;

            END
            """,
        )


        # Source updates refresh only non-archived articles.

        create_trigger(
            cursor,

            "trg_source_reference_snapshot_sync",

            """
            CREATE TRIGGER
                trg_source_reference_snapshot_sync

            AFTER UPDATE OF
                title,
                authors,
                source_type,
                publication_year,
                url,
                doi

            ON source_references

            FOR EACH ROW

            BEGIN

                UPDATE article_source_references

                SET

                    source_title_snapshot =
                        NEW.title,

                    source_authors_snapshot =
                        NEW.authors,

                    source_type_snapshot =
                        NEW.source_type,

                    source_publication_year_snapshot =
                        NEW.publication_year,

                    source_url_snapshot =
                        NEW.url,

                    source_doi_snapshot =
                        NEW.doi


                WHERE
                    source_reference_id =
                    NEW.source_reference_id

                  AND scientific_article_id
                      IN (

                        SELECT
                            article_terms.scientific_article_id

                        FROM article_terms

                        JOIN terms

                            ON terms.term_id =
                               article_terms.term_id

                        WHERE
                            terms.status !=
                            'ARCHIVED'
                      );

            END
            """,
        )


        create_trigger(
            cursor,

            "trg_source_reference_delete_archived_guard",

            """
            CREATE TRIGGER
                trg_source_reference_delete_archived_guard

            BEFORE DELETE
            ON source_references

            FOR EACH ROW

            WHEN EXISTS (

                SELECT 1

                FROM article_source_references

                JOIN article_terms

                    ON article_terms.scientific_article_id =
                       article_source_references.scientific_article_id

                JOIN terms

                    ON terms.term_id =
                       article_terms.term_id

                WHERE
                    article_source_references.source_reference_id =
                    OLD.source_reference_id

                  AND terms.status =
                      'ARCHIVED'
            )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'HISTORICAL_IMMUTABILITY: source used by archived article cannot be deleted'
                );

            END
            """,
        )


        # ====================================================
        # HEALTH
        # ====================================================

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

            raise RuntimeError(
                "Integrity check failed: "
                f"{integrity}"
            )


        if foreign_keys:

            raise RuntimeError(
                "Foreign key check failed: "
                f"{foreign_keys}"
            )


        conn.commit()


        if verbose:

            print()

            print(
                "========================================"
            )

            print(
                "CLUB RECORDS MIGRATION SUCCESSFUL"
            )

            print(
                "========================================"
            )


            print(
                "Meetings + mandate protection: OK"
            )

            print(
                "Attendance validation: OK"
            )

            print(
                "Member notes model: OK"
            )

            print(
                "Annual schedule metadata: OK"
            )

            print(
                "Certificates + recipients snapshots: OK"
            )

            print(
                "Article source snapshots: OK"
            )

            print(
                "Integrity check:",
                integrity,
            )

            print(
                "Foreign key check:",
                foreign_keys,
            )


        return {

            "integrity":
                integrity,

            "foreign_keys":
                foreign_keys,
        }


    except Exception:

        conn.rollback()

        raise


    finally:

        conn.close()


if __name__ == "__main__":

    migrate_database()