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
    / "rsclub_backup_before_history_immutability.db"
)


SNAPSHOT_COLUMNS = {

    "organization_name_snapshot":
        "TEXT",

    "organization_type_snapshot":
        "TEXT",

    "organization_description_snapshot":
        "TEXT",

    "organization_address_snapshot":
        "TEXT",

    "organization_website_snapshot":
        "TEXT",

    "organization_email_snapshot":
        "TEXT",

    "organization_phone_snapshot":
        "TEXT",

    "organization_logo_path_snapshot":
        "TEXT",

    "organization_original_logo_filename_snapshot":
        "TEXT",
}


# ============================================================
# CONNECTION
# ============================================================

def connect(
    path,
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


# ============================================================
# GENERIC TRIGGER
# ============================================================

def create_guard_trigger(
    cursor,
    name,
    table,
    event,
    when_sql,
    message,
):

    cursor.execute(
        f"""
        CREATE TRIGGER IF NOT EXISTS
            {name}

        BEFORE {event}

        ON {table}

        FOR EACH ROW

        WHEN {when_sql}

        BEGIN

            SELECT RAISE(
                ABORT,
                '{message}'
            );

        END
        """
    )


# ============================================================
# SQL CONDITIONS
# ============================================================

def archived_term(
    term_expression,
):

    return (

        "EXISTS ("

        "SELECT 1 "
        "FROM terms "

        f"WHERE term_id = "
        f"{term_expression} "

        "AND status = "
        "'ARCHIVED'"

        ")"
    )


def parent_has_archived_term(
    bridge_table,
    parent_column,
    parent_expression,
):

    return (

        "EXISTS ("

        f"SELECT 1 "
        f"FROM {bridge_table} "

        "JOIN terms "
        f"ON {bridge_table}.term_id = "
        "terms.term_id "

        f"WHERE {bridge_table}."
        f"{parent_column} = "
        f"{parent_expression} "

        "AND terms.status = "
        "'ARCHIVED'"

        ")"
    )


def event_is_archived(
    event_expression,
):

    return (

        "EXISTS ("

        "SELECT 1 "
        "FROM events "

        "JOIN terms "
        "ON events.term_id = "
        "terms.term_id "

        "WHERE events.event_id = "
        f"{event_expression} "

        "AND terms.status = "
        "'ARCHIVED'"

        ")"
    )


# ============================================================
# VERIFY CURRENT MULTI-TERM DATA
# ============================================================

def assert_no_shared_multi_term_rows(
    cursor,
):

    checks = (

        (
            "project_terms",
            "project_id",
        ),

        (
            "article_terms",
            "scientific_article_id",
        ),

        (
            "training_terms",
            "training_id",
        ),

    )


    for (
        table,
        column,
    ) in checks:

        duplicate = (
            cursor.execute(
                f"""
                SELECT
                    {column},

                    COUNT(*)
                        AS total

                FROM {table}

                GROUP BY
                    {column}

                HAVING
                    COUNT(*) > 1

                LIMIT 1
                """
            ).fetchone()
        )


        if duplicate is not None:

            raise RuntimeError(

                f"{table} already contains "
                "a record shared across "
                "multiple mandates "

                f"({column}="
                f"{duplicate[column]}). "

                "Resolve it before enabling "
                "historical immutability."
            )


    duplicate_relation = (
        cursor.execute(
            """
            SELECT
                organization_id,

                term_id,

                COUNT(*)
                    AS total

            FROM organization_relations

            GROUP BY
                organization_id,
                term_id

            HAVING
                COUNT(*) > 1

            LIMIT 1
            """
        ).fetchone()
    )


    if duplicate_relation is not None:

        raise RuntimeError(

            "Duplicate organization "
            "relationship found for "
            "the same organization "
            "and mandate."
        )


# ============================================================
# ORGANIZATION SNAPSHOT COLUMNS
# ============================================================

def add_organization_snapshot_columns(
    cursor,
):

    existing_columns = {

        row[
            "name"
        ]

        for row
        in cursor.execute(
            """
            PRAGMA table_info(
                "organization_relations"
            )
            """
        ).fetchall()

    }


    for (
        column_name,
        column_type,
    ) in SNAPSHOT_COLUMNS.items():

        if (
            column_name
            not in existing_columns
        ):

            cursor.execute(
                f"""
                ALTER TABLE
                    organization_relations

                ADD COLUMN
                    {column_name}
                    {column_type}
                """
            )


# ============================================================
# BACKFILL ORGANIZATION SNAPSHOTS
# ============================================================

def backfill_organization_snapshots(
    cursor,
):

    cursor.execute(
        """
        UPDATE organization_relations

        SET

            organization_name_snapshot = (

                SELECT name

                FROM organizations

                WHERE
                    organizations.organization_id =
                    organization_relations.organization_id
            ),


            organization_type_snapshot = (

                SELECT organization_type

                FROM organizations

                WHERE
                    organizations.organization_id =
                    organization_relations.organization_id
            ),


            organization_description_snapshot = (

                SELECT description

                FROM organizations

                WHERE
                    organizations.organization_id =
                    organization_relations.organization_id
            ),


            organization_address_snapshot = (

                SELECT address

                FROM organizations

                WHERE
                    organizations.organization_id =
                    organization_relations.organization_id
            ),


            organization_website_snapshot = (

                SELECT website

                FROM organizations

                WHERE
                    organizations.organization_id =
                    organization_relations.organization_id
            ),


            organization_email_snapshot = (

                SELECT email

                FROM organizations

                WHERE
                    organizations.organization_id =
                    organization_relations.organization_id
            ),


            organization_phone_snapshot = (

                SELECT phone

                FROM organizations

                WHERE
                    organizations.organization_id =
                    organization_relations.organization_id
            ),


            organization_logo_path_snapshot = (

                SELECT logo_path

                FROM organizations

                WHERE
                    organizations.organization_id =
                    organization_relations.organization_id
            ),


            organization_original_logo_filename_snapshot = (

                SELECT original_logo_filename

                FROM organizations

                WHERE
                    organizations.organization_id =
                    organization_relations.organization_id
            )


        WHERE
            organization_name_snapshot
            IS NULL
        """
    )


# ============================================================
# ORGANIZATION SNAPSHOT TRIGGERS
# ============================================================

def create_snapshot_triggers(
    cursor,
):

    # ========================================================
    # NEW RELATION
    # ========================================================

    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS
            trg_organization_relation_snapshot_insert

        AFTER INSERT

        ON organization_relations

        FOR EACH ROW

        BEGIN

            UPDATE organization_relations

            SET

                organization_name_snapshot = (

                    SELECT name

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                ),


                organization_type_snapshot = (

                    SELECT organization_type

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                ),


                organization_description_snapshot = (

                    SELECT description

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                ),


                organization_address_snapshot = (

                    SELECT address

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                ),


                organization_website_snapshot = (

                    SELECT website

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                ),


                organization_email_snapshot = (

                    SELECT email

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                ),


                organization_phone_snapshot = (

                    SELECT phone

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                ),


                organization_logo_path_snapshot = (

                    SELECT logo_path

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                ),


                organization_original_logo_filename_snapshot = (

                    SELECT original_logo_filename

                    FROM organizations

                    WHERE organization_id =
                          NEW.organization_id
                )


            WHERE
                organization_relation_id =
                NEW.organization_relation_id;

        END
        """
    )


    # ========================================================
    # CURRENT ORGANIZATION CHANGES
    #
    # ACTIVE / DRAFT snapshots follow current metadata.
    #
    # ARCHIVED snapshots stay frozen forever.
    # ========================================================

    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS
            trg_organization_current_snapshot_sync

        AFTER UPDATE OF

            name,

            organization_type,

            description,

            address,

            website,

            email,

            phone,

            logo_path,

            original_logo_filename

        ON organizations

        FOR EACH ROW

        BEGIN

            UPDATE organization_relations

            SET

                organization_name_snapshot =
                    NEW.name,

                organization_type_snapshot =
                    NEW.organization_type,

                organization_description_snapshot =
                    NEW.description,

                organization_address_snapshot =
                    NEW.address,

                organization_website_snapshot =
                    NEW.website,

                organization_email_snapshot =
                    NEW.email,

                organization_phone_snapshot =
                    NEW.phone,

                organization_logo_path_snapshot =
                    NEW.logo_path,

                organization_original_logo_filename_snapshot =
                    NEW.original_logo_filename


            WHERE
                organization_id =
                NEW.organization_id

              AND term_id IN (

                    SELECT term_id

                    FROM terms

                    WHERE status !=
                          'ARCHIVED'
              );

        END
        """
    )


