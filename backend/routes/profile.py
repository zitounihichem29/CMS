import os
import uuid

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from werkzeug.utils import secure_filename

from context import get_active_term_id
from database import get_db_connection
from permissions import login_required


profile_bp = Blueprint(
    "profile",
    __name__,
)


ALLOWED_PROFILE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


# =========================================================
# PROFILE PHOTO
# =========================================================

@profile_bp.route(
    "/profile/photo/<path:filename>"
)
@login_required
def profile_photo(filename):

    profiles_folder = os.path.join(
        current_app.root_path,
        "uploads",
        "profiles",
    )

    return send_from_directory(
        profiles_folder,
        filename,
    )


# =========================================================
# MY PROFILE
# =========================================================

@profile_bp.route("/profile")
@login_required
def profile():

    conn = get_db_connection()
    cursor = conn.cursor()

    # =====================================================
    # PERSONAL + ACCOUNT INFORMATION
    # =====================================================

    cursor.execute("""
        SELECT
            people.*,

            users.user_id,
            users.username,
            users.is_active,
            users.is_platform_admin

        FROM users

        JOIN people
            ON users.person_id =
               people.person_id

        WHERE users.user_id = ?
    """, (
        session["user_id"],
    ))

    profile_data = cursor.fetchone()

    if profile_data is None:

        conn.close()

        return (
            "Profile not found",
            404,
        )

    person_id = (
        profile_data["person_id"]
    )

    active_term_id = (
        get_active_term_id()
    )

    # =====================================================
    # CURRENT MEMBERSHIP
    #
    # 1. ACTIVE mandate membership if one exists.
    # 2. Otherwise latest ARCHIVED membership.
    #
    # DRAFT memberships are intentionally ignored here.
    # =====================================================

    cursor.execute("""
        SELECT
            memberships.membership_id,
            memberships.term_id,

            terms.name AS term_name,
            terms.start_date,
            terms.end_date,
            terms.status AS term_status,

            roles.name AS role_name,

            departments.department_id,
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
            CASE
                WHEN terms.status = 'ACTIVE'
                THEN 0
                ELSE 1
            END,

            terms.end_date DESC

        LIMIT 1
    """, (
        person_id,
    ))

    current_membership = (
        cursor.fetchone()
    )

    # =====================================================
    # MEMBERSHIP HISTORY
    #
    # ACTIVE + ARCHIVED only.
    # DRAFT mandate preparation must not appear as
    # historical/current club membership.
    # =====================================================

    cursor.execute("""
        SELECT
            memberships.membership_id,
            memberships.term_id,

            terms.name AS term_name,
            terms.start_date,
            terms.end_date,
            terms.status AS term_status,

            roles.name AS role_name,

            departments.department_id,
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
            terms.start_date DESC
    """, (
        person_id,
    ))

    membership_history = (
        cursor.fetchall()
    )

    # =====================================================
    # YEAR JOINED ORSC
    #
    # Ignore DRAFT mandates.
    # =====================================================

    cursor.execute("""
        SELECT
            terms.term_id,
            terms.name AS term_name,
            terms.start_date,
            terms.end_date,
            terms.status AS term_status

        FROM memberships

        JOIN terms
            ON memberships.term_id =
               terms.term_id

        WHERE memberships.person_id = ?

          AND terms.status IN (
              'ACTIVE',
              'ARCHIVED'
          )

        ORDER BY
            terms.start_date ASC

        LIMIT 1
    """, (
        person_id,
    ))

    first_membership = (
        cursor.fetchone()
    )

    if first_membership is not None:

        year_joined = (
            first_membership[
                "term_name"
            ]
        )

    else:

        year_joined = None

    # =====================================================
    # MEMBER / ALUMNI STATUS
    #
    # A user is considered current only when they have a
    # non-ALUMNI membership in the ACTIVE mandate.
    # =====================================================

    is_alumni = True

    if active_term_id is not None:

        for membership in membership_history:

            if (
                membership["term_id"]
                == active_term_id
                and membership["role_name"]
                != "ALUMNI"
            ):

                is_alumni = False
                break

    conn.close()

    # =====================================================
    # PROFILE PAGE
    # =====================================================

    return render_template(
        "profile.html",

        profile=profile_data,

        current_membership=(
            current_membership
        ),

        membership_history=(
            membership_history
        ),

        year_joined=(
            year_joined
        ),

        is_alumni=(
            is_alumni
        ),
    )


