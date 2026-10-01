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
    / "public_alumni_test.db"
)

UPLOAD_FOLDER = (
    BACKEND_DIR
    / "uploads"
    / "alumni"
)

PUBLIC_PHOTO = (
    "task7_public_alumni.png"
)

HIDDEN_PHOTO = (
    "task7_hidden_alumni.png"
)


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


database.DATABASE_PATH = (
    TEST_DB
)


UPLOAD_FOLDER.mkdir(
    parents=True,
    exist_ok=True,
)


public_photo_path = (
    UPLOAD_FOLDER
    / PUBLIC_PHOTO
)

hidden_photo_path = (
    UPLOAD_FOLDER
    / HIDDEN_PHOTO
)


public_photo_path.write_bytes(
    b"task 7 public alumni photo"
)

hidden_photo_path.write_bytes(
    b"task 7 hidden alumni photo"
)


try:

    conn = (
        database.get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    # ========================================================
    # CLEAR CURRENT SPOTLIGHT IN TEMP COPY
    # ========================================================

    cursor.execute(
        """
        UPDATE alumni_profiles

        SET is_spotlight = 0
        """
    )


    # ========================================================
    # PUBLIC ALUMNI
    # ========================================================

    cursor.execute(
        """
        INSERT INTO people (
            first_name,
            last_name,
            university
        )

        VALUES (
            'PublicTaskSeven',
            'Alumni',
            'USTHB'
        )
        """
    )


    public_person_id = (
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

            graduation_year,

            short_bio,

            story,

            photo_path,

            linkedin_url,

            website_url,

            is_public,

            is_featured,

            is_spotlight,

            display_order
        )

        VALUES (
            ?,
            'public-task-seven-alumni',
            'STARTUP',
            'From ORSC to entrepreneurship',
            'Founder',
            'Test Startup',
            2025,
            'Public Alumni test biography.',
            'Public Alumni test journey.',
            ?,
            'https://example.com/linkedin',
            'https://example.com',
            1,
            1,
            1,
            1
        )
        """,
        (
            public_person_id,
            PUBLIC_PHOTO,
        ),
    )


    # ========================================================
    # HIDDEN ALUMNI
    # ========================================================

    cursor.execute(
        """
        INSERT INTO people (
            first_name,
            last_name,
            university
        )

        VALUES (
            'HiddenTaskSeven',
            'Alumni',
            'USTHB'
        )
        """
    )


    hidden_person_id = (
        cursor.lastrowid
    )


    cursor.execute(
        """
        INSERT INTO alumni_profiles (

            person_id,

            slug,

            category,

            headline,

            photo_path,

            is_public,

            is_featured,

            is_spotlight,

            display_order
        )

        VALUES (
            ?,
            'hidden-task-seven-alumni',
            'ACADEMIA',
            'Hidden Alumni test',
            ?,
            0,
            1,
            0,
            2
        )
        """,
        (
            hidden_person_id,
            HIDDEN_PHOTO,
        ),
    )


    conn.commit()

    conn.close()


    # ========================================================
    # PUBLIC DIRECTORY
    # ========================================================

    with app.test_client() as client:

        response = client.get(
            "/website/alumni"
        )


        require(
            response.status_code
            == 200,

            "Public Alumni directory failed.",
        )


        body = response.get_data(
            as_text=True
        )


        require(
            "PublicTaskSeven"
            in body,

            "Public Alumni is missing "
            "from directory.",
        )


        require(
            "HiddenTaskSeven"
            not in body,

            "Hidden Alumni appeared "
            "in public directory.",
        )


        require(
            "FROM ORSC"
            in body,

            "Public Alumni hero missing.",
        )


    print(
        "Public Alumni directory: OK"
    )


    # ========================================================
    # CATEGORY FILTER
    # ========================================================

    with app.test_client() as client:

        response = client.get(
            "/website/alumni"
            "?category=STARTUP"
        )


        require(
            response.status_code
            == 200,

            "Public Alumni filter failed.",
        )


        body = response.get_data(
            as_text=True
        )


        require(
            "PublicTaskSeven"
            in body,

            "Startup Alumni missing "
            "from STARTUP filter.",
        )


        response = client.get(
            "/website/alumni"
            "?category=ACADEMIA"
        )


        require(
            response.status_code
            == 200,

            "ACADEMIA filter failed.",
        )


        body = response.get_data(
            as_text=True
        )


        require(
            "PublicTaskSeven"
            not in body,

            "STARTUP Alumni appeared "
            "inside ACADEMIA filter.",
        )


    print(
        "Public category filters: OK"
    )


    # ========================================================
    # PUBLIC DETAIL
    # ========================================================

    with app.test_client() as client:

        response = client.get(
            "/website/alumni/"
            "public-task-seven-alumni"
        )


        require(
            response.status_code
            == 200,

            "Public Alumni detail failed.",
        )


        body = response.get_data(
            as_text=True
        )


        require(
            "PublicTaskSeven"
            in body,

            "Public Alumni detail "
            "content missing.",
        )


        require(
            "Founder"
            in body,

            "Current Alumni path "
            "missing from detail.",
        )


    print(
        "Public Alumni detail: OK"
    )


    # ========================================================
    # HIDDEN DETAIL
    # ========================================================

    with app.test_client() as client:

        response = client.get(
            "/website/alumni/"
            "hidden-task-seven-alumni"
        )


        require(
            response.status_code
            == 404,

            "Hidden Alumni detail "
            "was publicly accessible.",
        )


    print(
        "Hidden Alumni privacy: OK"
    )


    # ========================================================
    # PUBLIC PHOTO
    # ========================================================

    with app.test_client() as client:

        response = client.get(
            "/website/alumni/"
            "public-task-seven-alumni/photo"
        )


        require(
            response.status_code
            == 200,

            "Public Alumni photo failed.",
        )


        response = client.get(
            "/website/alumni/"
            "hidden-task-seven-alumni/photo"
        )


        require(
            response.status_code
            == 404,

            "Hidden Alumni photo "
            "was publicly accessible.",
        )


    print(
        "Public/hidden Alumni photo "
        "protection: OK"
    )


    # ========================================================
    # HOME SPOTLIGHT
    # ========================================================

    with app.test_client() as client:

        response = client.get(
            "/website"
        )


        require(
            response.status_code
            == 200,

            "Public homepage failed.",
        )


        body = response.get_data(
            as_text=True
        )


        require(
            "ALUMNI SPOTLIGHT"
            in body,

            "Homepage Alumni "
            "Spotlight missing.",
        )


        require(
            "PublicTaskSeven"
            in body,

            "Spotlight Alumni name "
            "missing from homepage.",
        )


        require(
            "Meet Our Alumni"
            in body,

            "Homepage Alumni CTA missing.",
        )


    print(
        "Homepage Alumni Spotlight: OK"
    )


    # ========================================================
    # NAVIGATION
    # ========================================================

    with app.test_client() as client:

        response = client.get(
            "/website"
        )


        body = response.get_data(
            as_text=True
        )


        require(
            "/website/alumni"
            in body,

            "Public Alumni navigation "
            "link missing.",
        )


    print(
        "Public navigation Alumni link: OK"
    )


    # ========================================================
    # DATABASE HEALTH
    # ========================================================

    conn = (
        database.get_db_connection()
    )


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


    print()

    print(
        "========================================"
    )

    print(
        "PUBLIC ALUMNI TEST SUCCESSFUL"
    )

    print(
        "========================================"
    )


    print(
        "Public Alumni directory: OK"
    )

    print(
        "Category filters: OK"
    )

    print(
        "Public Alumni detail: OK"
    )

    print(
        "Hidden profiles protected: OK"
    )

    print(
        "Hidden photos protected: OK"
    )

    print(
        "Homepage Spotlight: OK"
    )

    print(
        "Public navigation: OK"
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

    for path in (
        public_photo_path,
        hidden_photo_path,
    ):

        if path.exists():

            try:

                path.unlink()

            except OSError:

                pass


    if TEST_DB.exists():

        TEST_DB.unlink()


    print(
        "Temporary database deleted."
    )