# ============================================================
# TERM + MEMBERSHIP PROTECTION
# ============================================================

def create_term_and_membership_guards(
    cursor,
):

    create_guard_trigger(

        cursor,

        "trg_archived_terms_no_update",

        "terms",

        "UPDATE",

        "OLD.status = 'ARCHIVED'",

        (
            "HISTORICAL_IMMUTABILITY: "
            "archived mandate cannot be modified"
        ),
    )


    create_guard_trigger(

        cursor,

        "trg_archived_terms_no_delete",

        "terms",

        "DELETE",

        "OLD.status = 'ARCHIVED'",

        (
            "HISTORICAL_IMMUTABILITY: "
            "archived mandate cannot be deleted"
        ),
    )


    create_guard_trigger(

        cursor,

        "trg_archived_memberships_no_insert",

        "memberships",

        "INSERT",

        archived_term(
            "NEW.term_id"
        ),

        (
            "HISTORICAL_IMMUTABILITY: "
            "archived membership cannot be created"
        ),
    )


    create_guard_trigger(

        cursor,

        "trg_archived_memberships_no_update",

        "memberships",

        "UPDATE",

        (
            f"{archived_term('OLD.term_id')} "
            "OR "
            f"{archived_term('NEW.term_id')}"
        ),

        (
            "HISTORICAL_IMMUTABILITY: "
            "archived membership cannot be modified"
        ),
    )


    create_guard_trigger(

        cursor,

        "trg_archived_memberships_no_delete",

        "memberships",

        "DELETE",

        archived_term(
            "OLD.term_id"
        ),

        (
            "HISTORICAL_IMMUTABILITY: "
            "archived membership cannot be deleted"
        ),
    )


