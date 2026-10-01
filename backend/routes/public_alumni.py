import os
from urllib.parse import urlparse

from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    send_from_directory,
)

from database import get_db_connection


public_alumni_bp = Blueprint(
    "public_alumni",
    __name__,
)


ALUMNI_CATEGORIES = {
    "ACADEMIA",
    "STARTUP",
    "INDUSTRY",
    "OTHER",
}


# ============================================================
# HELPERS
# ============================================================

def safe_external_url(value):

    if not value:
        return None

    value = value.strip()

    try:

        parsed = urlparse(
            value
        )

    except ValueError:
        return None

    if parsed.scheme not in {
        "http",
        "https",
    }:
        return None

    if not parsed.netloc:
        return None

    return value


def get_public_alumni_profile(
    cursor,
    slug,
):

    cursor.execute(
        """
        SELECT
            alumni_profiles.alumni_id,
            alumni_profiles.person_id,
            alumni_profiles.slug,
            alumni_profiles.category,
            alumni_profiles.headline,
            alumni_profiles.current_title,
            alumni_profiles.current_organization,
            alumni_profiles.graduation_year,
            alumni_profiles.short_bio,
            alumni_profiles.story,
            alumni_profiles.photo_path,
            alumni_profiles.linkedin_url,
            alumni_profiles.website_url,
            alumni_profiles.is_public,
            alumni_profiles.is_featured,
            alumni_profiles.is_spotlight,
            alumni_profiles.display_order,

            people.first_name,
            people.last_name,
            people.university,
            people.faculty,
            people.profession

        FROM alumni_profiles

        JOIN people
            ON alumni_profiles.person_id =
               people.person_id

        WHERE alumni_profiles.slug = ?

          AND alumni_profiles.is_public = 1

        LIMIT 1
        """,
        (
            slug,
        ),
    )

    return cursor.fetchone()


def get_public_membership_history(
    cursor,
    person_id,
):

    cursor.execute(
        """
        SELECT
            memberships.membership_id,

            terms.term_id,
            terms.name AS term_name,
            terms.start_date,
            terms.end_date,
            terms.status AS term_status,

            roles.name AS role_name,

            departments.name AS department_name

        FROM memberships

        JOIN terms
            ON memberships.term_id =
               terms.term_id

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        LEFT JOIN departments
            ON memberships.department_id =
               departments.department_id

        WHERE memberships.person_id = ?

          AND terms.status IN (
              'ACTIVE',
              'ARCHIVED'
          )

        ORDER BY
            terms.start_date DESC,
            memberships.membership_id DESC
        """,
        (
            person_id,
        ),
    )

    return cursor.fetchall()


# ============================================================
# HOMEPAGE ALUMNI SPOTLIGHT
#
# This context processor injects Alumni Spotlight only
# when public.home is being rendered.
#
# We therefore do NOT need to modify the large public.py file.
# ============================================================

