import shutil
from pathlib import Path

import database
from app import app


# ============================================================
# PATHS
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parent

REAL_DB = (
    BACKEND_DIR.parent
    / "database"
    / "rsclub.db"
)

TEST_DB = (
    BACKEND_DIR.parent
    / "database"
    / "member_optional_account_test.db"
)


# ============================================================
# HELPERS
# ============================================================

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

        session["user_id"] = (
            user_id
        )


def is_redirect(response):

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


# ============================================================
# CREATE TEMPORARY DATABASE
# ============================================================

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

    # ========================================================
    # ACTIVE TERM + HR HEAD
    # ========================================================

    conn = (
        database.get_db_connection()
    )


    active_term = conn.execute(
        """
        SELECT
            term_id,
            name,
            status

        FROM terms

        WHERE status = 'ACTIVE'

        LIMIT 1
        """
    ).fetchone()


    require(
        active_term is not None,
        "ACTIVE mandate not found.",
    )


    require(
        active_term["name"]
        == "2025/2026",
        (
            "Expected ACTIVE mandate "
            "2025/2026."
        ),
    )


    hr_manager = conn.execute(
        """
        SELECT
            users.user_id,
            users.username,

            people.person_id,
            people.first_name,
            people.last_name,

            memberships.membership_id,

            roles.name
                AS role_name,

            departments.name
                AS department_name,

            departments.department_id

        FROM users

        JOIN people

            ON people.person_id =
               users.person_id

        JOIN memberships

            ON memberships.person_id =
               people.person_id

        JOIN roles

            ON roles.role_id =
               memberships.role_id

        LEFT JOIN departments

            ON departments.department_id =
               memberships.department_id

        WHERE
            memberships.term_id = ?

          AND users.is_active = 1

          AND departments.name =
              'Human Resources'

          AND roles.name IN (
              'HEAD',
              'SUB_HEAD'
          )

        ORDER BY
            CASE roles.name
                WHEN 'HEAD' THEN 1
                ELSE 2
            END

        LIMIT 1
        """,
        (
            active_term[
                "term_id"
            ],
        ),
    ).fetchone()


    require(
        hr_manager is not None,
        (
            "No active HR HEAD/SUB_HEAD "
            "account found."
        ),
    )


    department = conn.execute(
        """
        SELECT
            department_id,
            name

        FROM departments

        WHERE name =
            'Projects & Activities'

        LIMIT 1
        """
    ).fetchone()


    require(
        department is not None,
        (
            "Projects & Activities "
            "department not found."
        ),
    )


    conn.close()


    print(
        "Active mandate:",
        active_term["name"],
    )

    print(
        "HR manager:",
        hr_manager["username"],
        "-",
        hr_manager["role_name"],
    )


    # ========================================================
    # GET FORM
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            hr_manager[
                "user_id"
            ],
        )


        response = client.get(
            "/members/add"
        )


        require(
            response.status_code
            == 200,
            (
                "HR cannot open "
                "/members/add."
            ),
        )


        html = response.get_data(
            as_text=True
        )


        require(
            'name="create_account"'
            in html,
            (
                "create_account checkbox "
                "missing from form."
            ),
        )


        require(
            (
                "Create a CMS account "
                "for this member"
            )
            in html,
            (
                "Optional account label "
                "missing."
            ),
        )


    print(
        "Add Person form: OK"
    )


    # ========================================================
    # TEST 1
    # MEMBER WITHOUT CMS ACCOUNT
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            hr_manager[
                "user_id"
            ],
        )


        response = client.post(
            "/members/add",

            data={
                "person_type":
                    "member",

                "first_name":
                    "Temporary",

                "last_name":
                    "NoAccount",

                "department_id":
                    str(
                        department[
                            "department_id"
                        ]
                    ),

                # create_account
                # intentionally absent

                # username/password
                # intentionally absent
            },

            follow_redirects=False,
        )


        require(
            is_redirect(
                response
            ),
            (
                "Member without CMS "
                "account was not created."
            ),
        )


    conn = (
        database.get_db_connection()
    )


    no_account_person = conn.execute(
        """
        SELECT
            person_id

        FROM people

        WHERE first_name =
              'Temporary'

          AND last_name =
              'NoAccount'

        LIMIT 1
        """
    ).fetchone()


    require(
        no_account_person
        is not None,
        (
            "Person without account "
            "was not created."
        ),
    )


    no_account_membership = (
        conn.execute(
            """
            SELECT
                memberships.membership_id,

                roles.name
                    AS role_name,

                departments.name
                    AS department_name

            FROM memberships

            JOIN roles

                ON roles.role_id =
                   memberships.role_id

            LEFT JOIN departments

                ON departments.department_id =
                   memberships.department_id

            WHERE
                memberships.person_id = ?

              AND memberships.term_id = ?

            LIMIT 1
            """,
            (
                no_account_person[
                    "person_id"
                ],

                active_term[
                    "term_id"
                ],
            ),
        ).fetchone()
    )


    require(
        no_account_membership
        is not None,
        (
            "Membership without account "
            "was not created."
        ),
    )


    require(
        no_account_membership[
            "role_name"
        ]
        == "MEMBER",
        (
            "Member received wrong role."
        ),
    )


    require(
        no_account_membership[
            "department_name"
        ]
        ==
        "Projects & Activities",
        (
            "Member received wrong "
            "department."
        ),
    )


    no_account_user = (
        conn.execute(
            """
            SELECT
                user_id

            FROM users

            WHERE person_id = ?

            LIMIT 1
            """,
            (
                no_account_person[
                    "person_id"
                ],
            ),
        ).fetchone()
    )


    require(
        no_account_user
        is None,
        (
            "A USER account was created "
            "even though create_account "
            "was unchecked."
        ),
    )


    conn.close()


    print(
        "Member without CMS account: OK"
    )


    # ========================================================
    # TEST 2
    # MEMBER WITH CMS ACCOUNT
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            hr_manager[
                "user_id"
            ],
        )


        response = client.post(
            "/members/add",

            data={
                "person_type":
                    "member",

                "first_name":
                    "Temporary",

                "last_name":
                    "WithAccount",

                "department_id":
                    str(
                        department[
                            "department_id"
                        ]
                    ),

                "create_account":
                    "1",

                "username":
                    "temporary_member_test",

                "password":
                    "Temporary-Test-Password-2026",
            },

            follow_redirects=False,
        )


        require(
            is_redirect(
                response
            ),
            (
                "Member with CMS account "
                "was not created."
            ),
        )


    conn = (
        database.get_db_connection()
    )


    with_account_person = conn.execute(
        """
        SELECT
            person_id

        FROM people

        WHERE first_name =
              'Temporary'

          AND last_name =
              'WithAccount'

        LIMIT 1
        """
    ).fetchone()


    require(
        with_account_person
        is not None,
        (
            "Person with account "
            "was not created."
        ),
    )


    with_account_membership = (
        conn.execute(
            """
            SELECT
                memberships.membership_id,

                roles.name
                    AS role_name

            FROM memberships

            JOIN roles

                ON roles.role_id =
                   memberships.role_id

            WHERE
                memberships.person_id = ?

              AND memberships.term_id = ?

            LIMIT 1
            """,
            (
                with_account_person[
                    "person_id"
                ],

                active_term[
                    "term_id"
                ],
            ),
        ).fetchone()
    )


    require(
        with_account_membership
        is not None,
        (
            "Membership with account "
            "was not created."
        ),
    )


    require(
        with_account_membership[
            "role_name"
        ]
        == "MEMBER",
        (
            "Account member received "
            "wrong role."
        ),
    )


    created_user = conn.execute(
        """
        SELECT
            user_id,
            username,
            is_active

        FROM users

        WHERE person_id = ?

        LIMIT 1
        """,
        (
            with_account_person[
                "person_id"
            ],
        ),
    ).fetchone()


    require(
        created_user is not None,
        (
            "CMS USER account "
            "was not created."
        ),
    )


    require(
        created_user[
            "username"
        ]
        ==
        "temporary_member_test",
        (
            "Wrong username created."
        ),
    )


    require(
        created_user[
            "is_active"
        ]
        == 1,
        (
            "Created account "
            "is not active."
        ),
    )


    conn.close()


    print(
        "Member with CMS account: OK"
    )


    # ========================================================
    # TEST 3
    # CHECKBOX WITHOUT CREDENTIALS
    # ========================================================

    with app.test_client() as client:

        login(
            client,
            hr_manager[
                "user_id"
            ],
        )


        response = client.post(
            "/members/add",

            data={
                "person_type":
                    "member",

                "first_name":
                    "Temporary",

                "last_name":
                    "MissingCredentials",

                "department_id":
                    str(
                        department[
                            "department_id"
                        ]
                    ),

                "create_account":
                    "1",

                "username":
                    "",

                "password":
                    "",
            },

            follow_redirects=False,
        )


        require(
            response.status_code
            == 400,
            (
                "Missing username/password "
                "should return HTTP 400."
            ),
        )


    conn = (
        database.get_db_connection()
    )


    invalid_person_count = (
        conn.execute(
            """
            SELECT COUNT(*)

            FROM people

            WHERE first_name =
                  'Temporary'

              AND last_name =
                  'MissingCredentials'
            """
        ).fetchone()[0]
    )


    require(
        invalid_person_count
        == 0,
        (
            "Invalid member created a "
            "PEOPLE row before validation."
        ),
    )


    # ========================================================
    # DATABASE HEALTH
    # ========================================================

    integrity = conn.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]


    foreign_keys = conn.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()


    conn.close()


    require(
        integrity == "ok",
        (
            "Integrity check failed."
        ),
    )


    require(
        not foreign_keys,
        (
            "Foreign key violations "
            "detected."
        ),
    )


    print(
        "Missing credentials validation: OK"
    )


    print()

    print(
        "========================================"
    )

    print(
        "OPTIONAL MEMBER ACCOUNT TEST SUCCESSFUL"
    )

    print(
        "========================================"
    )

    print(
        "Form checkbox: OK"
    )

    print(
        "Member without account: OK"
    )

    print(
        "Member with account: OK"
    )

    print(
        "Required credentials when checked: OK"
    )

    print(
        "2025/2026 remained ACTIVE: OK"
    )

    print(
        "Real database untouched: OK"
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

    if TEST_DB.exists():

        TEST_DB.unlink()


    print(
        "Temporary database deleted."
    )