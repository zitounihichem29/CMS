from app import app
from database import get_db_connection
from context import get_active_term_id


conn = get_db_connection()
active_term_id = get_active_term_id()


user = conn.execute("""
    SELECT
        users.user_id,
        users.username,
        roles.name AS role_name,
        memberships.department_id

    FROM users

    JOIN memberships
        ON users.person_id = memberships.person_id

    JOIN roles
        ON memberships.role_id = roles.role_id

    WHERE memberships.term_id = ?
      AND users.is_active = 1

      AND (
            roles.name IN (
                'PRESIDENT',
                'VICE_PRESIDENT'
            )

            OR (
                roles.name = 'HEAD'
                AND memberships.department_id = 1
            )
      )

    ORDER BY users.user_id
    LIMIT 1
""", (
    active_term_id,
)).fetchone()


conn.close()


if user is None:
    raise RuntimeError(
        "No President, Vice-President or HR Head "
        "with an active CMS account was found."
    )


print(
    "Testing with:",
    user["username"],
    "-",
    user["role_name"]
)


with app.test_client() as client:

    with client.session_transaction() as session:
        session["user_id"] = user["user_id"]


    if (
        user["role_name"] == "HEAD"
        and user["department_id"] == 1
    ):

        response = client.get(
            "/dashboard?scope=club"
        )

    else:

        response = client.get(
            "/dashboard"
        )


    print(
        "Status code:",
        response.status_code
    )


    if response.status_code == 200:

        print(
            "DASHBOARD TEST SUCCESSFUL"
        )

    else:

        print(
            response.get_data(
                as_text=True
            )[:1000]
        )