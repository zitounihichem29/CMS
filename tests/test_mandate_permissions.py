from database import get_db_connection

from routes.mandates import (
    can_view_mandates,
    can_create_draft,
    can_edit_draft_basic_info,
    can_manage_election,
    can_edit_draft_board,
    can_approve_as_president,
    can_approve_as_vice_president,
    can_activate_draft,
    can_delete_draft,
    can_emergency_manage_mandates,
)


# ============================================================
# DATABASE
# ============================================================

conn = get_db_connection()


active_term = conn.execute("""
    SELECT term_id, name
    FROM terms
    WHERE status = 'ACTIVE'
    LIMIT 1
""").fetchone()


if active_term is None:
    conn.close()
    raise RuntimeError(
        "No ACTIVE mandate found."
    )


ACTIVE_TERM_ID = active_term["term_id"]


print(
    "ACTIVE mandate:",
    active_term["name"]
)


# ============================================================
# USER LOADER
# ============================================================

def get_user_for_role(
    role_name,
    department_id=None
):

    sql = """
        SELECT
            users.user_id,
            users.username,
            users.is_active,
            users.is_platform_admin,

            memberships.membership_id,

            roles.name AS role_name,

            departments.department_id,
            departments.name AS department_name,

            CASE
                WHEN memberships.membership_id IS NULL
                    THEN 1

                WHEN roles.name = 'ALUMNI'
                    THEN 1

                ELSE 0
            END AS is_alumni

        FROM users

        JOIN people
            ON users.person_id =
               people.person_id

        JOIN memberships
            ON people.person_id =
               memberships.person_id

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        LEFT JOIN departments
            ON memberships.department_id =
               departments.department_id

        WHERE users.is_active = 1
          AND users.is_platform_admin = 0
          AND memberships.term_id = ?
          AND roles.name = ?
    """

    params = [
        ACTIVE_TERM_ID,
        role_name,
    ]


    if department_id is not None:

        sql += """
            AND memberships.department_id = ?
        """

        params.append(
            department_id
        )


    sql += """
        ORDER BY users.user_id
        LIMIT 1
    """


    return conn.execute(
        sql,
        params
    ).fetchone()


def get_platform_admin():

    return conn.execute("""
        SELECT
            users.user_id,
            users.username,
            users.is_active,
            users.is_platform_admin,

            memberships.membership_id,

            roles.name AS role_name,

            departments.department_id,
            departments.name AS department_name,

            CASE
                WHEN memberships.membership_id IS NULL
                    THEN 1

                WHEN roles.name = 'ALUMNI'
                    THEN 1

                ELSE 0
            END AS is_alumni

        FROM users

        JOIN people
            ON users.person_id =
               people.person_id

        LEFT JOIN memberships
            ON people.person_id =
               memberships.person_id
            AND memberships.term_id = ?

        LEFT JOIN roles
            ON memberships.role_id =
               roles.role_id

        LEFT JOIN departments
            ON memberships.department_id =
               departments.department_id

        WHERE users.is_active = 1
          AND users.is_platform_admin = 1

        ORDER BY users.user_id

        LIMIT 1
    """, (
        ACTIVE_TERM_ID,
    )).fetchone()


# ============================================================
# LOAD TEST USERS
# ============================================================

president = get_user_for_role(
    "PRESIDENT"
)

vice_president = get_user_for_role(
    "VICE_PRESIDENT"
)

hr_head = get_user_for_role(
    "HEAD",
    1
)

platform_admin = get_platform_admin()


missing = []


if president is None:
    missing.append(
        "President"
    )

if vice_president is None:
    missing.append(
        "Vice-President"
    )

if hr_head is None:
    missing.append(
        "HR Head"
    )

if platform_admin is None:
    missing.append(
        "Platform Admin"
    )


if missing:

    conn.close()

    raise RuntimeError(
        "Missing test users: "
        + ", ".join(missing)
    )


# ============================================================
# PERMISSION FUNCTIONS
# ============================================================

permission_functions = {

    "view":
        can_view_mandates,

    "create_draft":
        can_create_draft,

    "edit_basic_info":
        can_edit_draft_basic_info,

    "manage_election":
        can_manage_election,

    "edit_board":
        can_edit_draft_board,

    "approve_president":
        can_approve_as_president,

    "approve_vp":
        can_approve_as_vice_president,

    "activate":
        can_activate_draft,

    "delete_draft":
        can_delete_draft,

    "emergency":
        can_emergency_manage_mandates,
}


# ============================================================
# EXPECTED MATRIX
# ============================================================

tests = [

    (
        "OUTGOING PRESIDENT",
        president,
        {
            "view": True,
            "create_draft": True,
            "edit_basic_info": True,
            "manage_election": True,
            "edit_board": False,
            "approve_president": True,
            "approve_vp": False,
            "activate": True,
            "delete_draft": True,
            "emergency": False,
        }
    ),

    (
        "OUTGOING VICE-PRESIDENT",
        vice_president,
        {
            "view": True,
            "create_draft": True,
            "edit_basic_info": True,
            "manage_election": True,
            "edit_board": False,
            "approve_president": False,
            "approve_vp": True,
            "activate": False,
            "delete_draft": False,
            "emergency": False,
        }
    ),

    (
        "HR HEAD",
        hr_head,
        {
            "view": True,
            "create_draft": False,
            "edit_basic_info": False,
            "manage_election": False,
            "edit_board": True,
            "approve_president": False,
            "approve_vp": False,
            "activate": False,
            "delete_draft": False,
            "emergency": False,
        }
    ),

    (
        "PLATFORM ADMIN",
        platform_admin,
        {
            "view": True,
            "create_draft": True,
            "edit_basic_info": True,
            "manage_election": True,
            "edit_board": True,
            "approve_president": True,
            "approve_vp": True,
            "activate": True,
            "delete_draft": True,
            "emergency": True,
        }
    ),
]


# ============================================================
# RUN TESTS
# ============================================================

failures = []


for label, user, expected in tests:

    print()
    print(
        "========================================"
    )

    print(
        label
    )

    print(
        "Username:",
        user["username"]
    )

    print(
        "Current role:",
        user["role_name"]
    )

    print(
        "Department:",
        user["department_name"]
    )

    print(
        "Platform Admin:",
        bool(
            user["is_platform_admin"]
        )
    )

    print(
        "----------------------------------------"
    )


    for permission_name, function in (
        permission_functions.items()
    ):

        actual = bool(
            function(user)
        )

        expected_value = expected[
            permission_name
        ]

        status = (
            "OK"
            if actual == expected_value
            else "FAIL"
        )


        print(
            f"{permission_name:20} "
            f"expected={str(expected_value):5} "
            f"actual={str(actual):5} "
            f"{status}"
        )


        if actual != expected_value:

            failures.append(
                (
                    label,
                    permission_name,
                    expected_value,
                    actual,
                )
            )


# ============================================================
# FINAL RESULT
# ============================================================

conn.close()


print()
print(
    "========================================"
)
print(
    "MANDATE PERMISSION TEST SUMMARY"
)
print(
    "========================================"
)


if failures:

    print(
        "Failures:",
        len(failures)
    )

    for failure in failures:

        print(
            failure
        )

    raise RuntimeError(
        "Mandate permission matrix failed."
    )


print(
    "Failures: 0"
)

print()
print(
    "MANDATE PERMISSION MATRIX SUCCESSFUL"
)