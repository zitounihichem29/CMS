import os
import re
import sqlite3
import unicodedata
import uuid

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from werkzeug.utils import secure_filename

from context import get_current_user
from database import get_db_connection
from permissions import login_required


alumni_bp = Blueprint(
    "alumni",
    __name__,
)


HR_DEPARTMENT_ID = 1


ALLOWED_CATEGORIES = {
    "ACADEMIA",
    "STARTUP",
    "INDUSTRY",
    "OTHER",
}


ALLOWED_PHOTO_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


# ============================================================
# PROTECT MODULE
# ============================================================

@alumni_bp.before_request
@login_required
def protect_alumni_module():
    pass


# ============================================================
# PERMISSIONS
# ============================================================

def is_platform_admin(user):

    return (
        user is not None
        and bool(
            user["is_platform_admin"]
        )
    )


def is_current_presidency(user):

    return (
        user is not None
        and not user["is_alumni"]
        and user["role_name"] in {
            "PRESIDENT",
            "VICE_PRESIDENT",
        }
    )


def is_current_hr_leadership(user):

    return (
        user is not None
        and not user["is_alumni"]
        and user["department_id"]
        == HR_DEPARTMENT_ID
        and user["role_name"] in {
            "HEAD",
            "SUB_HEAD",
        }
    )


def can_manage_alumni(user):

    return (
        is_platform_admin(user)
        or is_current_presidency(user)
        or is_current_hr_leadership(user)
    )


# ============================================================
# BASIC HELPERS
# ============================================================

def normalize_optional(value):

    value = (
        value
        or ""
    ).strip()

    return (
        value
        or None
    )


def parse_integer(
    value,
    label,
    minimum=None,
    maximum=None,
    default=None,
):

    value = (
        value
        or ""
    ).strip()


    if not value:

        return default


    try:

        result = int(
            value
        )


    except ValueError as error:

        raise ValueError(
            f"{label} must be a number."
        ) from error


    if (
        minimum is not None
        and result < minimum
    ):

        raise ValueError(
            f"{label} must be at least "
            f"{minimum}."
        )


    if (
        maximum is not None
        and result > maximum
    ):

        raise ValueError(
            f"{label} must be at most "
            f"{maximum}."
        )


    return result


# ============================================================
# SLUG
# ============================================================

def slugify(value):

    value = unicodedata.normalize(
        "NFKD",
        value or "",
    )


    value = (
        value
        .encode(
            "ascii",
            "ignore",
        )
        .decode(
            "ascii"
        )
    )


    value = (
        value
        .lower()
        .strip()
    )


    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value,
    )


    return value.strip(
        "-"
    )


def unique_slug(
    cursor,
    raw_slug,
    first_name,
    last_name,
    alumni_id=None,
):

    base = slugify(
        raw_slug
    )


    if not base:

        base = slugify(
            f"{first_name}-{last_name}"
        )


    if not base:

        base = "alumni"


    candidate = base
    number = 2


    while True:

        if alumni_id is None:

            cursor.execute(
                """
                SELECT
                    alumni_id

                FROM alumni_profiles

                WHERE slug = ?

                LIMIT 1
                """,
                (
                    candidate,
                ),
            )


        else:

            cursor.execute(
                """
                SELECT
                    alumni_id

                FROM alumni_profiles

                WHERE slug = ?

                  AND alumni_id != ?

                LIMIT 1
                """,
                (
                    candidate,
                    alumni_id,
                ),
            )


        if (
            cursor.fetchone()
            is None
        ):

            return candidate


        candidate = (
            f"{base}-{number}"
        )

        number += 1


# ============================================================
# EMAIL
# ============================================================

