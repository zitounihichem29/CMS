from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect
)

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from extensions import limiter

from datetime import (
    datetime,
    timedelta,
    timezone
)

import secrets

from database import get_db_connection

from services.email_service import send_email


auth_bp = Blueprint(
    "auth",
    __name__
)


# ============================================================
# LOGIN
# ============================================================

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
@limiter.limit(
    "10 per minute",
    methods=["POST"]
)
def login():

    error = None

    if request.method == "POST":

        username_or_email = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not username_or_email or not password:

            error = (
                "Please enter your username "
                "or email and password."
            )

            return render_template(
                "login.html",
                error=error
            )


        conn = get_db_connection()
        cursor = conn.cursor()


        cursor.execute("""
            SELECT
                users.user_id,
                users.username,
                users.password_hash,
                users.is_active,

                people.email,
                people.first_name,
                people.last_name

            FROM users

            JOIN people
                ON users.person_id =
                   people.person_id

            WHERE LOWER(users.username) =
                  LOWER(?)

               OR LOWER(people.email) =
                  LOWER(?)

            LIMIT 1
        """, (
            username_or_email,
            username_or_email
        ))


        user = cursor.fetchone()

        conn.close()


        if user is None:

            error = (
                "Username, email or password "
                "is incorrect."
            )

            return render_template(
                "login.html",
                error=error
            )


        if user["is_active"] == 0:

            error = (
                "This account is currently inactive."
            )

            return render_template(
                "login.html",
                error=error
            )


        if not check_password_hash(
            user["password_hash"],
            password
        ):

            error = (
                "Username, email or password "
                "is incorrect."
            )

            return render_template(
                "login.html",
                error=error
            )


        session["user_id"] = user["user_id"]

        session["username"] = user["username"]


        return redirect(
            "/home"
        )


    return render_template(
        "login.html",
        error=error
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================

@auth_bp.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
@limiter.limit(
    "5 per 15 minutes",
    methods=["POST"]
)
def forgot_password():

    message = None


    if request.method == "POST":

        username_or_email = request.form.get(
            "username",
            ""
        ).strip()


        # Remove an old password-reset session
        session.pop(
            "password_reset_user_id",
            None
        )

        session.pop(
            "password_reset_verified_user_id",
            None
        )


        message = (
            "If an active account matches the "
            "information provided, a verification "
            "code has been sent to the associated "
            "email address."
        )


        if username_or_email:

            conn = get_db_connection()
            cursor = conn.cursor()


            # ==================================================
            # FIND ACTIVE USER
            # ==================================================

            cursor.execute("""
                SELECT
                    users.user_id,
                    users.username,
                    people.email

                FROM users

                JOIN people
                    ON users.person_id =
                       people.person_id

                WHERE users.is_active = 1

                  AND (
                        LOWER(users.username) =
                        LOWER(?)

                        OR LOWER(people.email) =
                           LOWER(?)
                  )

                LIMIT 1
            """, (
                username_or_email,
                username_or_email
            ))


            user = cursor.fetchone()


            # ==================================================
            # USER FOUND
            # ==================================================

            if (
                user is not None
                and user["email"]
            ):

                # ==============================================
                # CREATE 6-DIGIT CODE
                # ==============================================

                code = "".join(
                    secrets.choice(
                        "0123456789"
                    )
                    for _ in range(6)
                )


                # ==============================================
                # HASH CODE
                # ==============================================

                code_hash = (
                    generate_password_hash(
                        code
                    )
                )


                # ==============================================
                # CODE EXPIRATION
                # ==============================================

                expires_at = (
                    datetime.now(
                        timezone.utc
                    )
                    + timedelta(
                        minutes=10
                    )
                )


                # ==============================================
                # INVALIDATE PREVIOUS CODES
                # ==============================================

                cursor.execute("""
                    UPDATE password_reset_codes

                    SET is_used = 1

                    WHERE user_id = ?
                      AND is_used = 0
                """, (
                    user["user_id"],
                ))


                # ==============================================
                # SAVE NEW CODE
                # ==============================================

                cursor.execute("""
                    INSERT INTO password_reset_codes (
                        user_id,
                        code_hash,
                        expires_at,
                        is_used
                    )

                    VALUES (?, ?, ?, 0)
                """, (
                    user["user_id"],
                    code_hash,
                    expires_at.isoformat()
                ))


                conn.commit()


                # ==============================================
                # SEND CODE BY EMAIL
                # ==============================================

                send_email(
                    recipient=user["email"],
                    subject=(
                        "ORSC CMS - Password Reset Code"
                    ),
                    body=(
                        "Hello,\n\n"

                        "We received a request to reset "
                        "the password for your ORSC CMS "
                        "account.\n\n"

                        f"Your verification code is: "
                        f"{code}\n\n"

                        "This code will expire in "
                        "10 minutes.\n\n"

                        "If you did not request a password "
                        "reset, you can ignore this email."
                        "\n\n"

                        "ORSC CMS"
                    )
                )


                # ==============================================
                # REMEMBER USER FOR VERIFICATION
                # ==============================================

                session[
                    "password_reset_user_id"
                ] = user["user_id"]


                conn.close()


                # ==============================================
                # GO TO CODE VERIFICATION PAGE
                # ==============================================

                return redirect(
                    "/verify-reset-code"
                )


            conn.close()


    return render_template(
        "forgot_password.html",
        message=message
    )


# ============================================================
# VERIFY PASSWORD RESET CODE
# ============================================================

@auth_bp.route(
    "/verify-reset-code",
    methods=["GET", "POST"]
)
@limiter.limit(
    "10 per 15 minutes",
    methods=["POST"]
)
def verify_reset_code():

    error = None
    success = None


    # ========================================================
    # GET USER FROM RESET SESSION
    # ========================================================

    user_id = session.get(
        "password_reset_user_id"
    )


    # User did not start Forgot Password correctly
    if user_id is None:

        return redirect(
            "/forgot-password"
        )


    if request.method == "POST":

        code = request.form.get(
            "code",
            ""
        ).strip()


        # ====================================================
        # BASIC CODE VALIDATION
        # ====================================================

        if (
            not code
            or len(code) != 6
            or not code.isdigit()
        ):

            error = (
                "Please enter the 6-digit "
                "verification code."
            )


        else:

            conn = get_db_connection()
            cursor = conn.cursor()


            # =================================================
            # GET LATEST UNUSED CODE
            # =================================================

            cursor.execute("""
                SELECT
                    code_hash,
                    expires_at

                FROM password_reset_codes

                WHERE user_id = ?
                  AND is_used = 0

                ORDER BY expires_at DESC

                LIMIT 1
            """, (
                user_id,
            ))


            reset_code = cursor.fetchone()


            # =================================================
            # NO ACTIVE CODE
            # =================================================

            if reset_code is None:

                error = (
                    "This verification code is "
                    "invalid or has expired."
                )


            else:

                expires_at = (
                    datetime.fromisoformat(
                        reset_code["expires_at"]
                    )
                )


                # =============================================
                # CODE EXPIRED
                # =============================================

                if (
                    datetime.now(
                        timezone.utc
                    )
                    > expires_at
                ):

                    cursor.execute("""
                        UPDATE password_reset_codes

                        SET is_used = 1

                        WHERE user_id = ?
                          AND is_used = 0
                    """, (
                        user_id,
                    ))


                    conn.commit()


                    error = (
                        "This verification code "
                        "has expired. Please request "
                        "a new one."
                    )


                # =============================================
                # INCORRECT CODE
                # =============================================

                elif not check_password_hash(
                    reset_code["code_hash"],
                    code
                ):

                    error = (
                        "The verification code "
                        "is incorrect."
                    )


                # =============================================
                # CORRECT CODE
                # =============================================

                else:

                    cursor.execute("""
                        UPDATE password_reset_codes

                        SET is_used = 1

                        WHERE user_id = ?
                          AND is_used = 0
                    """, (
                        user_id,
                    ))


                    conn.commit()


                    session[
                        "password_reset_verified_user_id"
                    ] = user_id

                    session[
                        "password_reset_verified_at"
                    ] = datetime.now(
                        timezone.utc
                    ).isoformat()

                    session.pop(
                        "password_reset_user_id",
                        None
                    )

                    conn.close()

                    return redirect(
                        "/reset-password"
                    )


            conn.close()


    return render_template(
        "verify_reset_code.html",
        error=error,
        success=success
    )







# ============================================================
# RESET PASSWORD
# ============================================================

@auth_bp.route(
    "/reset-password",
    methods=["GET", "POST"]
)
@limiter.limit(
    "5 per 15 minutes",
    methods=["POST"]
)
def reset_password():

    error = None


    # ========================================================
    # CHECK VERIFIED RESET SESSION
    # ========================================================

    user_id = session.get(
        "password_reset_verified_user_id"
    )

    verified_at = session.get(
        "password_reset_verified_at"
    )


    if (
        user_id is None
        or verified_at is None
    ):

        return redirect(
            "/forgot-password"
        )


    # ========================================================
    # CHECK RESET SESSION EXPIRATION
    # ========================================================

    try:

        verification_time = (
            datetime.fromisoformat(
                verified_at
            )
        )

    except ValueError:

        session.pop(
            "password_reset_verified_user_id",
            None
        )

        session.pop(
            "password_reset_verified_at",
            None
        )

        return redirect(
            "/forgot-password"
        )


    if (
        datetime.now(timezone.utc)
        > verification_time
        + timedelta(minutes=10)
    ):

        session.pop(
            "password_reset_verified_user_id",
            None
        )

        session.pop(
            "password_reset_verified_at",
            None
        )

        return redirect(
            "/forgot-password"
        )


    # ========================================================
    # NEW PASSWORD
    # ========================================================

    if request.method == "POST":

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


        # ====================================================
        # VALIDATION
        # ====================================================

        if (
            not password
            or not confirm_password
        ):

            error = (
                "Please complete both password fields."
            )


        elif len(password) < 8:

            error = (
                "Password must contain at least "
                "8 characters."
            )


        elif password != confirm_password:

            error = (
                "The passwords do not match."
            )


        else:

            # =================================================
            # HASH NEW PASSWORD
            # =================================================

            password_hash = (
                generate_password_hash(
                    password
                )
            )


            # =================================================
            # UPDATE USER
            # =================================================

            conn = get_db_connection()
            cursor = conn.cursor()


            cursor.execute("""
                UPDATE users

                SET password_hash = ?

                WHERE user_id = ?
            """, (
                password_hash,
                user_id
            ))


            conn.commit()
            conn.close()


            # =================================================
            # REMOVE RESET AUTHORIZATION
            # =================================================

            session.pop(
                "password_reset_verified_user_id",
                None
            )

            session.pop(
                "password_reset_verified_at",
                None
            )


            # =================================================
            # RETURN TO LOGIN
            # =================================================

            return redirect(
                "/login"
            )


    return render_template(
        "reset_password.html",
        error=error
    )