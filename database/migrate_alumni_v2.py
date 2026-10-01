import shutil
import sqlite3
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = DATABASE_DIR / "rsclub.db"

BACKUP_PATH = (
    DATABASE_DIR
    / "rsclub_backup_before_alumni_v2.db"
)


ALUMNI_PROFILE_COLUMNS = {
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


def get_table_columns(
    cursor,
    table_name,
):

    return {
        row["name"]

        for row in cursor.execute(
            f'PRAGMA table_info("{table_name}")'
        ).fetchall()
    }


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
        # ALUMNI PROFILES
        #
        # Important:
        #
        # Alumni status is separate from memberships.
        #
        # memberships =
        # historical ORSC role per mandate
        #
        # alumni_profiles =
        # current alumni public/CMS profile
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS alumni_profiles (

                alumni_id INTEGER PRIMARY KEY,

                person_id INTEGER
                    NOT NULL
                    UNIQUE,

                slug TEXT UNIQUE,


                category TEXT
                    NOT NULL
                    DEFAULT 'OTHER'

                    CHECK (
                        category IN (
                            'ACADEMIA',
                            'STARTUP',
                            'INDUSTRY',
                            'OTHER'
                        )
                    ),


                headline TEXT,

                current_title TEXT,

                current_organization TEXT,


                graduation_year INTEGER

                    CHECK (
                        graduation_year IS NULL
                        OR graduation_year
                           BETWEEN 1900 AND 2200
                    ),


                short_bio TEXT,

                story TEXT,


                photo_path TEXT,

                linkedin_url TEXT,

                website_url TEXT,


                is_public INTEGER
                    NOT NULL
                    DEFAULT 0

                    CHECK (
                        is_public IN (0, 1)
                    ),


                is_featured INTEGER
                    NOT NULL
                    DEFAULT 0

                    CHECK (
                        is_featured IN (0, 1)
                    ),


                is_spotlight INTEGER
                    NOT NULL
                    DEFAULT 0

                    CHECK (
                        is_spotlight IN (0, 1)
                    ),


                display_order INTEGER
                    NOT NULL
                    DEFAULT 0

                    CHECK (
                        display_order >= 0
                    ),


                created_by_user_id INTEGER,

                updated_by_user_id INTEGER,


                created_at TEXT
                    NOT NULL
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TEXT,


                FOREIGN KEY (
                    person_id
                )

                    REFERENCES people(
                        person_id
                    )

                    ON DELETE CASCADE,


                FOREIGN KEY (
                    created_by_user_id
                )

                    REFERENCES users(
                        user_id
                    )

                    ON DELETE SET NULL,


                FOREIGN KEY (
                    updated_by_user_id
                )

                    REFERENCES users(
                        user_id
                    )

                    ON DELETE SET NULL
            )
            """
        )


        # ====================================================
        # INDEXES
        # ====================================================

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_alumni_profiles_public

            ON alumni_profiles(
                is_public,
                display_order,
                alumni_id
            )
            """
        )


        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_alumni_profiles_category

            ON alumni_profiles(
                category,
                is_public
            )
            """
        )


        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_alumni_profiles_featured

            ON alumni_profiles(
                is_featured,
                is_public,
                display_order
            )
            """
        )


        # ====================================================
        # ONLY ONE HOME SPOTLIGHT
        # ====================================================

        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_alumni_single_spotlight

            ON alumni_profiles(
                is_spotlight
            )

            WHERE is_spotlight = 1
            """
        )


        # ====================================================
        # BLOCK ALUMNI ROLE IN ACTIVE / DRAFT
        #
        # The legacy ALUMNI role stays in roles for now
        # because older parts of the CMS still know it.
        #
        # But no new ACTIVE or DRAFT membership may use it.
        # ====================================================

        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS
                trg_memberships_no_alumni_active_insert

            BEFORE INSERT
            ON memberships

            FOR EACH ROW

            WHEN

                EXISTS (

                    SELECT 1

                    FROM roles

                    WHERE role_id =
                          NEW.role_id

                      AND name =
                          'ALUMNI'
                )

                AND

                EXISTS (

                    SELECT 1

                    FROM terms

                    WHERE term_id =
                          NEW.term_id

                      AND status IN (
                          'ACTIVE',
                          'DRAFT'
                      )
                )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'ALUMNI role cannot be used in ACTIVE or DRAFT mandates'
                );

            END
            """
        )


        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS
                trg_memberships_no_alumni_active_update

            BEFORE UPDATE OF
                role_id,
                term_id

            ON memberships

            FOR EACH ROW

            WHEN

                EXISTS (

                    SELECT 1

                    FROM roles

                    WHERE role_id =
                          NEW.role_id

                      AND name =
                          'ALUMNI'
                )

                AND

                EXISTS (

                    SELECT 1

                    FROM terms

                    WHERE term_id =
                          NEW.term_id

                      AND status IN (
                          'ACTIVE',
                          'DRAFT'
                      )
                )

            BEGIN

                SELECT RAISE(
                    ABORT,
                    'ALUMNI role cannot be used in ACTIVE or DRAFT mandates'
                );

            END
            """
        )


        # ====================================================
        # VERIFY TABLE
        # ====================================================

        columns = get_table_columns(
            cursor,
            "alumni_profiles",
        )


        missing_columns = (
            ALUMNI_PROFILE_COLUMNS
            - columns
        )


        if missing_columns:

            raise RuntimeError(

                "alumni_profiles exists "
                "but is incomplete. "

                "Missing columns: "

                + ", ".join(
                    sorted(
                        missing_columns
                    )
                )
            )


        # ====================================================
        # DATABASE HEALTH
        # ====================================================

        integrity = cursor.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]


        foreign_keys = cursor.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()


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


        # ====================================================
        # RESULT
        # ====================================================

        if verbose:

            print()

            print(
                "========================================"
            )

            print(
                "ALUMNI V2 MIGRATION SUCCESSFUL"
            )

            print(
                "========================================"
            )

            print(
                "alumni_profiles: OK"
            )

            print(
                "Single spotlight rule: OK"
            )

            print(
                "ACTIVE/DRAFT ALUMNI "
                "role protection: OK"
            )

            print(
                "Historical memberships "
                "remain separate: OK"
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