def validate_person_email(
    cursor,
    email,
    exclude_person_id=None,
):

    if not email:

        return


    if exclude_person_id is None:

        cursor.execute(
            """
            SELECT
                person_id

            FROM people

            WHERE email IS NOT NULL

              AND LOWER(email) =
                  LOWER(?)

            LIMIT 1
            """,
            (
                email,
            ),
        )


    else:

        cursor.execute(
            """
            SELECT
                person_id

            FROM people

            WHERE email IS NOT NULL

              AND LOWER(email) =
                  LOWER(?)

              AND person_id != ?

            LIMIT 1
            """,
            (
                email,
                exclude_person_id,
            ),
        )


    if (
        cursor.fetchone()
        is not None
    ):

        raise ValueError(
            "This email already belongs "
            "to another person."
        )


# ============================================================
# ALUMNI PHOTO
# ============================================================

def save_alumni_photo(
    photo_file,
):

    if (
        photo_file is None
        or not photo_file.filename
    ):

        return None


    filename = secure_filename(
        photo_file.filename
    )


    if not filename:

        raise ValueError(
            "Invalid alumni photo filename."
        )


    extension = os.path.splitext(
        filename
    )[1].lower()


    if (
        extension
        not in ALLOWED_PHOTO_EXTENSIONS
    ):

        raise ValueError(
            "Alumni photo must be "
            "JPG, JPEG, PNG or WEBP."
        )


    unique_filename = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )


    folder = os.path.join(
        current_app.root_path,
        "uploads",
        "alumni",
    )


    os.makedirs(
        folder,
        exist_ok=True,
    )


    photo_file.save(
        os.path.join(
            folder,
            unique_filename,
        )
    )


    return unique_filename


def delete_alumni_photo(
    filename,
):

    if not filename:

        return


    safe_filename = (
        os.path.basename(
            filename
        )
    )


    folder = os.path.realpath(
        os.path.join(
            current_app.root_path,
            "uploads",
            "alumni",
        )
    )


    path = os.path.realpath(
        os.path.join(
            folder,
            safe_filename,
        )
    )


    try:

        if (
            os.path.commonpath(
                [
                    folder,
                    path,
                ]
            )
            != folder
        ):

            return


    except ValueError:

        return


    if os.path.isfile(
        path
    ):

        try:

            os.remove(
                path
            )


        except OSError:

            pass


# ============================================================
# PROFILE QUERY
# ============================================================

def get_alumni_profile(
    cursor,
    alumni_id,
):

    cursor.execute(
        """
        SELECT
            alumni_profiles.*,

            people.first_name,
            people.last_name,
            people.email,
            people.phone,
            people.university,
            people.faculty,
            people.profession,
            people.profile_photo,

            creator.username
                AS created_by_username,

            updater.username
                AS updated_by_username

        FROM alumni_profiles


        JOIN people

            ON alumni_profiles.person_id =
               people.person_id


        LEFT JOIN users
            AS creator

            ON alumni_profiles.created_by_user_id =
               creator.user_id


        LEFT JOIN users
            AS updater

            ON alumni_profiles.updated_by_user_id =
               updater.user_id


        WHERE alumni_profiles.alumni_id = ?


        LIMIT 1
        """,
        (
            alumni_id,
        ),
    )


    return (
        cursor.fetchone()
    )


# ============================================================
# MEMBERSHIP HISTORY
# ============================================================

