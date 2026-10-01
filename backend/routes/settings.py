from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for
)

from database import get_db_connection
from permissions import login_required


settings_bp = Blueprint(
    "settings",
    __name__
)


# =========================================================
# SETTINGS
# =========================================================

@settings_bp.route("/settings")
@login_required
def settings():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            users.user_id,
            users.username,

            people.first_name,
            people.last_name,
            people.email,
            people.profile_photo

        FROM users

        JOIN people
            ON users.person_id =
               people.person_id

        WHERE users.user_id = ?
    """, (
        session["user_id"],
    ))

    user = cursor.fetchone()

    conn.close()


    if user is None:
        return "User not found", 404


    return render_template(
        "settings.html",
        user=user
    )




# =========================================================
# CHANGE PASSWORD
# =========================================================

@settings_bp.route(
    "/settings/password",
    methods=["GET", "POST"]
)
@login_required
def change_password():

    conn = get_db_connection()
    cursor = conn.cursor()


    # =====================================================
    # GET CURRENT USER
    # =====================================================

    cursor.execute("""
        SELECT
            user_id,
            username,
            password_hash

        FROM users

        WHERE user_id = ?
    """, (
        session["user_id"],
    ))

    user = cursor.fetchone()


    if user is None:
        conn.close()
        return "User not found", 404


    error = None
    success = None


    # =====================================================
    # CHANGE PASSWORD
    # =====================================================

    if request.method == "POST":

        current_password = request.form.get(
            "current_password",
            ""
        )

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


        # =============================================
        # REQUIRED FIELDS
        # =============================================

        if (
            not current_password
            or not new_password
            or not confirm_password
        ):
            error = "All password fields are required."


        # =============================================
        # VERIFY CURRENT PASSWORD
        # =============================================

        elif not check_password_hash(
            user["password_hash"],
            current_password
        ):
            error = "Current password is incorrect."


        # =============================================
        # PASSWORD CONFIRMATION
        # =============================================

        elif new_password != confirm_password:
            error = "New passwords do not match."


        # =============================================
        # MINIMUM LENGTH
        # =============================================

        elif len(new_password) < 8:
            error = (
                "New password must contain "
                "at least 8 characters."
            )


        # =============================================
        # NEW PASSWORD MUST BE DIFFERENT
        # =============================================

        elif check_password_hash(
            user["password_hash"],
            new_password
        ):
            error = (
                "New password must be different "
                "from the current password."
            )


        # =============================================
        # UPDATE PASSWORD
        # =============================================

        else:

            new_password_hash = generate_password_hash(
                new_password
            )

            cursor.execute("""
                UPDATE users

                SET password_hash = ?

                WHERE user_id = ?
            """, (
                new_password_hash,
                session["user_id"]
            ))

            conn.commit()

            success = "Password changed successfully."


    conn.close()


    return render_template(
        "change_password.html",
        error=error,
        success=success
    )