@public_alumni_bp.app_context_processor
def inject_public_alumni_spotlight():

    if request.endpoint != "public.home":

        return {
            "alumni_spotlight": None
        }

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            alumni_profiles.alumni_id,
            alumni_profiles.person_id,
            alumni_profiles.slug,
            alumni_profiles.category,
            alumni_profiles.headline,
            alumni_profiles.current_title,
            alumni_profiles.current_organization,
            alumni_profiles.graduation_year,
            alumni_profiles.short_bio,
            alumni_profiles.photo_path,

            people.first_name,
            people.last_name,

            (
                SELECT
                    terms.name

                FROM memberships

                JOIN terms
                    ON memberships.term_id =
                       terms.term_id

                WHERE memberships.person_id =
                      alumni_profiles.person_id

                  AND terms.status IN (
                      'ACTIVE',
                      'ARCHIVED'
                  )

                ORDER BY
                    terms.start_date DESC,
                    memberships.membership_id DESC

                LIMIT 1
            )
                AS latest_term_name,

            (
                SELECT
                    roles.name

                FROM memberships

                JOIN terms
                    ON memberships.term_id =
                       terms.term_id

                JOIN roles
                    ON memberships.role_id =
                       roles.role_id

                WHERE memberships.person_id =
                      alumni_profiles.person_id

                  AND terms.status IN (
                      'ACTIVE',
                      'ARCHIVED'
                  )

                ORDER BY
                    terms.start_date DESC,
                    memberships.membership_id DESC

                LIMIT 1
            )
                AS latest_role_name,

            (
                SELECT
                    departments.name

                FROM memberships

                JOIN terms
                    ON memberships.term_id =
                       terms.term_id

                LEFT JOIN departments
                    ON memberships.department_id =
                       departments.department_id

                WHERE memberships.person_id =
                      alumni_profiles.person_id

                  AND terms.status IN (
                      'ACTIVE',
                      'ARCHIVED'
                  )

                ORDER BY
                    terms.start_date DESC,
                    memberships.membership_id DESC

                LIMIT 1
            )
                AS latest_department_name

        FROM alumni_profiles

        JOIN people
            ON alumni_profiles.person_id =
               people.person_id

        WHERE alumni_profiles.is_public = 1

          AND alumni_profiles.is_spotlight = 1

          AND alumni_profiles.slug IS NOT NULL

          AND TRIM(
              alumni_profiles.slug
          ) != ''

        LIMIT 1
        """
    )

    alumni_spotlight = (
        cursor.fetchone()
    )

    conn.close()

    return {
        "alumni_spotlight":
            alumni_spotlight
    }


# ============================================================
# PUBLIC ALUMNI DIRECTORY
# ============================================================

@public_alumni_bp.route(
    "/website/alumni"
)
def alumni():

    category = (
        request.args.get(
            "category",
            "ALL",
        )
        .strip()
        .upper()
    )

    if (
        category != "ALL"
        and category
        not in ALUMNI_CATEGORIES
    ):
        category = "ALL"

    conn = get_db_connection()
    cursor = conn.cursor()

    parameters = []

    category_condition = ""

    if category != "ALL":

        category_condition = (
            "AND alumni_profiles.category = ?"
        )

        parameters.append(
            category
        )

    cursor.execute(
        f"""
        SELECT
            alumni_profiles.alumni_id,
            alumni_profiles.person_id,
            alumni_profiles.slug,
            alumni_profiles.category,
            alumni_profiles.headline,
            alumni_profiles.current_title,
            alumni_profiles.current_organization,
            alumni_profiles.graduation_year,
            alumni_profiles.short_bio,
            alumni_profiles.photo_path,
            alumni_profiles.is_featured,
            alumni_profiles.is_spotlight,
            alumni_profiles.display_order,

            people.first_name,
            people.last_name,

            (
                SELECT
                    terms.name

                FROM memberships

                JOIN terms
                    ON memberships.term_id =
                       terms.term_id

                WHERE memberships.person_id =
                      alumni_profiles.person_id

                  AND terms.status IN (
                      'ACTIVE',
                      'ARCHIVED'
                  )

                ORDER BY
                    terms.start_date DESC,
                    memberships.membership_id DESC

                LIMIT 1
            )
                AS latest_term_name,

            (
                SELECT
                    roles.name

                FROM memberships

                JOIN terms
                    ON memberships.term_id =
                       terms.term_id

                JOIN roles
                    ON memberships.role_id =
                       roles.role_id

                WHERE memberships.person_id =
                      alumni_profiles.person_id

                  AND terms.status IN (
                      'ACTIVE',
                      'ARCHIVED'
                  )

                ORDER BY
                    terms.start_date DESC,
                    memberships.membership_id DESC

                LIMIT 1
            )
                AS latest_role_name,

            (
                SELECT
                    departments.name

                FROM memberships

                JOIN terms
                    ON memberships.term_id =
                       terms.term_id

                LEFT JOIN departments
                    ON memberships.department_id =
                       departments.department_id

                WHERE memberships.person_id =
                      alumni_profiles.person_id

                  AND terms.status IN (
                      'ACTIVE',
                      'ARCHIVED'
                  )

                ORDER BY
                    terms.start_date DESC,
                    memberships.membership_id DESC

                LIMIT 1
            )
                AS latest_department_name

        FROM alumni_profiles

        JOIN people
            ON alumni_profiles.person_id =
               people.person_id

        WHERE alumni_profiles.is_public = 1

          AND alumni_profiles.slug IS NOT NULL

          AND TRIM(
              alumni_profiles.slug
          ) != ''

          {category_condition}

        ORDER BY
            alumni_profiles.is_spotlight DESC,
            alumni_profiles.is_featured DESC,
            alumni_profiles.display_order ASC,
            people.first_name ASC,
            people.last_name ASC
        """,
        parameters,
    )

    alumni_profiles = (
        cursor.fetchall()
    )

    cursor.execute(
        """
        SELECT
            COUNT(*) AS total

        FROM alumni_profiles

        WHERE is_public = 1

          AND slug IS NOT NULL

          AND TRIM(slug) != ''
        """
    )

    public_count = (
        cursor.fetchone()[
            "total"
        ]
        or 0
    )

    conn.close()

    return render_template(
        "public/alumni.html",

        alumni_profiles=(
            alumni_profiles
        ),

        selected_category=(
            category
        ),

        public_count=(
            public_count
        ),
    )


# ============================================================
# PUBLIC ALUMNI DETAIL
# ============================================================

@public_alumni_bp.route(
    "/website/alumni/<string:slug>"
)
def alumni_detail(
    slug,
):

    conn = get_db_connection()
    cursor = conn.cursor()

    profile = (
        get_public_alumni_profile(
            cursor,
            slug,
        )
    )

    if profile is None:

        conn.close()

        return (
            "Alumni profile not found",
            404,
        )

    history = (
        get_public_membership_history(
            cursor,
            profile[
                "person_id"
            ],
        )
    )

    linkedin_url = (
        safe_external_url(
            profile[
                "linkedin_url"
            ]
        )
    )

    website_url = (
        safe_external_url(
            profile[
                "website_url"
            ]
        )
    )

    conn.close()

    return render_template(
        "public/alumni_detail.html",

        profile=profile,

        history=history,

        linkedin_url=(
            linkedin_url
        ),

        website_url=(
            website_url
        ),
    )


# ============================================================
# PUBLIC ALUMNI PHOTO
#
# The route is profile-based, not filename-based.
# Hidden Alumni photos therefore cannot be fetched publicly.
# ============================================================

@public_alumni_bp.route(
    "/website/alumni/<string:slug>/photo"
)
def alumni_photo(
    slug,
):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            alumni_profiles.photo_path

        FROM alumni_profiles

        WHERE alumni_profiles.slug = ?

          AND alumni_profiles.is_public = 1

          AND alumni_profiles.photo_path
              IS NOT NULL

        LIMIT 1
        """,
        (
            slug,
        ),
    )

    row = cursor.fetchone()

    conn.close()

    if row is None:

        return (
            "Alumni photo not found",
            404,
        )

    filename = os.path.basename(
        row[
            "photo_path"
        ]
    )

    folder = os.path.join(
        current_app.root_path,
        "uploads",
        "alumni",
    )

    return send_from_directory(
        folder,
        filename,
    )