# ============================================================
# DIRECT TERM TABLES
# ============================================================

def create_direct_term_guards(
    cursor,
):

    direct_tables = (

        "annual_schedule",

        "application_periods",

        "mandate_elections",

        "mandate_approvals",

    )


    for table in direct_tables:

        create_guard_trigger(

            cursor,

            f"trg_archived_{table}_no_insert",

            table,

            "INSERT",

            archived_term(
                "NEW.term_id"
            ),

            (
                "HISTORICAL_IMMUTABILITY: "
                f"archived {table} data "
                "cannot be created"
            ),
        )


        create_guard_trigger(

            cursor,

            f"trg_archived_{table}_no_update",

            table,

            "UPDATE",

            (
                f"{archived_term('OLD.term_id')} "
                "OR "
                f"{archived_term('NEW.term_id')}"
            ),

            (
                "HISTORICAL_IMMUTABILITY: "
                f"archived {table} data "
                "cannot be modified"
            ),
        )


        create_guard_trigger(

            cursor,

            f"trg_archived_{table}_no_delete",

            table,

            "DELETE",

            archived_term(
                "OLD.term_id"
            ),

            (
                "HISTORICAL_IMMUTABILITY: "
                f"archived {table} data "
                "cannot be deleted"
            ),
        )


# ============================================================
# EVENTS
# ============================================================

def create_event_guards(
    cursor,
):

    create_guard_trigger(

        cursor,

        "trg_archived_events_no_insert",

        "events",

        "INSERT",

        archived_term(
            "NEW.term_id"
        ),

        (
            "HISTORICAL_IMMUTABILITY: "
            "archived event cannot be created"
        ),
    )


    create_guard_trigger(

        cursor,

        "trg_archived_events_no_update",

        "events",

        "UPDATE",

        (
            f"{archived_term('OLD.term_id')} "
            "OR "
            f"{archived_term('NEW.term_id')}"
        ),

        (
            "HISTORICAL_IMMUTABILITY: "
            "archived event cannot be modified"
        ),
    )


    create_guard_trigger(

        cursor,

        "trg_archived_events_no_delete",

        "events",

        "DELETE",

        archived_term(
            "OLD.term_id"
        ),

        (
            "HISTORICAL_IMMUTABILITY: "
            "archived event cannot be deleted"
        ),
    )


    child_tables = (

        (
            "event_media",
            "event_id",
        ),

        (
            "event_attendance",
            "event_id",
        ),

        (
            "event_documents",
            "event_id",
        ),

        (
            "event_organizations",
            "event_id",
        ),

    )


    for (
        table,
        foreign_key,
    ) in child_tables:

        for (
            event,
            alias,
        ) in (

            (
                "INSERT",
                "NEW",
            ),

            (
                "UPDATE",
                "NEW",
            ),

            (
                "DELETE",
                "OLD",
            ),

        ):

            create_guard_trigger(

                cursor,

                (
                    f"trg_archived_"
                    f"{table}_"
                    f"{event.lower()}"
                ),

                table,

                event,

                event_is_archived(
                    f"{alias}."
                    f"{foreign_key}"
                ),

                (
                    "HISTORICAL_IMMUTABILITY: "
                    "archived event data "
                    "cannot be modified"
                ),
            )


