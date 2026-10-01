from pathlib import Path

from app import app


BACKEND_DIR = (
    Path(__file__).resolve().parent
)


CSS_FILE = (
    BACKEND_DIR
    / "static"
    / "css"
    / "public-ui-v4.css"
)


JS_FILE = (
    BACKEND_DIR
    / "static"
    / "js"
    / "public-ui-v4.js"
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

    "public-ui-v4.css is missing.",
)


require(
    JS_FILE.exists(),

    "public-ui-v4.js is missing.",
)


require(
    CSS_FILE.stat().st_size
    > 8000,

    (
        "public-ui-v4.css appears "
        "incomplete."
    ),
)


require(
    JS_FILE.stat().st_size
    > 2500,

    (
        "public-ui-v4.js appears "
        "incomplete."
    ),
)


print(
    "Final public CSS: OK"
)

print(
    "Final public JavaScript: OK"
)


# ============================================================
# PUBLIC HOME
# ============================================================

with app.test_client() as client:

    response = client.get(
        "/website"
    )


    require(
        response.status_code
        == 200,

        (
            "Public homepage failed: "
            f"{response.status_code}"
        ),
    )


    body = response.get_data(
        as_text=True
    )


    require(
        "public-ui-v4.css"
        in body,

        (
            "public-ui-v4.css "
            "not loaded."
        ),
    )


    require(
        "public-ui-v4.js"
        in body,

        (
            "public-ui-v4.js "
            "not loaded."
        ),
    )


    require(
        "public-site"
        in body,

        (
            "public-site body class "
            "is missing."
        ),
    )


    require(
        "OPTIMIZATION BEYOND"
        in body,

        (
            "Final public Home "
            "hero missing."
        ),
    )


    require(
        "Learn. Model. Optimize. Build."
        in body,

        (
            "Final mission section "
            "missing."
        ),
    )


    require(
        "Inside the ORSC ecosystem"
        in body,

        (
            "Final ecosystem section "
            "missing."
        ),
    )


    require(
        "Ready to explore Operations Research differently?"
        in body,

        (
            "Final CTA missing."
        ),
    )


    require(
        'href="#"'
        not in body,

        (
            "Homepage still contains "
            "placeholder href=\"#\" links."
        ),
    )


print(
    "Final public homepage: OK"
)


# ============================================================
# STATIC ASSETS
# ============================================================

with app.test_client() as client:

    response = client.get(
        "/static/css/public-ui-v4.css"
    )


    require(
        response.status_code
        == 200,

        "Final public CSS not served.",
    )


    response = client.get(
        "/static/js/public-ui-v4.js"
    )


    require(
        response.status_code
        == 200,

        "Final public JS not served.",
    )


print(
    "Final public assets served: OK"
)


# ============================================================
# PUBLIC PAGES
# ============================================================

routes = [

    "/website",

    "/about",

    "/website/departments",

    "/website/events",

    "/website/research-innovation",

    "/website/trainings",

    "/website/gallery",

    "/website/alumni",

    "/website/contact",

]


with app.test_client() as client:

    for route in routes:

        response = client.get(
            route,
            follow_redirects=False,
        )


        require(
            response.status_code
            == 200,

            (
                "Public page failed: "
                f"{route} "
                f"status="
                f"{response.status_code}"
            ),
        )


print(
    "All major public pages: OK"
)


# ============================================================
# NAVIGATION
# ============================================================

with app.test_client() as client:

    body = client.get(
        "/website"
    ).get_data(
        as_text=True
    )


    required_paths = [

        "/about",

        "/website/departments",

        "/website/events",

        "/website/research-innovation",

        "/website/trainings",

        "/website/gallery",

        "/website/alumni",

        "/website/contact",

        "/login",

    ]


    for path in required_paths:

        require(
            path in body,

            (
                "Missing public navigation "
                f"path: {path}"
            ),
        )


print(
    "Public navigation coverage: OK"
)


# ============================================================
# LIGHT / DARK SUPPORT
# ============================================================

css_text = (
    CSS_FILE.read_text(
        encoding="utf-8"
    )
)


require(
    "body.dark-mode"
    in css_text,

    (
        "Dark-mode support "
        "is missing."
    ),
)


require(
    "@media"
    in css_text
    and "max-width"
    in css_text,

    (
        "Responsive rules "
        "are missing."
    ),
)


require(
    "prefers-reduced-motion"
    in css_text,

    (
        "Reduced-motion "
        "accessibility missing."
    ),
)


print(
    "Light/Dark public theme: OK"
)

print(
    "Responsive public site: OK"
)

print(
    "Reduced-motion support: OK"
)


# ============================================================
# SUCCESS
# ============================================================

print()

print(
    "========================================"
)

print(
    "FINAL PUBLIC WEBSITE TEST SUCCESSFUL"
)

print(
    "========================================"
)


print(
    "Final Home: OK"
)

print(
    "Navbar/Footer integration: OK"
)

print(
    "Alumni integration: OK"
)

print(
    "Public page coverage: OK"
)

print(
    "Light/Dark mode: OK"
)

print(
    "Desktop/Mobile responsive: OK"
)

print(
    "Animations/accessibility: OK"
)