def get_membership_history(
    cursor,
    person_id,
):

    cursor.execute(
        """
        SELECT
            memberships.membership_id,

            terms.term_id,
            terms.name
                AS term_name,

            terms.start_date,
            terms.end_date,

            terms.status
                AS term_status,

            roles.name
                AS role_name,

            departments.name
                AS department_name

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


    return (
        cursor.fetchall()
    )


# ============================================================
# PEOPLE AVAILABLE FOR NEW ALUMNI PROFILE
# ============================================================

def get_available_people(
    cursor,
):

    cursor.execute(
        """
        SELECT
            people.person_id,
            people.first_name,
            people.last_name,
            people.email,
            people.university,

            users.username,

            active_roles.name
                AS active_role_name,

            active_departments.name
                AS active_department_name

        FROM people


        LEFT JOIN alumni_profiles

            ON people.person_id =
               alumni_profiles.person_id


        LEFT JOIN users

            ON people.person_id =
               users.person_id


        LEFT JOIN terms
            AS active_term

            ON active_term.status =
               'ACTIVE'


        LEFT JOIN memberships
            AS active_membership

            ON people.person_id =
               active_membership.person_id

           AND active_membership.term_id =
               active_term.term_id


        LEFT JOIN roles
            AS active_roles

            ON active_membership.role_id =
               active_roles.role_id


        LEFT JOIN departments
            AS active_departments

            ON active_membership.department_id =
               active_departments.department_id


        WHERE alumni_profiles.alumni_id
              IS NULL


        ORDER BY
            people.first_name,
            people.last_name
        """
    )


    return (
        cursor.fetchall()
    )


# ============================================================
# READ ALUMNI PROFILE FORM
# ============================================================

def read_profile_form():

    category = (
        request.form.get(
            "category",
            "OTHER",
        )
        .strip()
        .upper()
    )


    if (
        category
        not in ALLOWED_CATEGORIES
    ):

        raise ValueError(
            "Invalid alumni category."
        )


    graduation_year = (
        parse_integer(
            request.form.get(
                "graduation_year"
            ),
            "Graduation year",
            minimum=1900,
            maximum=2200,
            default=None,
        )
    )


    display_order = (
        parse_integer(
            request.form.get(
                "display_order"
            ),
            "Display order",
            minimum=0,
            default=0,
        )
    )


    is_public = (
        1
        if request.form.get(
            "is_public"
        ) == "1"
        else 0
    )


    is_featured = (
        1
        if request.form.get(
            "is_featured"
        ) == "1"
        else 0
    )


    is_spotlight = (
        1
        if request.form.get(
            "is_spotlight"
        ) == "1"
        else 0
    )


    # Spotlight must always be public + featured.

    if is_spotlight:

        is_public = 1

        is_featured = 1


    return {

        "slug":
            normalize_optional(
                request.form.get(
                    "slug"
                )
            ),

        "category":
            category,

        "headline":
            normalize_optional(
                request.form.get(
                    "headline"
                )
            ),

        "current_title":
            normalize_optional(
                request.form.get(
                    "current_title"
                )
            ),

        "current_organization":
            normalize_optional(
                request.form.get(
                    "current_organization"
                )
            ),

        "graduation_year":
            graduation_year,

        "short_bio":
            normalize_optional(
                request.form.get(
                    "short_bio"
                )
            ),

        "story":
            normalize_optional(
                request.form.get(
                    "story"
                )
            ),

        "linkedin_url":
            normalize_optional(
                request.form.get(
                    "linkedin_url"
                )
            ),

        "website_url":
            normalize_optional(
                request.form.get(
                    "website_url"
                )
            ),

        "is_public":
            is_public,

        "is_featured":
            is_featured,

        "is_spotlight":
            is_spotlight,

        "display_order":
            display_order,
    }


# ============================================================
# PHOTO ROUTE
# ============================================================

@alumni_bp.route(
    "/alumni/photo/<path:filename>"
)
def alumni_photo(
    filename,
):

    folder = os.path.join(
        current_app.root_path,
        "uploads",
        "alumni",
    )


    return send_from_directory(
        folder,
        os.path.basename(
            filename
        ),
    )


# ============================================================
# ALUMNI LIST
# ============================================================

@alumni_bp.route(
    "/alumni"
)
def alumni_list():

    current_user = (
        get_current_user()
    )


    category = (
        request.args.get(
            "category",
            "ALL",
        )
        .strip()
        .upper()
    )


    visibility = (
        request.args.get(
            "visibility",
            "ALL",
        )
        .strip()
        .upper()
    )


    if (
        category
        not in (
            ALLOWED_CATEGORIES
            | {"ALL"}
        )
    ):

        category = "ALL"


    if (
        visibility
        not in {
            "ALL",
            "PUBLIC",
            "HIDDEN",
            "FEATURED",
            "SPOTLIGHT",
        }
    ):

        visibility = "ALL"


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    conditions = []

    parameters = []


    if category != "ALL":

        conditions.append(
            "alumni_profiles.category = ?"
        )

        parameters.append(
            category
        )


    if visibility == "PUBLIC":

        conditions.append(
            "alumni_profiles.is_public = 1"
        )


    elif visibility == "HIDDEN":

        conditions.append(
            "alumni_profiles.is_public = 0"
        )


    elif visibility == "FEATURED":

        conditions.append(
            "alumni_profiles.is_featured = 1"
        )


    elif visibility == "SPOTLIGHT":

        conditions.append(
            "alumni_profiles.is_spotlight = 1"
        )


    where_clause = ""


    if conditions:

        where_clause = (
            "WHERE "
            + " AND ".join(
                conditions
            )
        )


    cursor.execute(
        f"""
        SELECT
            alumni_profiles.*,

            people.first_name,
            people.last_name,
            people.profile_photo,

            (
                SELECT
                    COUNT(*)

                FROM memberships

                JOIN terms

                    ON memberships.term_id =
                       terms.term_id

                WHERE memberships.person_id =
                      people.person_id

                  AND terms.status IN (
                      'ACTIVE',
                      'ARCHIVED'
                  )
            )
                AS membership_count

        FROM alumni_profiles


        JOIN people

            ON alumni_profiles.person_id =
               people.person_id


        {where_clause}


        ORDER BY

            alumni_profiles.is_spotlight
                DESC,

            alumni_profiles.is_featured
                DESC,

            alumni_profiles.display_order
                ASC,

            people.first_name,

            people.last_name
        """,
        parameters,
    )


    alumni = (
        cursor.fetchall()
    )


    cursor.execute(
        """
        SELECT
            COUNT(*)
                AS total,

            SUM(
                CASE
                    WHEN is_public = 1
                    THEN 1
                    ELSE 0
                END
            )
                AS public_total,

            SUM(
                CASE
                    WHEN is_featured = 1
                    THEN 1
                    ELSE 0
                END
            )
                AS featured_total,

            SUM(
                CASE
                    WHEN is_spotlight = 1
                    THEN 1
                    ELSE 0
                END
            )
                AS spotlight_total

        FROM alumni_profiles
        """
    )


    stats = (
        cursor.fetchone()
    )


    conn.close()


    return render_template(
        "alumni/alumni_list.html",

        alumni=alumni,

        stats=stats,

        selected_category=(
            category
        ),

        selected_visibility=(
            visibility
        ),

        can_manage=(
            can_manage_alumni(
                current_user
            )
        ),
    )


# ============================================================
# ALUMNI DETAIL
# ============================================================

@alumni_bp.route(
    "/alumni/<int:alumni_id>"
)
def alumni_detail(
    alumni_id,
):

    current_user = (
        get_current_user()
    )


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    profile = get_alumni_profile(
        cursor,
        alumni_id,
    )


    if profile is None:

        conn.close()

        return (
            "Alumni profile not found",
            404,
        )


    history = (
        get_membership_history(
            cursor,
            profile[
                "person_id"
            ],
        )
    )


    conn.close()


    return render_template(
        "alumni/alumni_detail.html",

        profile=profile,

        history=history,

        can_manage=(
            can_manage_alumni(
                current_user
            )
        ),
    )


# ============================================================
# NEW ALUMNI
# ============================================================

@alumni_bp.route(
    "/alumni/new",
    methods=[
        "GET",
        "POST",
    ],
)
def new_alumni():

    current_user = (
        get_current_user()
    )


    if not can_manage_alumni(
        current_user
    ):

        return (
            "Access denied",
            403,
        )


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    error = None

    new_photo = None


    if request.method == "POST":

        try:

            existing_person_id = (
                request.form.get(
                    "existing_person_id",
                    "",
                ).strip()
            )


            person_id = None


            creating_new_person = (
                not existing_person_id
            )


            # =================================================
            # EXISTING PERSON
            # =================================================

            if existing_person_id:

                try:

                    person_id = int(
                        existing_person_id
                    )


                except ValueError as parse_error:

                    raise ValueError(
                        "Invalid existing person."
                    ) from parse_error


                cursor.execute(
                    """
                    SELECT
                        person_id,
                        first_name,
                        last_name,
                        email,
                        university

                    FROM people

                    WHERE person_id = ?

                    LIMIT 1
                    """,
                    (
                        person_id,
                    ),
                )


                person = (
                    cursor.fetchone()
                )


                if person is None:

                    raise ValueError(
                        "Selected person "
                        "does not exist."
                    )


                cursor.execute(
                    """
                    SELECT
                        alumni_id

                    FROM alumni_profiles

                    WHERE person_id = ?

                    LIMIT 1
                    """,
                    (
                        person_id,
                    ),
                )


                if (
                    cursor.fetchone()
                    is not None
                ):

                    raise ValueError(
                        "This person already "
                        "has an Alumni profile."
                    )


                first_name = (
                    person[
                        "first_name"
                    ]
                )

                last_name = (
                    person[
                        "last_name"
                    ]
                )

                email = (
                    person[
                        "email"
                    ]
                )

                university = (
                    person[
                        "university"
                    ]
                )


            # =================================================
            # NEW PERSON
            # =================================================

            else:

                first_name = (
                    request.form.get(
                        "first_name",
                        "",
                    ).strip()
                )


                last_name = (
                    request.form.get(
                        "last_name",
                        "",
                    ).strip()
                )


                email = (
                    normalize_optional(
                        request.form.get(
                            "email"
                        )
                    )
                )


                university = (
                    normalize_optional(
                        request.form.get(
                            "university"
                        )
                    )
                    or "USTHB"
                )


                if (
                    not first_name
                    or not last_name
                ):

                    raise ValueError(
                        "First name and last "
                        "name are required "
                        "for a new person."
                    )


                validate_person_email(
                    cursor,
                    email,
                )


            # =================================================
            # ALUMNI DATA
            # =================================================

            data = (
                read_profile_form()
            )


            slug = unique_slug(
                cursor,
                data["slug"],
                first_name,
                last_name,
            )


            photo_file = (
                request.files.get(
                    "photo_file"
                )
            )


            new_photo = (
                save_alumni_photo(
                    photo_file
                )
            )


            # =================================================
            # TRANSACTION
            # =================================================

            conn.execute(
                "BEGIN IMMEDIATE"
            )


            if creating_new_person:

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
                        first_name,
                        last_name,
                        email,
                        university,
                    ),
                )


                person_id = (
                    cursor.lastrowid
                )


            # =================================================
            # SINGLE SPOTLIGHT
            # =================================================

            if data[
                "is_spotlight"
            ]:

                cursor.execute(
                    """
                    UPDATE alumni_profiles

                    SET
                        is_spotlight = 0,

                        updated_at =
                            CURRENT_TIMESTAMP

                    WHERE is_spotlight = 1
                    """
                )


            # =================================================
            # INSERT PROFILE
            # =================================================

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

                    display_order,

                    created_by_user_id
                )

                VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?
                )
                """,
                (
                    person_id,

                    slug,

                    data[
                        "category"
                    ],

                    data[
                        "headline"
                    ],

                    data[
                        "current_title"
                    ],

                    data[
                        "current_organization"
                    ],

                    data[
                        "graduation_year"
                    ],

                    data[
                        "short_bio"
                    ],

                    data[
                        "story"
                    ],

                    new_photo,

                    data[
                        "linkedin_url"
                    ],

                    data[
                        "website_url"
                    ],

                    data[
                        "is_public"
                    ],

                    data[
                        "is_featured"
                    ],

                    data[
                        "is_spotlight"
                    ],

                    data[
                        "display_order"
                    ],

                    current_user[
                        "user_id"
                    ],
                ),
            )


            alumni_id = (
                cursor.lastrowid
            )


            conn.commit()

            conn.close()


            return redirect(
                url_for(
                    "alumni.alumni_detail",

                    alumni_id=(
                        alumni_id
                    ),
                )
            )


        except (
            ValueError,
            sqlite3.IntegrityError,
            OSError,
        ) as caught_error:

            conn.rollback()


            if new_photo:

                delete_alumni_photo(
                    new_photo
                )


            error = str(
                caught_error
            )


    available_people = (
        get_available_people(
            cursor
        )
    )


    conn.close()


    return render_template(
        "alumni/alumni_form.html",

        mode="create",

        profile=None,

        available_people=(
            available_people
        ),

        error=error,

        categories=sorted(
            ALLOWED_CATEGORIES
        ),
    )


