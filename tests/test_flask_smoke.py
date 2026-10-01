from app import app
from database import get_db_connection
from context import get_active_term_id


# ============================================================
# CONFIGURATION
# ============================================================

ALLOWED_STATUS_CODES = {
    200,  # OK
    301, 302, 303, 307, 308,  # Redirects
    401,  # Authentication required
    403,  # Permission denied
}


SKIPPED_ENDPOINTS = {
    "static",
    "logout",
    "test",
    "test_user",
}


# ============================================================
# DATABASE / ACTIVE TERM
# ============================================================

conn = get_db_connection()

active_term_id = get_active_term_id()

if active_term_id is None:
    conn.close()
    raise RuntimeError(
        "No ACTIVE mandate found."
    )


term = conn.execute("""
    SELECT
        term_id,
        name,
        status

    FROM terms

    WHERE term_id = ?
""", (
    active_term_id,
)).fetchone()


print(
    "Active mandate:",
    term["name"],
    "-",
    term["status"]
)


# ============================================================
# FIND ONE ACTIVE CURRENT MEMBER
# ============================================================

user = conn.execute("""
    SELECT
        users.user_id,
        users.username,
        roles.name AS role_name,
        departments.name AS department_name

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
      AND memberships.term_id = ?
      AND roles.name != 'ALUMNI'

    ORDER BY users.user_id

    LIMIT 1
""", (
    active_term_id,
)).fetchone()


conn.close()


if user is None:
    raise RuntimeError(
        "No active current member account found."
    )


print(
    "Authenticated test user:",
    user["username"],
    "-",
    user["role_name"]
)


# ============================================================
# ROUTES TO TEST
# ============================================================

routes = []


for rule in app.url_map.iter_rules():

    # Only GET routes
    if "GET" not in rule.methods:
        continue

    # Skip routes requiring URL parameters:
    # /members/<id>, /events/<id>, etc.
    if rule.arguments:
        continue

    # Skip Flask static files
    if rule.endpoint == "static":
        continue

    # Skip development/test/session-changing routes
    if (
        rule.rule == "/logout"
        or rule.rule == "/test"
        or rule.rule == "/test-user"
    ):
        continue

    routes.append(
        (
            rule.rule,
            rule.endpoint
        )
    )


routes = sorted(
    set(routes),
    key=lambda item: item[0]
)


print()
print(
    "Static GET routes found:",
    len(routes)
)


# ============================================================
# TEST FUNCTION
# ============================================================

def run_test(
    client,
    route,
    mode
):

    try:

        response = client.get(
            route,
            follow_redirects=False
        )

        status = response.status_code

        if status >= 500:

            return {
                "route": route,
                "status": status,
                "mode": mode,
                "result": "SERVER ERROR",
            }

        if status not in ALLOWED_STATUS_CODES:

            return {
                "route": route,
                "status": status,
                "mode": mode,
                "result": "UNEXPECTED STATUS",
            }

        return {
            "route": route,
            "status": status,
            "mode": mode,
            "result": "OK",
        }

    except Exception as error:

        return {
            "route": route,
            "status": "EXCEPTION",
            "mode": mode,
            "result": repr(error),
        }


# ============================================================
# PUBLIC / ANONYMOUS TEST
# ============================================================

print()
print(
    "========================================"
)
print(
    "ANONYMOUS SMOKE TEST"
)
print(
    "========================================"
)


anonymous_results = []


with app.test_client() as client:

    for route, endpoint in routes:

        result = run_test(
            client,
            route,
            "anonymous"
        )

        anonymous_results.append(
            result
        )

        print(
            f"{str(result['status']):>9}  "
            f"{route}"
        )


# ============================================================
# AUTHENTICATED TEST
# ============================================================

print()
print(
    "========================================"
)
print(
    "AUTHENTICATED SMOKE TEST"
)
print(
    "========================================"
)


authenticated_results = []


with app.test_client() as client:

    with client.session_transaction() as session:

        session["user_id"] = (
            user["user_id"]
        )


    for route, endpoint in routes:

        result = run_test(
            client,
            route,
            "authenticated"
        )

        authenticated_results.append(
            result
        )

        print(
            f"{str(result['status']):>9}  "
            f"{route}"
        )


# ============================================================
# RESULTS
# ============================================================

all_results = (
    anonymous_results
    + authenticated_results
)


errors = [
    result
    for result in all_results
    if result["result"] != "OK"
]


server_errors = [
    result
    for result in all_results
    if (
        isinstance(
            result["status"],
            int
        )
        and result["status"] >= 500
    )
]


exceptions = [
    result
    for result in all_results
    if result["status"] == "EXCEPTION"
]


print()
print(
    "========================================"
)
print(
    "SMOKE TEST SUMMARY"
)
print(
    "========================================"
)

print(
    "Routes tested:",
    len(routes)
)

print(
    "Total requests:",
    len(all_results)
)

print(
    "Server errors:",
    len(server_errors)
)

print(
    "Exceptions:",
    len(exceptions)
)

print(
    "Other unexpected statuses:",
    len(errors)
    - len(server_errors)
    - len(exceptions)
)


if errors:

    print()
    print(
        "PROBLEMS FOUND:"
    )

    for error in errors:

        print(
            f"- [{error['mode']}] "
            f"{error['route']} "
            f"-> {error['status']} "
            f"{error['result']}"
        )


if server_errors or exceptions:

    raise RuntimeError(
        "Smoke test failed."
    )


print()
print(
    "========================================"
)
print(
    "FLASK SMOKE TEST SUCCESSFUL"
)
print(
    "========================================"
)

print(
    "No HTTP 500 errors: OK"
)

print(
    "No unhandled exceptions: OK"
)

print(
    "Application import: OK"
)

print(
    "Database access: OK"
)

print(
    "Active mandate: OK"
)