# =========================================================
# EDIT MY PROFILE
# =========================================================

@profile_bp.route(
    "/profile/edit",
    methods=[
        "GET",
        "POST",
    ],
)
@login_required
def edit_profile():

    conn = get_db_connection()
    cursor = conn.cursor()

    # =====================================================
    # GET CURRENT USER PROFILE
    # =====================================================

    cursor.execute("""
        SELECT
            people.person_id,
            people.first_name,
            people.last_name,
            people.date_of_birth,
            people.phone,
            people.email,
            people.university,
            people.faculty,
            people.bio,
            people.linkedin,
            people.facebook,
            people.discord,
            people.github,
            people.profession,
            people.profile_photo,

            users.username

        FROM users

        JOIN people
            ON users.person_id =
               people.person_id

        WHERE users.user_id = ?
    """, (
        session["user_id"],
    ))

    profile_data = (
        cursor.fetchone()
    )

    if profile_data is None:

        conn.close()

        return (
            "Profile not found",
            404,
        )

    # =====================================================
    # UPDATE PERSONAL INFORMATION
    # =====================================================

    if request.method == "POST":

        phone = request.form.get(
            "phone",
            "",
        ).strip()

        email = request.form.get(
            "email",
            "",
        ).strip()

        date_of_birth = request.form.get(
            "date_of_birth",
            "",
        ).strip()

        university = request.form.get(
            "university",
            "",
        ).strip()

        faculty = request.form.get(
            "faculty",
            "",
        ).strip()

        profession = request.form.get(
            "profession",
            "",
        ).strip()

        bio = request.form.get(
            "bio",
            "",
        ).strip()

        linkedin = request.form.get(
            "linkedin",
            "",
        ).strip()

        facebook = request.form.get(
            "facebook",
            "",
        ).strip()

        discord = request.form.get(
            "discord",
            "",
        ).strip()

        github = request.form.get(
            "github",
            "",
        ).strip()

        # =================================================
        # PROFILE PHOTO
        # =================================================

        profile_photo = (
            profile_data[
                "profile_photo"
            ]
        )

        photo = request.files.get(
            "profile_photo"
        )

        if photo and photo.filename:

            original_filename = (
                secure_filename(
                    photo.filename
                )
            )

            extension = os.path.splitext(
                original_filename
            )[1].lower()

            if (
                extension
                not in ALLOWED_PROFILE_EXTENSIONS
            ):

                conn.close()

                return (
                    "Invalid profile photo format",
                    400,
                )

            if (
                not photo.mimetype
                or not photo.mimetype.startswith(
                    "image/"
                )
            ):

                conn.close()

                return (
                    "Invalid profile photo",
                    400,
                )

            stored_filename = (
                uuid.uuid4().hex
                + extension
            )

            profiles_folder = os.path.join(
                current_app.root_path,
                "uploads",
                "profiles",
            )

            os.makedirs(
                profiles_folder,
                exist_ok=True,
            )

            save_path = os.path.join(
                profiles_folder,
                stored_filename,
            )

            photo.save(
                save_path
            )

            profile_photo = (
                stored_filename
            )

        # =================================================
        # UPDATE PEOPLE
        # =================================================

        cursor.execute("""
            UPDATE people

            SET
                phone = ?,
                email = ?,
                date_of_birth = ?,
                university = ?,
                faculty = ?,
                profession = ?,
                bio = ?,
                linkedin = ?,
                facebook = ?,
                discord = ?,
                github = ?,
                profile_photo = ?

            WHERE person_id = ?
        """, (
            phone or None,
            email or None,
            date_of_birth or None,
            university or None,
            faculty or None,
            profession or None,
            bio or None,
            linkedin or None,
            facebook or None,
            discord or None,
            github or None,
            profile_photo,
            profile_data[
                "person_id"
            ],
        ))

        conn.commit()
        conn.close()

        return redirect(
            url_for(
                "profile.profile"
            )
        )

    conn.close()

    return render_template(
        "edit_profile.html",
        profile=profile_data,
    )