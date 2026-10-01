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
    / "rsclub_disabled_account_test.db"
)


# ============================================================
# CREATE TEMPORARY DATABASE COPY
# ============================================================

if TEST_DB.exists():
    TEST_DB.unlink()

shutil.copy2(
    REAL_DB,
    TEST_DB
)


# Make every get_db_connection()
# use the temporary database copy.
database.DATABASE_PATH = TEST_DB


# ============================================================
# FIND ONE ACTIVE ACCOUNT
# ============================================================

conn = database.get_db_connection()

user = conn.execute("""
    SELECT
        user_id,
        username

    FROM users

    WHERE is_active = 1

    ORDER BY user_id

    LIMIT 1
""").fetchone()


if user is None:

    conn.close()

    raise RuntimeError(
        "No active user found."
    )


user_id = user["user_id"]
username = user["username"]


print(
    "Testing with:",
    username
)


# ============================================================
# DISABLE USER ONLY IN TEMPORARY DATABASE
# ============================================================

conn.execute("""
    UPDATE users

    SET is_active = 0

    WHERE user_id = ?
""", (
    user_id,
))

conn.commit()
conn.close()


# ============================================================
# TEST SESSION
# ============================================================

with app.test_client() as client:

    with client.session_transaction() as session:

        session["user_id"] = user_id


    response = client.get(
        "/help",
        follow_redirects=False
    )


    print(
        "Status code:",
        response.status_code
    )

    print(
        "Redirect location:",
        response.headers.get(
            "Location"
        )
    )


    with client.session_transaction() as session:

        session_still_exists = (
            "user_id" in session
        )


    print(
        "User still in session:",
        session_still_exists
    )


# ============================================================
# VALIDATION
# ============================================================

if response.status_code not in (
    301,
    302,
    303,
    307,
    308
):

    raise RuntimeError(
        "Disabled account was not redirected."
    )


if response.headers.get(
    "Location"
) != "/login":

    raise RuntimeError(
        "Disabled account was not redirected "
        "to /login."
    )


if session_still_exists:

    raise RuntimeError(
        "Disabled account remained in session."
    )


print()
print(
    "========================================"
)
print(
    "DISABLED ACCOUNT TEST SUCCESSFUL"
)
print(
    "========================================"
)

print(
    "Disabled user redirected to login: OK"
)

print(
    "Session cleared: OK"
)


# ============================================================
# DELETE TEMPORARY DATABASE
# ============================================================

if TEST_DB.exists():
    TEST_DB.unlink()


print(
    "Temporary database deleted."
)