# ============================================================
# PROJECTS / ARTICLES / TRAININGS
# ============================================================

def create_single_term_family_guards(
    cursor,
):

    families = (

        {

            "bridge":
                "project_terms",

            "bridge_parent":
                "project_id",

            "parent":
                "projects",

            "parent_pk":
                "project_id",

            "children": (

                (
                    "project_members",
                    "project_id",
                ),

                (
                    "project_volunteers",
                    "project_id",
                ),

            ),
        },


        {

            "bridge":
                "article_terms",

            "bridge_parent":
                "scientific_article_id",

            "parent":
                "scientific_articles",

            "parent_pk":
                "scientific_article_id",

            "children": (

                (
                    "article_authors",
                    "scientific_article_id",
                ),

                (
                    "article_volunteers",
                    "scientific_article_id",
                ),

                (
                    "article_source_references",
                    "scientific_article_id",
                ),

            ),
        },


        {

            "bridge":
                "training_terms",

            "bridge_parent":
                "training_id",

            "parent":
                "trainings",

            "parent_pk":
                "training_id",

            "children": (

                (
                    "training_attendance",
                    "training_id",
                ),

                (
                    "training_media",
                    "training_id",
                ),

            ),
        },

    )


    for family in families:

        bridge = (
            family[
                "bridge"
            ]
        )


        bridge_parent = (
            family[
                "bridge_parent"
            ]
        )


        parent = (
            family[
                "parent"
            ]
        )


        parent_pk = (
            family[
                "parent_pk"
            ]
        )


        # ====================================================
        # TERM LINK
        # ====================================================

        create_guard_trigger(

            cursor,

            (
                f"trg_archived_"
                f"{bridge}_insert"
            ),

            bridge,

            "INSERT",

            archived_term(
                "NEW.term_id"
            ),

            (
                "HISTORICAL_IMMUTABILITY: "
                f"archived {parent} "
                "term link cannot be created"
            ),
        )


        create_guard_trigger(

            cursor,

            (
                f"trg_archived_"
                f"{bridge}_update"
            ),

            bridge,

            "UPDATE",

            (
                f"{archived_term('OLD.term_id')} "
                "OR "
                f"{archived_term('NEW.term_id')}"
            ),

            (
                "HISTORICAL_IMMUTABILITY: "
                f"archived {parent} "
                "term link cannot be modified"
            ),
        )


        create_guard_trigger(

            cursor,

            (
                f"trg_archived_"
                f"{bridge}_delete"
            ),

            bridge,

            "DELETE",

            archived_term(
                "OLD.term_id"
            ),

            (
                "HISTORICAL_IMMUTABILITY: "
                f"archived {parent} "
                "term link cannot be deleted"
            ),
        )


        # ====================================================
        # PARENT ROW
        # ====================================================

        archived_parent = (
            parent_has_archived_term(

                bridge,

                bridge_parent,

                f"OLD.{parent_pk}",
            )
        )


        create_guard_trigger(

            cursor,

            (
                f"trg_archived_"
                f"{parent}_update"
            ),

            parent,

            "UPDATE",

            archived_parent,

            (
                "HISTORICAL_IMMUTABILITY: "
                f"archived {parent} "
                "cannot be modified"
            ),
        )


        create_guard_trigger(

            cursor,

            (
                f"trg_archived_"
                f"{parent}_delete"
            ),

            parent,

            "DELETE",

            archived_parent,

            (
                "HISTORICAL_IMMUTABILITY: "
                f"archived {parent} "
                "cannot be deleted"
            ),
        )


        # ====================================================
        # CHILD TABLES
        # ====================================================

        for (
            child_table,
            child_foreign_key,
        ) in family[
            "children"
        ]:

            for (
                event,
                alias,
            ) in (

                (
                    "INSERT",
                    "NEW",
                ),

                (
                    "UPDATE",
                    "NEW",
                ),

                (
                    "DELETE",
                    "OLD",
                ),

            ):

                create_guard_trigger(

                    cursor,

                    (
                        f"trg_archived_"
                        f"{child_table}_"
                        f"{event.lower()}"
                    ),

                    child_table,

                    event,

                    parent_has_archived_term(

                        bridge,

                        bridge_parent,

                        (
                            f"{alias}."
                            f"{child_foreign_key}"
                        ),
                    ),

                    (
                        "HISTORICAL_IMMUTABILITY: "
                        f"archived {parent} "
                        "data cannot be modified"
                    ),
                )


