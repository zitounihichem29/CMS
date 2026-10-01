import shutil
import sqlite3
from pathlib import Path

from migrate_history_immutability import (
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
    / "history_immutability_test.db"
)


# ============================================================
# HELPERS
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


def require(
    condition,
    message,
):

    if not condition:

        raise RuntimeError(
            message
        )


def require_blocked(
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


# ============================================================
# PREPARE TEMP COPY
# ============================================================

if TEST_DB.exists():

    TEST_DB.unlink()


shutil.copy2(
    REAL_DB,
    TEST_DB,
)


try:

    # ========================================================
    # MIGRATE TEMP DATABASE
    # ========================================================

    migrate_database(

        db_path=TEST_DB,

        create_backup_file=False,

        verbose=False,

    )


    conn = connect(
        TEST_DB
    )


    cursor = (
        conn.cursor()
    )


    # ========================================================
    # INDEXES
    # ========================================================

    indexes = {

        row[
            "name"
        ]

        for row
        in cursor.execute(
            """
            SELECT
                name

            FROM sqlite_master

            WHERE type = 'index'

              AND sql IS NOT NULL
            """
        ).fetchall()

    }


    required_indexes = {

        "idx_project_terms_single_term",

        "idx_article_terms_single_term",

        "idx_training_terms_single_term",

        "idx_organization_relations_unique_term",

    }


    for index_name in (
        required_indexes
    ):

        require(

            index_name
            in indexes,

            "Missing index: "
            f"{index_name}",
        )


    # ========================================================
    # SNAPSHOT COLUMNS
    # ========================================================

    columns = {

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


    snapshot_columns = {

        "organization_name_snapshot",

        "organization_type_snapshot",

        "organization_description_snapshot",

        "organization_address_snapshot",

        "organization_website_snapshot",

        "organization_email_snapshot",

        "organization_phone_snapshot",

        "organization_logo_path_snapshot",

        "organization_original_logo_filename_snapshot",

    }


    for column_name in (
        snapshot_columns
    ):

        require(

            column_name
            in columns,

            "Missing snapshot column: "
            f"{column_name}",
        )


    # ========================================================
    # ACTIVE + DRAFT
    # ========================================================

    active_term = (
        cursor.execute(
            """
            SELECT
                term_id

            FROM terms

            WHERE status = 'ACTIVE'

            LIMIT 1
            """
        ).fetchone()
    )


    draft_term = (
        cursor.execute(
            """
            SELECT
                term_id

            FROM terms

            WHERE status = 'DRAFT'

            LIMIT 1
            """
        ).fetchone()
    )


    require(
        active_term is not None,

        "ACTIVE term missing.",
    )


    require(
        draft_term is not None,

        "DRAFT term missing.",
    )


    draft_membership = (
        cursor.execute(
            """
            SELECT
                membership_id,

                person_id

            FROM memberships

            WHERE term_id = ?

            LIMIT 1
            """,
            (
                draft_term[
                    "term_id"
                ],
            ),
        ).fetchone()
    )


    require(
        draft_membership is not None,

        "No DRAFT membership available.",
    )


    # ========================================================
    # PROJECT
    # ========================================================

    cursor.execute(
        """
        INSERT INTO projects (

            idea_owner_membership_id,

            name,

            status
        )

        VALUES (?, ?, ?)
        """,
        (
            draft_membership[
                "membership_id"
            ],

            "Task 9 Project",

            "active",
        ),
    )


    project_id = (
        cursor.lastrowid
    )


    cursor.execute(
        """
        INSERT INTO project_terms (
            project_id,
            term_id
        )

        VALUES (?, ?)
        """,
        (
            project_id,

            draft_term[
                "term_id"
            ],
        ),
    )


    require_blocked(

        lambda:

            cursor.execute(
                """
                INSERT INTO project_terms (
                    project_id,
                    term_id
                )

                VALUES (?, ?)
                """,
                (
                    project_id,

                    active_term[
                        "term_id"
                    ],
                ),
            ),

        (
            "Project was shared across "
            "multiple mandates."
        ),
    )


    # ========================================================
    # ARTICLE
    # ========================================================

    cursor.execute(
        """
        INSERT INTO scientific_articles (

            article_owner_membership_id,

            title,

            status
        )

        VALUES (?, ?, ?)
        """,
        (
            draft_membership[
                "membership_id"
            ],

            "Task 9 Article",

            "active",
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

            draft_term[
                "term_id"
            ],
        ),
    )


    require_blocked(

        lambda:

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

                    active_term[
                        "term_id"
                    ],
                ),
            ),

        (
            "Article was shared across "
            "multiple mandates."
        ),
    )


    # ========================================================
    # TRAINING
    # ========================================================

    cursor.execute(
        """
        INSERT INTO trainings (

            coach_person_id,

            title
        )

        VALUES (?, ?)
        """,
        (
            draft_membership[
                "person_id"
            ],

            "Task 9 Training",
        ),
    )


    training_id = (
        cursor.lastrowid
    )


    cursor.execute(
        """
        INSERT INTO training_terms (
            training_id,
            term_id
        )

        VALUES (?, ?)
        """,
        (
            training_id,

            draft_term[
                "term_id"
            ],
        ),
    )


    require_blocked(

        lambda:

            cursor.execute(
                """
                INSERT INTO training_terms (
                    training_id,
                    term_id
                )

                VALUES (?, ?)
                """,
                (
                    training_id,

                    active_term[
                        "term_id"
                    ],
                ),
            ),

        (
            "Training was shared across "
            "multiple mandates."
        ),
    )


    # ========================================================
    # EVENT
    # ========================================================

    cursor.execute(
        """
        INSERT INTO events (

            term_id,

            event_leader_membership_id,

            title,

            event_date
        )

        VALUES (?, ?, ?, ?)
        """,
        (
            draft_term[
                "term_id"
            ],

            draft_membership[
                "membership_id"
            ],

            "Task 9 Event",

            "2099-01-01",
        ),
    )


    event_id = (
        cursor.lastrowid
    )


    # ========================================================
    # ORGANIZATION + RELATION
    # ========================================================

    cursor.execute(
        """
        INSERT INTO organizations (

            name,

            organization_type,

            created_by_membership_id
        )

        VALUES (?, ?, ?)
        """,
        (
            "Task 9 Organization",

            "company",

            draft_membership[
                "membership_id"
            ],
        ),
    )


    organization_id = (
        cursor.lastrowid
    )


    cursor.execute(
        """
        INSERT INTO organization_relations (

            organization_id,

            term_id,

            relation_type
        )

        VALUES (?, ?, ?)
        """,
        (
            organization_id,

            draft_term[
                "term_id"
            ],

            "partner",
        ),
    )


    relation_id = (
        cursor.lastrowid
    )


    snapshot = (
        cursor.execute(
            """
            SELECT
                organization_name_snapshot

            FROM organization_relations

            WHERE organization_relation_id = ?
            """,
            (
                relation_id,
            ),
        ).fetchone()[
            "organization_name_snapshot"
        ]
    )


    require(

        snapshot
        ==
        "Task 9 Organization",

        "Initial organization "
        "snapshot failed.",
    )


    # ========================================================
    # NON-ARCHIVED SNAPSHOT SYNCS
    # ========================================================

    cursor.execute(
        """
        UPDATE organizations

        SET
            name = ?

        WHERE organization_id = ?
        """,
        (
            "Task 9 Organization Updated",

            organization_id,
        ),
    )


    snapshot = (
        cursor.execute(
            """
            SELECT
                organization_name_snapshot

            FROM organization_relations

            WHERE organization_relation_id = ?
            """,
            (
                relation_id,
            ),
        ).fetchone()[
            "organization_name_snapshot"
        ]
    )


    require(

        snapshot
        ==
        "Task 9 Organization Updated",

        "Current organization "
        "snapshot did not sync.",
    )


    # ========================================================
    # ARCHIVE TEMP DRAFT
    # ========================================================

    cursor.execute(
        """
        UPDATE terms

        SET status = 'ARCHIVED'

        WHERE term_id = ?
        """,
        (
            draft_term[
                "term_id"
            ],
        ),
    )


    # ========================================================
    # PROJECT IMMUTABILITY
    # ========================================================

    require_blocked(

        lambda:

            cursor.execute(
                """
                UPDATE projects

                SET name =
                    'Changed'

                WHERE project_id = ?
                """,
                (
                    project_id,
                ),
            ),

        "Archived project was editable.",
    )


    # ========================================================
    # ARTICLE IMMUTABILITY
    # ========================================================

    require_blocked(

        lambda:

            cursor.execute(
                """
                UPDATE scientific_articles

                SET title =
                    'Changed'

                WHERE scientific_article_id = ?
                """,
                (
                    article_id,
                ),
            ),

        "Archived article was editable.",
    )


    # ========================================================
    # TRAINING IMMUTABILITY
    # ========================================================

    require_blocked(

        lambda:

            cursor.execute(
                """
                UPDATE trainings

                SET title =
                    'Changed'

                WHERE training_id = ?
                """,
                (
                    training_id,
                ),
            ),

        "Archived training was editable.",
    )


    # ========================================================
    # EVENT IMMUTABILITY
    # ========================================================

    require_blocked(

        lambda:

            cursor.execute(
                """
                UPDATE events

                SET title =
                    'Changed'

                WHERE event_id = ?
                """,
                (
                    event_id,
                ),
            ),

        "Archived event was editable.",
    )


    # ========================================================
    # MEMBERSHIP IMMUTABILITY
    # ========================================================

    require_blocked(

        lambda:

            cursor.execute(
                """
                UPDATE memberships

                SET role_id =
                    role_id

                WHERE membership_id = ?
                """,
                (
                    draft_membership[
                        "membership_id"
                    ],
                ),
            ),

        "Archived membership was editable.",
    )


    # ========================================================
    # ORGANIZATION RELATION IMMUTABILITY
    # ========================================================

    require_blocked(

        lambda:

            cursor.execute(
                """
                UPDATE organization_relations

                SET relation_type =
                    'other'

                WHERE organization_relation_id = ?
                """,
                (
                    relation_id,
                ),
            ),

        (
            "Archived organization "
            "relation was editable."
        ),
    )


    # ========================================================
    # ORGANIZATION WITH HISTORY CANNOT BE DELETED
    # ========================================================

    require_blocked(

        lambda:

            cursor.execute(
                """
                DELETE FROM organizations

                WHERE organization_id = ?
                """,
                (
                    organization_id,
                ),
            ),

        (
            "Organization with archived "
            "history was deletable."
        ),
    )


    # ========================================================
    # ARCHIVED TERM ITSELF IS LOCKED
    # ========================================================

    require_blocked(

        lambda:

            cursor.execute(
                """
                UPDATE terms

                SET name = name

                WHERE term_id = ?
                """,
                (
                    draft_term[
                        "term_id"
                    ],
                ),
            ),

        "Archived term was editable.",
    )


    # ========================================================
    # CURRENT ORGANIZATION MAY EVOLVE
    #
    # BUT ARCHIVED SNAPSHOT MUST NOT CHANGE
    # ========================================================

    cursor.execute(
        """
        UPDATE organizations

        SET name = ?

        WHERE organization_id = ?
        """,
        (
            "Task 9 Organization Current",

            organization_id,
        ),
    )


    frozen_snapshot = (
        cursor.execute(
            """
            SELECT
                organization_name_snapshot

            FROM organization_relations

            WHERE organization_relation_id = ?
            """,
            (
                relation_id,
            ),
        ).fetchone()[
            "organization_name_snapshot"
        ]
    )


    current_name = (
        cursor.execute(
            """
            SELECT
                name

            FROM organizations

            WHERE organization_id = ?
            """,
            (
                organization_id,
            ),
        ).fetchone()[
            "name"
        ]
    )


    require(

        frozen_snapshot
        ==
        "Task 9 Organization Updated",

        (
            "Archived organization "
            "snapshot changed."
        ),
    )


    require(

        current_name
        ==
        "Task 9 Organization Current",

        (
            "Current organization metadata "
            "could not evolve."
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

        integrity_second
        == "ok",

        (
            "Second migration "
            "integrity check failed."
        ),
    )


    require(

        not foreign_keys_second,

        (
            "Second migration "
            "foreign key check failed."
        ),
    )


    # ========================================================
    # SUCCESS
    # ========================================================

    print(
        "========================================"
    )

    print(
        "HISTORICAL IMMUTABILITY TEST SUCCESSFUL"
    )

    print(
        "========================================"
    )


    print(
        "One mandate per "
        "project record: OK"
    )

    print(
        "One mandate per "
        "article record: OK"
    )

    print(
        "One mandate per "
        "training record: OK"
    )

    print(
        "Archived project/article/"
        "training/event locked: OK"
    )

    print(
        "Archived memberships locked: OK"
    )

    print(
        "Archived terms locked: OK"
    )

    print(
        "Organization current "
        "snapshots sync: OK"
    )

    print(
        "Organization archived "
        "snapshots freeze: OK"
    )

    print(
        "Archived organization "
        "relations locked: OK"
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