import shutil
import sqlite3
from pathlib import Path

from migrate_alumni_v2 import (
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
    / "alumni_v2_test.db"
)


def connect(path):

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


if TEST_DB.exists():

    TEST_DB.unlink()


shutil.copy2(
    REAL_DB,
    TEST_DB,
)


try:

    # ========================================================
    # MIGRATE TEMP COPY
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
    # TABLE EXISTS
    # ========================================================

    table = cursor.execute(
        """
        SELECT
            name

        FROM sqlite_master

        WHERE type = 'table'

          AND name =
              'alumni_profiles'
        """
    ).fetchone()


    require(
        table is not None,
        "alumni_profiles table missing.",
    )


    # ========================================================
    # COLUMNS
    # ========================================================

    required_columns = {

        "alumni_id",

        "person_id",

        "slug",

        "category",

        "headline",

        "current_title",

        "current_organization",

        "graduation_year",

        "short_bio",

        "story",

        "photo_path",

        "linkedin_url",

        "website_url",

        "is_public",

        "is_featured",

        "is_spotlight",

        "display_order",

        "created_by_user_id",

        "updated_by_user_id",

        "created_at",

        "updated_at",

    }


    columns = {

        row["name"]

        for row in cursor.execute(
            """
            PRAGMA table_info(
                "alumni_profiles"
            )
            """
        ).fetchall()

    }


    require(

        required_columns
        <= columns,

        "alumni_profiles "
        "columns are incomplete.",

    )


    # ========================================================
    # INDEXES
    # ========================================================

    indexes = {

        row["name"]

        for row in cursor.execute(
            """
            SELECT
                name

            FROM sqlite_master

            WHERE type = 'index'

              AND sql IS NOT NULL
            """
        ).fetchall()

    }


    for index_name in {

        "idx_alumni_profiles_public",

        "idx_alumni_profiles_category",

        "idx_alumni_profiles_featured",

        "idx_alumni_single_spotlight",

    }:

        require(

            index_name
            in indexes,

            "Missing index: "
            f"{index_name}",

        )


    # ========================================================
    # TRIGGERS
    # ========================================================

    triggers = {

        row["name"]

        for row in cursor.execute(
            """
            SELECT
                name

            FROM sqlite_master

            WHERE type = 'trigger'
            """
        ).fetchall()

    }


    require(

        "trg_memberships_no_alumni_active_insert"
        in triggers,

        "ALUMNI insert protection "
        "trigger missing.",

    )


    require(

        "trg_memberships_no_alumni_active_update"
        in triggers,

        "ALUMNI update protection "
        "trigger missing.",

    )


    # ========================================================
    # OLDER ALUMNI WITHOUT HISTORICAL MEMBERSHIP
    #
    # This is intentionally allowed.
    #
    # It lets us manually add alumni from older years
    # even when their old ORSC mandate is not yet in DB.
    # ========================================================

    cursor.execute(
        """
        INSERT INTO people (
            first_name,
            last_name,
            university
        )

        VALUES (?, ?, ?)
        """,
        (
            "Legacy",

            "AlumniTest",

            "USTHB",
        ),
    )


    legacy_person_id = (
        cursor.lastrowid
    )


    cursor.execute(
        """
        INSERT INTO alumni_profiles (

            person_id,

            slug,

            category,

            headline,

            current_title,

            current_organization,

            short_bio,

            is_public,

            is_featured,

            is_spotlight
        )

        VALUES (
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            ?,
            1,
            1,
            1
        )
        """,
        (
            legacy_person_id,

            "legacy-alumni-test",

            "ACADEMIA",

            "Research path after ORSC",

            "PhD Candidate",

            "Test University",

            "Temporary alumni model test.",
        ),
    )


    membership_count = (
        cursor.execute(
            """
            SELECT
                COUNT(*)

            FROM memberships

            WHERE person_id = ?
            """,
            (
                legacy_person_id,
            ),
        ).fetchone()[0]
    )


    require(

        membership_count == 0,

        "Legacy alumni profile "
        "unexpectedly requires "
        "a historical membership.",

    )


    print(
        "Alumni profile without "
        "historical membership: OK"
    )


    # ========================================================
    # ONE PROFILE PER PERSON
    # ========================================================

    duplicate_person_blocked = (
        False
    )


    try:

        cursor.execute(
            """
            INSERT INTO alumni_profiles (
                person_id,
                category
            )

            VALUES (
                ?,
                'OTHER'
            )
            """,
            (
                legacy_person_id,
            ),
        )


    except sqlite3.IntegrityError:

        duplicate_person_blocked = (
            True
        )


    require(

        duplicate_person_blocked,

        "Duplicate alumni profile "
        "was allowed.",

    )


    print(
        "One alumni profile per person: OK"
    )


    # ========================================================
    # SECOND PERSON
    # ========================================================

    cursor.execute(
        """
        INSERT INTO people (
            first_name,
            last_name,
            university
        )

        VALUES (
            'Second',
            'SpotlightTest',
            'USTHB'
        )
        """
    )


    second_person_id = (
        cursor.lastrowid
    )


    # ========================================================
    # ONLY ONE SPOTLIGHT
    # ========================================================

    second_spotlight_blocked = (
        False
    )


    try:

        cursor.execute(
            """
            INSERT INTO alumni_profiles (

                person_id,

                slug,

                category,

                is_public,

                is_spotlight
            )

            VALUES (
                ?,
                ?,
                'INDUSTRY',
                1,
                1
            )
            """,
            (
                second_person_id,

                "second-spotlight-test",
            ),
        )


    except sqlite3.IntegrityError:

        second_spotlight_blocked = (
            True
        )


    require(

        second_spotlight_blocked,

        "More than one spotlight "
        "alumni was allowed.",

    )


    print(
        "Single homepage spotlight: OK"
    )


    # ========================================================
    # CATEGORY CONSTRAINT
    # ========================================================

    invalid_category_blocked = (
        False
    )


    try:

        cursor.execute(
            """
            INSERT INTO alumni_profiles (
                person_id,
                category
            )

            VALUES (
                ?,
                'INVALID'
            )
            """,
            (
                second_person_id,
            ),
        )


    except sqlite3.IntegrityError:

        invalid_category_blocked = (
            True
        )


    require(

        invalid_category_blocked,

        "Invalid alumni category "
        "was allowed.",

    )


    print(
        "Alumni category constraint: OK"
    )


    # ========================================================
    # REQUIRED ROLE IDS
    # ========================================================

    alumni_role = (
        cursor.execute(
            """
            SELECT
                role_id

            FROM roles

            WHERE name = 'ALUMNI'
            """
        ).fetchone()
    )


    member_role = (
        cursor.execute(
            """
            SELECT
                role_id

            FROM roles

            WHERE name = 'MEMBER'
            """
        ).fetchone()
    )


    require(
        alumni_role is not None,
        "Legacy ALUMNI role missing.",
    )


    require(
        member_role is not None,
        "MEMBER role missing.",
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
        draft_term is not None,
        "DRAFT term missing.",
    )


    # ========================================================
    # TEST INSERT TRIGGER
    # ========================================================

    cursor.execute(
        """
        INSERT INTO people (
            first_name,
            last_name,
            university
        )

        VALUES (
            'Trigger',
            'InsertTest',
            'USTHB'
        )
        """
    )


    trigger_person_id = (
        cursor.lastrowid
    )


    alumni_insert_blocked = (
        False
    )


    try:

        cursor.execute(
            """
            INSERT INTO memberships (

                person_id,

                term_id,

                role_id,

                department_id
            )

            VALUES (
                ?,
                ?,
                ?,
                NULL
            )
            """,
            (
                trigger_person_id,

                draft_term[
                    "term_id"
                ],

                alumni_role[
                    "role_id"
                ],
            ),
        )


    except sqlite3.IntegrityError:

        alumni_insert_blocked = (
            True
        )


    require(

        alumni_insert_blocked,

        "ALUMNI role was allowed "
        "in DRAFT on insert.",

    )


    print(
        "No ALUMNI role in "
        "DRAFT/ACTIVE inserts: OK"
    )


    # ========================================================
    # NORMAL MEMBER
    # ========================================================

    department = (
        cursor.execute(
            """
            SELECT
                department_id

            FROM departments

            ORDER BY
                department_id

            LIMIT 1
            """
        ).fetchone()
    )


    require(
        department is not None,
        "Department missing.",
    )


    cursor.execute(
        """
        INSERT INTO memberships (

            person_id,

            term_id,

            role_id,

            department_id
        )

        VALUES (?, ?, ?, ?)
        """,
        (
            trigger_person_id,

            draft_term[
                "term_id"
            ],

            member_role[
                "role_id"
            ],

            department[
                "department_id"
            ],
        ),
    )


    membership_id = (
        cursor.lastrowid
    )


    # ========================================================
    # TEST UPDATE TRIGGER
    # ========================================================

    alumni_update_blocked = (
        False
    )


    try:

        cursor.execute(
            """
            UPDATE memberships

            SET
                role_id = ?,

                department_id = NULL

            WHERE membership_id = ?
            """,
            (
                alumni_role[
                    "role_id"
                ],

                membership_id,
            ),
        )


    except sqlite3.IntegrityError:

        alumni_update_blocked = (
            True
        )


    require(

        alumni_update_blocked,

        "ALUMNI role was allowed "
        "in DRAFT on update.",

    )


    print(
        "No ALUMNI role in "
        "DRAFT/ACTIVE updates: OK"
    )


    # ========================================================
    # OLD ARCHIVED DATA STILL COMPATIBLE
    #
    # We are not deleting the old ALUMNI role yet.
    # Archived legacy data can still be read.
    # ========================================================

    archived_term = (
        cursor.execute(
            """
            SELECT
                term_id

            FROM terms

            WHERE status = 'ARCHIVED'

            ORDER BY
                term_id

            LIMIT 1
            """
        ).fetchone()
    )


    require(
        archived_term is not None,
        "ARCHIVED term missing.",
    )


    cursor.execute(
        """
        INSERT INTO people (
            first_name,
            last_name,
            university
        )

        VALUES (
            'Legacy',
            'ArchivedRoleTest',
            'USTHB'
        )
        """
    )


    archived_person_id = (
        cursor.lastrowid
    )


    cursor.execute(
        """
        INSERT INTO memberships (

            person_id,

            term_id,

            role_id,

            department_id
        )

        VALUES (
            ?,
            ?,
            ?,
            NULL
        )
        """,
        (
            archived_person_id,

            archived_term[
                "term_id"
            ],

            alumni_role[
                "role_id"
            ],
        ),
    )


    print(
        "Legacy archived ALUMNI "
        "compatibility: OK"
    )


    conn.commit()


    # ========================================================
    # PERSON -> ALUMNI PROFILE CASCADE
    # ========================================================

    cursor.execute(
        """
        DELETE FROM people

        WHERE person_id = ?
        """,
        (
            legacy_person_id,
        ),
    )


    remaining_profile = (
        cursor.execute(
            """
            SELECT
                COUNT(*)

            FROM alumni_profiles

            WHERE person_id = ?
            """,
            (
                legacy_person_id,
            ),
        ).fetchone()[0]
    )


    require(

        remaining_profile == 0,

        "Deleting a person did not "
        "cascade to alumni profile.",

    )


    print(
        "Alumni profile/person "
        "FK cascade: OK"
    )


    conn.commit()


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


    require(
        integrity == "ok",
        "Integrity check failed.",
    )


    require(
        not foreign_keys,
        "Foreign key check failed.",
    )


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

        "Second migration integrity "
        "check failed.",

    )


    require(

        not foreign_keys_second,

        "Second migration foreign "
        "key check failed.",

    )


    print(
        "Migration idempotency: OK"
    )


    # ========================================================
    # SUCCESS
    # ========================================================

    print()

    print(
        "========================================"
    )

    print(
        "ALUMNI V2 MODEL TEST SUCCESSFUL"
    )

    print(
        "========================================"
    )


    print(
        "Separate alumni_profiles model: OK"
    )

    print(
        "Historical memberships "
        "kept separate: OK"
    )

    print(
        "Older alumni without "
        "membership supported: OK"
    )

    print(
        "One profile per person: OK"
    )

    print(
        "Single homepage spotlight: OK"
    )

    print(
        "Category constraint: OK"
    )

    print(
        "ACTIVE/DRAFT ALUMNI role blocked: OK"
    )

    print(
        "Archived compatibility: OK"
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