# ============================================================
# ORGANIZATIONS
# ============================================================

def create_organization_guards(
    cursor,
):

    create_guard_trigger(

        cursor,

        (
            "trg_archived_"
            "organization_relations_no_insert"
        ),

        "organization_relations",

        "INSERT",

        archived_term(
            "NEW.term_id"
        ),

        (
            "HISTORICAL_IMMUTABILITY: "
            "archived organization "
            "relation cannot be created"
        ),
    )


    create_guard_trigger(

        cursor,

        (
            "trg_archived_"
            "organization_relations_no_update"
        ),

        "organization_relations",

        "UPDATE",

        (
            f"{archived_term('OLD.term_id')} "
            "OR "
            f"{archived_term('NEW.term_id')}"
        ),

        (
            "HISTORICAL_IMMUTABILITY: "
            "archived organization "
            "relation cannot be modified"
        ),
    )


    create_guard_trigger(

        cursor,

        (
            "trg_archived_"
            "organization_relations_no_delete"
        ),

        "organization_relations",

        "DELETE",

        archived_term(
            "OLD.term_id"
        ),

        (
            "HISTORICAL_IMMUTABILITY: "
            "archived organization "
            "relation cannot be deleted"
        ),
    )


    create_guard_trigger(

        cursor,

        (
            "trg_archived_"
            "organizations_no_delete"
        ),

        "organizations",

        "DELETE",

        """
        EXISTS (

            SELECT 1

            FROM organization_relations

            JOIN terms

                ON organization_relations.term_id =
                   terms.term_id

            WHERE
                organization_relations.organization_id =
                OLD.organization_id

              AND terms.status =
                  'ARCHIVED'
        )
        """,

        (
            "HISTORICAL_IMMUTABILITY: "
            "organization with archived "
            "history cannot be deleted"
        ),
    )


# ============================================================
# MIGRATION
# ============================================================

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


    cursor = (
        conn.cursor()
    )


    try:

        conn.execute(
            "BEGIN IMMEDIATE"
        )


        # ====================================================
        # CURRENT DATA SAFETY
        # ====================================================

        assert_no_shared_multi_term_rows(
            cursor
        )


        # ====================================================
        # ONE TERM PER MUTABLE RECORD
        # ====================================================

        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_project_terms_single_term

            ON project_terms(
                project_id
            )
            """
        )


        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_article_terms_single_term

            ON article_terms(
                scientific_article_id
            )
            """
        )


        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_training_terms_single_term

            ON training_terms(
                training_id
            )
            """
        )


        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_organization_relations_unique_term

            ON organization_relations(
                organization_id,
                term_id
            )
            """
        )


        # ====================================================
        # ORGANIZATION HISTORY
        # ====================================================

        add_organization_snapshot_columns(
            cursor
        )


        backfill_organization_snapshots(
            cursor
        )


        create_snapshot_triggers(
            cursor
        )


        # ====================================================
        # ARCHIVE PROTECTION
        # ====================================================

        create_term_and_membership_guards(
            cursor
        )


        create_direct_term_guards(
            cursor
        )


        create_event_guards(
            cursor
        )


        create_single_term_family_guards(
            cursor
        )


        create_organization_guards(
            cursor
        )


        # ====================================================
        # DATABASE HEALTH
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


        trigger_count = (
            cursor.execute(
                """
                SELECT
                    COUNT(*)

                FROM sqlite_master

                WHERE type = 'trigger'

                  AND (

                        name LIKE
                        'trg_archived_%'

                        OR

                        name LIKE
                        'trg_organization_%'
                  )
                """
            ).fetchone()[0]
        )


        # ====================================================
        # RESULT
        # ====================================================

        if verbose:

            print()

            print(
                "========================================"
            )

            print(
                "HISTORICAL IMMUTABILITY MIGRATION SUCCESSFUL"
            )

            print(
                "========================================"
            )


            print(
                "Project records limited "
                "to one mandate: OK"
            )


            print(
                "Article records limited "
                "to one mandate: OK"
            )


            print(
                "Training records limited "
                "to one mandate: OK"
            )


            print(
                "Archived memberships/events/"
                "content locked: OK"
            )


            print(
                "Organization historical "
                "snapshots: OK"
            )


            print(
                "Organization relation "
                "uniqueness: OK"
            )


            print(
                "Historical protection "
                "triggers:",
                trigger_count,
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

            "trigger_count":
                trigger_count,
        }


    except Exception:

        conn.rollback()

        raise


    finally:

        conn.close()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    migrate_database()