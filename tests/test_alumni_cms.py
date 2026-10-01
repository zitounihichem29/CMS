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
    / "alumni_cms_test.db"
)

ALUMNI_UPLOADS = (
    BACKEND_DIR
    / "uploads"
    / "alumni"
)


created_photos = []


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


    # ========================================================
    # MANAGER
    # ========================================================

    manager = (
        conn.execute(
            """
            SELECT
                users.user_id,
                users.username

            FROM users

            WHERE users.is_active = 1

              AND users.is_platform_admin = 1

            ORDER BY
                users.user_id

            LIMIT 1
            """
        ).fetchone()
    )


    require(
        manager is not None,
        "No active Platform "
        "Administrator found.",
    )


    # ========================================================
    # NON MANAGER
    # ========================================================

    non_manager = (
        conn.execute(
            """
            SELECT
                users.user_id,

                users.username,

                roles.name
                    AS role_name,

                memberships.department_id

            FROM users


            JOIN people

                ON users.person_id =
                   people.person_id


            JOIN terms

                ON terms.status =
                   'ACTIVE'


            JOIN memberships

                ON memberships.person_id =
                   people.person_id

               AND memberships.term_id =
                   terms.term_id


            JOIN roles

                ON memberships.role_id =
                   roles.role_id


            WHERE users.is_active = 1

              AND users.is_platform_admin = 0


              AND NOT (

                  roles.name IN (
                      'PRESIDENT',
                      'VICE_PRESIDENT'
                  )

              )


              AND NOT (

                  memberships.department_id = 1

                  AND roles.name IN (
                      'HEAD',
                      'SUB_HEAD'
                  )

              )


            ORDER BY
                users.user_id


            LIMIT 1
            """
        ).fetchone()
    )


    require(
        non_manager is not None,
        "No ordinary current member "
        "found for permission test.",
    )


    conn.close()


    print(
        "Alumni manager:",
        manager[
            "username"
        ],
    )


    print(
        "Non-manager viewer:",
        non_manager[
            "username"
        ],
    )


    # ========================================================
    # ANONYMOUS
    # ========================================================

    with app.test_client() as client:

        response = client.get(
            "/alumni",
            follow_redirects=False,
        )


        require(
            response.status_code
            == 302,

            "Anonymous Alumni access "
            "was not redirected.",
        )


    print(
        "Anonymous protection: OK"
    )


    # ========================================================
    # MANAGER PAGES
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            manager[
                "user_id"
            ],
        )


        response = client.get(
            "/alumni"
        )


        require(
            response.status_code
            == 200,

            "Alumni list failed "
            "for manager.",
        )


        response = client.get(
            "/alumni/new"
        )


        require(
            response.status_code
            == 200,

            "New Alumni page failed "
            "for manager.",
        )


    print(
        "Manager list/create pages: OK"
    )


    # ========================================================
    # NON MANAGER
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            non_manager[
                "user_id"
            ],
        )


        response = client.get(
            "/alumni"
        )


        require(
            response.status_code
            == 200,

            "Ordinary member cannot "
            "view Alumni directory.",
        )


        response = client.get(
            "/alumni/new"
        )


        require(
            response.status_code
            == 403,

            "Ordinary member was "
            "allowed to create Alumni.",
        )


    print(
        "View/manage permission split: OK"
    )


    # ========================================================
    # CREATE PERSON FOR EXISTING PERSON TEST
    # ========================================================

    conn = (
        database.get_db_connection()
    )


    cursor = (
        conn.cursor()
    )


    cursor.execute(
        """
        INSERT INTO people (
            first_name,
            last_name,
            email,
            university
        )

        VALUES (?, ?, ?, ?)
        """,
        (
            "Existing",

            "AlumniCandidate",

            "existing.alumni@example.test",

            "USTHB",
        ),
    )


    existing_person_id = (
        cursor.lastrowid
    )


    conn.commit()

    conn.close()


    # ========================================================
    # CREATE ALUMNI FROM EXISTING PERSON
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            manager[
                "user_id"
            ],
        )


        response = client.post(
            "/alumni/new",

            data={

                "existing_person_id":
                    str(
                        existing_person_id
                    ),

                "category":
                    "OTHER",

                "headline":
                    "Existing person Alumni test",

                "slug":
                    "existing-alumni-candidate",

                "display_order":
                    "0",
            },

            follow_redirects=False,
        )


        require(
            redirect_ok(
                response
            ),

            "Creating Alumni from "
            "existing person failed.",
        )


    conn = (
        database.get_db_connection()
    )


    existing_profile = (
        conn.execute(
            """
            SELECT
                alumni_id,
                person_id

            FROM alumni_profiles

            WHERE slug = ?
            """,
            (
                "existing-alumni-candidate",
            ),
        ).fetchone()
    )


    require(

        existing_profile is not None

        and existing_profile[
            "person_id"
        ] == existing_person_id,

        "Existing-person Alumni "
        "profile is incorrect.",

    )


    existing_profile_id = (
        existing_profile[
            "alumni_id"
        ]
    )


    conn.close()


    print(
        "Create Alumni from "
        "existing person: OK"
    )


    # ========================================================
    # CREATE NEW ALUMNI + PHOTO + SPOTLIGHT
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            manager[
                "user_id"
            ],
        )


        response = client.post(
            "/alumni/new",

            data={

                "existing_person_id":
                    "",

                "first_name":
                    "TaskSix",

                "last_name":
                    "AlumniOne",

                "email":
                    "tasksix.one@example.test",

                "university":
                    "USTHB",

                "category":
                    "STARTUP",

                "graduation_year":
                    "2025",

                "headline":
                    "From ORSC to entrepreneurship",

                "current_title":
                    "Founder",

                "current_organization":
                    "Test Startup",

                "short_bio":
                    "Temporary Alumni "
                    "CMS test profile.",

                "story":
                    "Temporary story "
                    "for automated testing.",

                "linkedin_url":
                    "https://example.com/linkedin-one",

                "website_url":
                    "https://example.com/one",

                "slug":
                    "task-six-alumni-one",

                "display_order":
                    "1",

                "is_public":
                    "1",

                "is_featured":
                    "1",

                "is_spotlight":
                    "1",

                "photo_file":
                    (
                        io.BytesIO(
                            b"fake image data"
                        ),

                        "alumni_one.png",
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

            "First Alumni creation failed.",
        )


    conn = (
        database.get_db_connection()
    )


    first = (
        conn.execute(
            """
            SELECT
                alumni_profiles.*,

                people.first_name,

                people.last_name

            FROM alumni_profiles


            JOIN people

                ON alumni_profiles.person_id =
                   people.person_id


            WHERE alumni_profiles.slug = ?
            """,
            (
                "task-six-alumni-one",
            ),
        ).fetchone()
    )


    require(
        first is not None,
        "First Alumni profile missing.",
    )


    require(

        first[
            "is_public"
        ] == 1

        and first[
            "is_featured"
        ] == 1

        and first[
            "is_spotlight"
        ] == 1,

        "First Alumni visibility "
        "flags are incorrect.",

    )


    require(
        first[
            "photo_path"
        ],

        "First Alumni photo "
        "path missing.",
    )


    first_photo = (
        first[
            "photo_path"
        ]
    )


    created_photos.append(
        first_photo
    )


    require(

        (
            ALUMNI_UPLOADS
            / first_photo
        ).exists(),

        "First Alumni photo "
        "file missing.",

    )


    first_id = (
        first[
            "alumni_id"
        ]
    )


    first_person_id = (
        first[
            "person_id"
        ]
    )


    membership_count = (
        conn.execute(
            """
            SELECT
                COUNT(*)

            FROM memberships

            WHERE person_id = ?
            """,
            (
                first_person_id,
            ),
        ).fetchone()[0]
    )


    require(

        membership_count == 0,

        "New older Alumni "
        "unexpectedly received "
        "a membership.",

    )


    conn.close()


    print(
        "Create older Alumni "
        "without history: OK"
    )


    print(
        "Alumni photo upload: OK"
    )


    # ========================================================
    # DETAIL + PHOTO
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            manager[
                "user_id"
            ],
        )


        response = client.get(
            f"/alumni/{first_id}"
        )


        require(
            response.status_code
            == 200,

            "Alumni detail failed.",
        )


        body = (
            response.get_data(
                as_text=True
            )
        )


        require(

            "TaskSix"
            in body

            and
            "No historical membership"
            in body,

            "Alumni detail does not "
            "show expected data.",

        )


        response = client.get(
            f"/alumni/photo/{first_photo}"
        )


        require(
            response.status_code
            == 200,

            "Alumni photo route failed.",
        )


    print(
        "Alumni detail + "
        "photo serving: OK"
    )


    # ========================================================
    # SECOND SPOTLIGHT
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            manager[
                "user_id"
            ],
        )


        response = client.post(
            "/alumni/new",

            data={

                "existing_person_id":
                    "",

                "first_name":
                    "TaskSix",

                "last_name":
                    "AlumniTwo",

                "email":
                    "tasksix.two@example.test",

                "university":
                    "USTHB",

                "category":
                    "ACADEMIA",

                "graduation_year":
                    "2024",

                "headline":
                    "Research after ORSC",

                "current_title":
                    "PhD Candidate",

                "current_organization":
                    "Test University",

                "short_bio":
                    "Second temporary profile.",

                "story":
                    "Second temporary story.",

                "slug":
                    "task-six-alumni-two",

                "display_order":
                    "2",

                "is_spotlight":
                    "1",
            },

            follow_redirects=False,
        )


        require(
            redirect_ok(
                response
            ),

            "Second Alumni creation failed.",
        )


    conn = (
        database.get_db_connection()
    )


    first_after = (
        conn.execute(
            """
            SELECT
                is_spotlight

            FROM alumni_profiles

            WHERE alumni_id = ?
            """,
            (
                first_id,
            ),
        ).fetchone()
    )


    second = (
        conn.execute(
            """
            SELECT
                alumni_profiles.*,

                people.first_name,

                people.last_name

            FROM alumni_profiles


            JOIN people

                ON alumni_profiles.person_id =
                   people.person_id


            WHERE alumni_profiles.slug = ?
            """,
            (
                "task-six-alumni-two",
            ),
        ).fetchone()
    )


    require(
        second is not None,
        "Second Alumni profile missing.",
    )


    require(

        first_after[
            "is_spotlight"
        ] == 0,

        "Previous Spotlight was "
        "not automatically cleared.",

    )


    require(

        second[
            "is_spotlight"
        ] == 1

        and second[
            "is_public"
        ] == 1

        and second[
            "is_featured"
        ] == 1,

        "New Spotlight did not "
        "force Public + Featured.",

    )


    second_id = (
        second[
            "alumni_id"
        ]
    )


    second_person_id = (
        second[
            "person_id"
        ]
    )


    spotlight_count = (
        conn.execute(
            """
            SELECT
                COUNT(*)

            FROM alumni_profiles

            WHERE is_spotlight = 1
            """
        ).fetchone()[0]
    )


    require(

        spotlight_count == 1,

        "There is not exactly "
        "one Spotlight profile.",

    )


    conn.close()


    print(
        "Automatic single "
        "Spotlight replacement: OK"
    )


    # ========================================================
    # EDIT
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            manager[
                "user_id"
            ],
        )


        response = client.post(
            f"/alumni/{first_id}/edit",

            data={

                "first_name":
                    "TaskSix",

                "last_name":
                    "AlumniOneEdited",

                "email":
                    "tasksix.one@example.test",

                "university":
                    "USTHB",

                "category":
                    "INDUSTRY",

                "graduation_year":
                    "2025",

                "headline":
                    "Optimization in industry",

                "current_title":
                    "Operations Research Analyst",

                "current_organization":
                    "Test Industry",

                "short_bio":
                    "Edited temporary profile.",

                "story":
                    "Edited story.",

                "linkedin_url":
                    "https://example.com/edited",

                "website_url":
                    "",

                "slug":
                    "task-six-alumni-one-edited",

                "display_order":
                    "3",

                "is_public":
                    "1",
            },

            follow_redirects=False,
        )


        require(
            redirect_ok(
                response
            ),

            "Alumni edit failed.",
        )


    conn = (
        database.get_db_connection()
    )


    edited = (
        conn.execute(
            """
            SELECT
                alumni_profiles.*,

                people.first_name,

                people.last_name

            FROM alumni_profiles


            JOIN people

                ON alumni_profiles.person_id =
                   people.person_id


            WHERE alumni_profiles.alumni_id = ?
            """,
            (
                first_id,
            ),
        ).fetchone()
    )


    require(

        edited[
            "last_name"
        ] == "AlumniOneEdited"

        and edited[
            "category"
        ] == "INDUSTRY"

        and edited[
            "slug"
        ] == "task-six-alumni-one-edited"

        and edited[
            "is_public"
        ] == 1

        and edited[
            "is_spotlight"
        ] == 0,

        "Alumni edit did not "
        "persist correctly.",

    )


    conn.close()


    print(
        "Alumni edit: OK"
    )


    # ========================================================
    # FILTERS
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            manager[
                "user_id"
            ],
        )


        response = client.get(
            "/alumni"
            "?category=INDUSTRY"
            "&visibility=PUBLIC"
        )


        require(
            response.status_code
            == 200,

            "Alumni filters failed.",
        )


        body = (
            response.get_data(
                as_text=True
            )
        )


        require(

            "AlumniOneEdited"
            in body,

            "Filtered Alumni profile "
            "missing from list.",

        )


    print(
        "Alumni CMS filters: OK"
    )


    # ========================================================
    # DELETE SECOND PROFILE
    # PERSON MUST STAY
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            manager[
                "user_id"
            ],
        )


        response = client.post(
            f"/alumni/{second_id}/delete",

            data={
                "confirmation":
                    "TaskSix AlumniTwo",
            },

            follow_redirects=False,
        )


        require(
            redirect_ok(
                response
            ),

            "Alumni profile deletion failed.",
        )


    conn = (
        database.get_db_connection()
    )


    deleted_profile = (
        conn.execute(
            """
            SELECT
                alumni_id

            FROM alumni_profiles

            WHERE alumni_id = ?
            """,
            (
                second_id,
            ),
        ).fetchone()
    )


    preserved_person = (
        conn.execute(
            """
            SELECT
                person_id

            FROM people

            WHERE person_id = ?
            """,
            (
                second_person_id,
            ),
        ).fetchone()
    )


    require(
        deleted_profile is None,

        "Deleted Alumni profile "
        "still exists.",
    )


    require(
        preserved_person is not None,

        "Deleting Alumni profile "
        "deleted the person.",
    )


    conn.close()


    print(
        "Delete profile while "
        "preserving person/history: OK"
    )


    # ========================================================
    # DELETE EXISTING PERSON PROFILE
    # PERSON MUST ALSO STAY
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            manager[
                "user_id"
            ],
        )


        response = client.post(
            f"/alumni/{existing_profile_id}/delete",

            data={
                "confirmation":
                    "Existing AlumniCandidate",
            },

            follow_redirects=False,
        )


        require(
            redirect_ok(
                response
            ),

            "Existing-person Alumni "
            "deletion failed.",
        )


    conn = (
        database.get_db_connection()
    )


    preserved_existing_person = (
        conn.execute(
            """
            SELECT
                person_id

            FROM people

            WHERE person_id = ?
            """,
            (
                existing_person_id,
            ),
        ).fetchone()
    )


    require(
        preserved_existing_person
        is not None,

        "Deleting existing-person "
        "Alumni profile deleted "
        "the person.",
    )


    print(
        "Existing-person profile "
        "deletion preserves person: OK"
    )


    # ========================================================
    # DATABASE HEALTH
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


    require(
        integrity == "ok",
        "Integrity check failed.",
    )


    require(
        not foreign_keys,
        "Foreign key check failed.",
    )


    conn.close()


    print()

    print(
        "========================================"
    )

    print(
        "ALUMNI CMS TEST SUCCESSFUL"
    )

    print(
        "========================================"
    )


    print(
        "Anonymous protection: OK"
    )

    print(
        "CMS view/manage permissions: OK"
    )

    print(
        "Create from existing person: OK"
    )

    print(
        "Create older Alumni "
        "without history: OK"
    )

    print(
        "Photo upload/view: OK"
    )

    print(
        "Edit Alumni: OK"
    )

    print(
        "Public/Featured/Spotlight "
        "management: OK"
    )

    print(
        "Single Spotlight "
        "replacement: OK"
    )

    print(
        "Category/visibility filters: OK"
    )

    print(
        "Delete profile preserves "
        "person/history: OK"
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

    for filename in (
        created_photos
    ):

        path = (
            ALUMNI_UPLOADS
            / filename
        )


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