# ============================================================
# EDIT ALUMNI
# ============================================================

@alumni_bp.route(
    "/alumni/<int:alumni_id>/edit",
    methods=[
        "GET",
        "POST",
    ],
)
def edit_alumni(
    alumni_id,
):

    current_user = (
        get_current_user()
    )


    if not can_manage_alumni(
        current_user
    ):

        return (
            "Access denied",
            403,
        )


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    profile = get_alumni_profile(
        cursor,
        alumni_id,
    )


    if profile is None:

        conn.close()

        return (
            "Alumni profile not found",
            404,
        )


    error = None

    new_photo = None


    if request.method == "POST":

        try:

            first_name = (
                request.form.get(
                    "first_name",
                    "",
                ).strip()
            )


            last_name = (
                request.form.get(
                    "last_name",
                    "",
                ).strip()
            )


            email = (
                normalize_optional(
                    request.form.get(
                        "email"
                    )
                )
            )


            university = (
                normalize_optional(
                    request.form.get(
                        "university"
                    )
                )
            )


            if (
                not first_name
                or not last_name
            ):

                raise ValueError(
                    "First name and last "
                    "name are required."
                )


            validate_person_email(
                cursor,

                email,

                exclude_person_id=(
                    profile[
                        "person_id"
                    ]
                ),
            )


            data = (
                read_profile_form()
            )


            slug = unique_slug(
                cursor,

                data[
                    "slug"
                ],

                first_name,

                last_name,

                alumni_id=(
                    alumni_id
                ),
            )


            photo_file = (
                request.files.get(
                    "photo_file"
                )
            )


            remove_photo = (
                request.form.get(
                    "remove_photo"
                )
                == "1"
            )


            new_photo = (
                save_alumni_photo(
                    photo_file
                )
            )


            old_photo = (
                profile[
                    "photo_path"
                ]
            )


            if new_photo:

                final_photo = (
                    new_photo
                )


            elif remove_photo:

                final_photo = None


            else:

                final_photo = (
                    old_photo
                )


            conn.execute(
                "BEGIN IMMEDIATE"
            )


            # =================================================
            # PERSON
            # =================================================

            cursor.execute(
                """
                UPDATE people

                SET
                    first_name = ?,

                    last_name = ?,

                    email = ?,

                    university = ?

                WHERE person_id = ?
                """,
                (
                    first_name,

                    last_name,

                    email,

                    university,

                    profile[
                        "person_id"
                    ],
                ),
            )


            # =================================================
            # SINGLE SPOTLIGHT
            # =================================================

            if data[
                "is_spotlight"
            ]:

                cursor.execute(
                    """
                    UPDATE alumni_profiles

                    SET
                        is_spotlight = 0,

                        updated_at =
                            CURRENT_TIMESTAMP

                    WHERE is_spotlight = 1

                      AND alumni_id != ?
                    """,
                    (
                        alumni_id,
                    ),
                )


            # =================================================
            # PROFILE
            # =================================================

            cursor.execute(
                """
                UPDATE alumni_profiles

                SET
                    slug = ?,

                    category = ?,

                    headline = ?,

                    current_title = ?,

                    current_organization = ?,

                    graduation_year = ?,

                    short_bio = ?,

                    story = ?,

                    photo_path = ?,

                    linkedin_url = ?,

                    website_url = ?,

                    is_public = ?,

                    is_featured = ?,

                    is_spotlight = ?,

                    display_order = ?,

                    updated_by_user_id = ?,

                    updated_at =
                        CURRENT_TIMESTAMP

                WHERE alumni_id = ?
                """,
                (
                    slug,

                    data[
                        "category"
                    ],

                    data[
                        "headline"
                    ],

                    data[
                        "current_title"
                    ],

                    data[
                        "current_organization"
                    ],

                    data[
                        "graduation_year"
                    ],

                    data[
                        "short_bio"
                    ],

                    data[
                        "story"
                    ],

                    final_photo,

                    data[
                        "linkedin_url"
                    ],

                    data[
                        "website_url"
                    ],

                    data[
                        "is_public"
                    ],

                    data[
                        "is_featured"
                    ],

                    data[
                        "is_spotlight"
                    ],

                    data[
                        "display_order"
                    ],

                    current_user[
                        "user_id"
                    ],

                    alumni_id,
                ),
            )


            conn.commit()


            if (
                old_photo
                and old_photo
                != final_photo
            ):

                delete_alumni_photo(
                    old_photo
                )


            conn.close()


            return redirect(
                url_for(
                    "alumni.alumni_detail",

                    alumni_id=(
                        alumni_id
                    ),
                )
            )


        except (
            ValueError,
            sqlite3.IntegrityError,
            OSError,
        ) as caught_error:

            conn.rollback()


            if new_photo:

                delete_alumni_photo(
                    new_photo
                )


            error = str(
                caught_error
            )


            profile = (
                get_alumni_profile(
                    cursor,
                    alumni_id,
                )
            )


    conn.close()


    return render_template(
        "alumni/alumni_form.html",

        mode="edit",

        profile=profile,

        available_people=[],

        error=error,

        categories=sorted(
            ALLOWED_CATEGORIES
        ),
    )


