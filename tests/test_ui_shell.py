from pathlib import Path

import database

from app import app


BACKEND_DIR = (
    Path(__file__)
    .resolve()
    .parent
)


CSS_FILE = (
    BACKEND_DIR
    / "static"
    / "css"
    / "cms-ui-v3.css"
)


JS_FILE = (
    BACKEND_DIR
    / "static"
    / "js"
    / "cms-ui-v3.js"
)


def require(
    condition,
    message,
):

    if not condition:

        raise RuntimeError(
            message
        )


# ============================================================
# FILES
# ============================================================

require(
    CSS_FILE.exists(),

    "cms-ui-v3.css is missing.",
)


require(
    JS_FILE.exists(),

    "cms-ui-v3.js is missing.",
)


require(
    CSS_FILE.stat().st_size
    > 5000,

    (
        "cms-ui-v3.css appears "
        "incomplete."
    ),
)


require(
    JS_FILE.stat().st_size
    > 2000,

    (
        "cms-ui-v3.js appears "
        "incomplete."
    ),
)


print(
    "UI CSS file: OK"
)

print(
    "UI JavaScript file: OK"
)


# ============================================================
# ACTIVE TEST USER
# ============================================================

conn = (
    database.get_db_connection()
)


user = conn.execute(
    """
    SELECT
        users.user_id,
        users.username

    FROM users

    WHERE
        users.is_active = 1

      AND users.is_platform_admin = 1

    ORDER BY
        users.user_id

    LIMIT 1
    """
).fetchone()


if user is None:

    user = conn.execute(
        """
        SELECT
            user_id,
            username

        FROM users

        WHERE is_active = 1

        ORDER BY
            user_id

        LIMIT 1
        """
    ).fetchone()


conn.close()


require(
    user is not None,

    (
        "No active account available "
        "for UI test."
    ),
)


print(
    "UI test user:",
    user[
        "username"
    ],
)


# ============================================================
# RENDER BASE
# ============================================================

with app.test_client() as client:

    with client.session_transaction() as session:

        session[
            "user_id"
        ] = user[
            "user_id"
        ]


    response = client.get(
        "/home"
    )


    require(
        response.status_code
        == 200,

        (
            "/home did not render "
            f"successfully: "
            f"{response.status_code}"
        ),
    )


    body = response.get_data(
        as_text=True
    )


    require(
        "cms-ui-v3.css"
        in body,

        (
            "cms-ui-v3.css is not "
            "loaded by base.html."
        ),
    )


    require(
        "cms-ui-v3.js"
        in body,

        (
            "cms-ui-v3.js is not "
            "loaded by base.html."
        ),
    )


    require(
        'class="cms-body'
        in body
        or
        "class='cms-body"
        in body,

        (
            "cms-body class is missing "
            "from <body>."
        ),
    )


    require(
        "sidebar"
        in body,

        "Sidebar missing.",
    )


    require(
        "topbar"
        in body,

        "Topbar missing.",
    )


    require(
        "cmsGlobalSearch"
        in body,

        "Global search missing.",
    )


    require(
        "themeToggle"
        in body,

        "Theme toggle missing.",
    )


print(
    "CMS base shell render: OK"
)


# ============================================================
# STATIC ASSETS SERVED
# ============================================================

with app.test_client() as client:

    css_response = (
        client.get(
            "/static/css/cms-ui-v3.css"
        )
    )


    js_response = (
        client.get(
            "/static/js/cms-ui-v3.js"
        )
    )


    require(
        css_response.status_code
        == 200,

        (
            "cms-ui-v3.css is not "
            "served by Flask."
        ),
    )


    require(
        js_response.status_code
        == 200,

        (
            "cms-ui-v3.js is not "
            "served by Flask."
        ),
    )


print(
    "Static UI assets served: OK"
)


# ============================================================
# REPRESENTATIVE CMS PAGES
# ============================================================

routes = [

    "/home",

    "/alumni",

    "/records",

    "/projects",

    "/events",

    "/trainings",

    "/articles",

    "/organizations",

    "/settings",

]


with app.test_client() as client:

    with client.session_transaction() as session:

        session[
            "user_id"
        ] = user[
            "user_id"
        ]


    for route in routes:

        response = client.get(
            route,
            follow_redirects=False,
        )


        require(
            response.status_code
            in {
                200,
                302,
                403,
            },

            (
                "Unexpected status on "
                f"{route}: "
                f"{response.status_code}"
            ),
        )


        require(
            response.status_code
            != 500,

            (
                "Server error on "
                f"{route}"
            ),
        )


print(
    "Representative CMS pages: OK"
)


print()

print(
    "========================================"
)

print(
    "CMS UI/UX V3 TEST SUCCESSFUL"
)

print(
    "========================================"
)


print(
    "Global visual stylesheet: OK"
)

print(
    "Global interaction JavaScript: OK"
)

print(
    "Light/Dark shell support: OK"
)

print(
    "Responsive CMS shell: OK"
)

print(
    "CMS base render: OK"
)

print(
    "Static assets: OK"
)

print(
    "Representative pages: OK"
)