# ============================================================
# DELETE ALUMNI PROFILE
#
# Important:
# delete Alumni profile only.
# Never delete person or membership history.
# ============================================================

@alumni_bp.route(
    "/alumni/<int:alumni_id>/delete",
    methods=[
        "POST",
    ],
)
def delete_alumni(
    alumni_id,
):

    current_user = (
        get_current_user()
    )


    if not can_manage_alumni(
        current_user
    ):

        return (
            "Access denied",
            403,
        )


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    profile = get_alumni_profile(
        cursor,
        alumni_id,
    )


    if profile is None:

        conn.close()

        return (
            "Alumni profile not found",
            404,
        )


    confirmation = (
        request.form.get(
            "confirmation",
            "",
        ).strip()
    )


    expected_name = (
        f"{profile['first_name']} "
        f"{profile['last_name']}"
    )


    if (
        confirmation
        != expected_name
    ):

        conn.close()

        return (
            "Type the Alumni full "
            "name exactly to confirm "
            "deletion.",
            400,
        )


    photo_path = (
        profile[
            "photo_path"
        ]
    )


    try:

        cursor.execute(
            """
            DELETE FROM alumni_profiles

            WHERE alumni_id = ?
            """,
            (
                alumni_id,
            ),
        )


        if (
            cursor.rowcount
            != 1
        ):

            raise ValueError(
                "Alumni profile could "
                "not be deleted."
            )


        conn.commit()


    except Exception as error:

        conn.rollback()

        conn.close()


        return (
            "Alumni profile deletion "
            f"failed: {error}",
            400,
        )


    conn.close()


    if photo_path:

        delete_alumni_photo(
            photo_path
        )


    return redirect(
        url_for(
            "alumni.alumni_list"
        )
    )