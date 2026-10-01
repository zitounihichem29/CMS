import re
import secrets
import unicodedata

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    url_for,
)

from werkzeug.security import generate_password_hash

from context import (
    get_active_term_id,
    get_current_user,
)

from database import get_db_connection
from permissions import login_required
from services.email_service import send_email


applications_bp = Blueprint(
    "applications",
    __name__,
)


RH_DEPARTMENT_ID = 1


# ============================================================
# HELPERS
# ============================================================

def can_view_applications(current_user):

    if current_user is None:
        return False

    if current_user["is_alumni"]:
        return False

    # President and Vice President can view applications
    if current_user["role_name"] in (
        "PRESIDENT",
        "VICE_PRESIDENT",
    ):
        return True

    # Entire RH team can view applications
    return (
        current_user["department_id"] == RH_DEPARTMENT_ID
        and current_user["role_name"] in (
            "HEAD",
            "SUB_HEAD",
            "MEMBER",
        )
    )


def can_process_applications(current_user):

    if current_user is None:
        return False

    if current_user["is_alumni"]:
        return False

    if current_user["role_name"] in (
        "PRESIDENT",
        "VICE_PRESIDENT",
    ):
        return True

    return (
        current_user["department_id"]
        == RH_DEPARTMENT_ID
        and current_user["role_name"] in (
            "HEAD",
            "SUB_HEAD",
            "MEMBER",
        )
    )


def can_manage_application_periods(current_user):

    if current_user is None:
        return False

    if current_user["is_alumni"]:
        return False

    # Only RH leadership manages recruitment periods
    return (
        current_user["department_id"] == RH_DEPARTMENT_ID
        and current_user["role_name"] in (
            "HEAD",
            "SUB_HEAD",
        )
    )


def get_active_term_row(
    cursor,
):

    active_term_id = (
        get_active_term_id()
    )

    if active_term_id is None:
        return None

    cursor.execute("""
        SELECT
            term_id,
            name,
            start_date,
            end_date,
            status

        FROM terms

        WHERE term_id = ?
          AND status = 'ACTIVE'

        LIMIT 1
    """, (
        active_term_id,
    ))

    return cursor.fetchone()


def get_application_for_action(
    cursor,
    application_id,
    active_term_id,
):

    cursor.execute("""
        SELECT
            applications.application_id,
            applications.person_id,
            applications.application_period_id,
            applications.status,
            applications.onboarding_token,
            applications.submitted_at,

            people.first_name,
            people.last_name,
            people.email,

            application_periods.term_id,
            application_periods.name
                AS period_name,

            terms.name
                AS term_name,

            terms.status
                AS term_status

        FROM applications

        JOIN people
            ON applications.person_id =
               people.person_id

        JOIN application_periods
            ON applications.application_period_id =
               application_periods.application_period_id

        JOIN terms
            ON application_periods.term_id =
               terms.term_id

        WHERE applications.application_id = ?
          AND application_periods.term_id = ?
          AND terms.status = 'ACTIVE'

        LIMIT 1
    """, (
        application_id,
        active_term_id,
    ))

    return cursor.fetchone()


# ============================================================
# GENERATE UNIQUE MEMBER USERNAME
# ============================================================

def generate_member_username(
    cursor,
    first_name,
    last_name,
):

    def clean_name(value):

        value = unicodedata.normalize(
            "NFKD",
            value,
        )

        value = "".join(
            character
            for character in value
            if not unicodedata.combining(
                character
            )
        )

        value = value.lower().strip()

        value = re.sub(
            r"[^a-z0-9]+",
            "_",
            value,
        )

        return value.strip("_")

    first_name = clean_name(
        first_name
    )

    last_name = clean_name(
        last_name
    )

    base_username = (
        f"{last_name}_{first_name}"
    )

    username = base_username

    number = 2

    while True:

        cursor.execute("""
            SELECT
                user_id

            FROM users

            WHERE LOWER(username) =
                  LOWER(?)

            LIMIT 1
        """, (
            username,
        ))

        existing_user = (
            cursor.fetchone()
        )

        if existing_user is None:
            return username

        username = (
            f"{base_username}_{number}"
        )

        number += 1


# ============================================================
# APPLICATION PERIODS
# ACTIVE + ARCHIVED HISTORY
# ============================================================

@applications_bp.route(
    "/applications/periods"
)
@login_required
def application_periods():

    current_user = (
        get_current_user()
    )

    if not can_manage_application_periods(
        current_user
    ):

        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            application_periods.application_period_id,
            application_periods.name,
            application_periods.start_date,
            application_periods.end_date,

            terms.term_id,

            terms.name
                AS term_name,

            terms.status
                AS term_status

        FROM application_periods

        JOIN terms
            ON application_periods.term_id =
               terms.term_id

        WHERE terms.status IN (
            'ACTIVE',
            'ARCHIVED'
        )

        ORDER BY
            application_periods.start_date DESC
    """)

    periods = cursor.fetchall()

    conn.close()

    return render_template(
        "application_periods.html",
        periods=periods,
    )


# ============================================================
# NEW APPLICATION PERIOD
# ACTIVE MANDATE ONLY
# ============================================================

@applications_bp.route(
    "/applications/periods/new",
    methods=[
        "GET",
        "POST",
    ],
)
@login_required
def new_application_period():

    current_user = (
        get_current_user()
    )

    if not can_manage_application_periods(
        current_user
    ):

        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term = (
        get_active_term_row(
            cursor
        )
    )

    if active_term is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    active_term_id = (
        active_term[
            "term_id"
        ]
    )

    # Existing HTML expects a list
    # called "terms".
    # Only the active mandate is available.

    terms = [
        active_term
    ]

    error = None

    if request.method == "POST":

        name = request.form.get(
            "name",
            "",
        ).strip()

        submitted_term_id = (
            request.form.get(
                "term_id",
                "",
            ).strip()
        )

        start_date = (
            request.form.get(
                "start_date",
                "",
            ).strip()
        )

        end_date = (
            request.form.get(
                "end_date",
                "",
            ).strip()
        )

        if not name:

            error = (
                "Period name is required."
            )

        elif not submitted_term_id:

            error = (
                "Academic year is required."
            )

        elif (
            not start_date
            or not end_date
        ):

            error = (
                "Start date and end date "
                "are required."
            )

        elif end_date <= start_date:

            error = (
                "End date must be after "
                "start date."
            )

        else:

            try:

                submitted_term_id = int(
                    submitted_term_id
                )

            except (
                TypeError,
                ValueError,
            ):

                error = (
                    "Invalid academic year."
                )

        if (
            error is None

            and submitted_term_id
            != active_term_id
        ):

            error = (
                "Recruitment periods can only "
                "be created for the active "
                "mandate."
            )

        # ====================================================
        # DUPLICATE
        # ====================================================

        if error is None:

            cursor.execute("""
                SELECT
                    application_period_id

                FROM application_periods

                WHERE LOWER(name) =
                      LOWER(?)

                  AND term_id = ?
            """, (
                name,
                active_term_id,
            ))

            existing_period = (
                cursor.fetchone()
            )

            if existing_period is not None:

                error = (
                    "A recruitment period with "
                    "this name already exists "
                    "for this academic year."
                )

        # ====================================================
        # CREATE
        # ====================================================

        if error is None:

            cursor.execute("""
                INSERT INTO application_periods (
                    term_id,
                    name,
                    start_date,
                    end_date
                )

                VALUES (?, ?, ?, ?)
            """, (
                active_term_id,
                name,
                start_date,
                end_date,
            ))

            conn.commit()
            conn.close()

            return redirect(
                url_for(
                    "applications.application_periods"
                )
            )

    conn.close()

    return render_template(
        "new_application_period.html",
        terms=terms,
        error=error,
    )


# ============================================================
# EDIT APPLICATION PERIOD
# ACTIVE MANDATE ONLY
# ============================================================

@applications_bp.route(
    "/applications/periods/<int:application_period_id>/edit",
    methods=[
        "GET",
        "POST",
    ],
)
@login_required
def edit_application_period(
    application_period_id,
):

    current_user = (
        get_current_user()
    )

    if not can_manage_application_periods(
        current_user
    ):

        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term = (
        get_active_term_row(
            cursor
        )
    )

    if active_term is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    active_term_id = (
        active_term[
            "term_id"
        ]
    )

    # ========================================================
    # PERIOD
    # ========================================================

    cursor.execute("""
        SELECT
            application_periods.application_period_id,
            application_periods.term_id,
            application_periods.name,
            application_periods.start_date,
            application_periods.end_date,

            terms.status
                AS term_status

        FROM application_periods

        JOIN terms
            ON application_periods.term_id =
               terms.term_id

        WHERE application_periods.application_period_id = ?
    """, (
        application_period_id,
    ))

    period = cursor.fetchone()

    if period is None:

        conn.close()

        return (
            "Application period not found",
            404,
        )

    if (
        period["term_id"]
        != active_term_id

        or period[
            "term_status"
        ]
        != "ACTIVE"
    ):

        conn.close()

        return (
            "Archived recruitment periods "
            "are read-only.",
            403,
        )

    terms = [
        active_term
    ]

    error = None

    if request.method == "POST":

        name = request.form.get(
            "name",
            "",
        ).strip()

        submitted_term_id = (
            request.form.get(
                "term_id",
                "",
            ).strip()
        )

        start_date = (
            request.form.get(
                "start_date",
                "",
            ).strip()
        )

        end_date = (
            request.form.get(
                "end_date",
                "",
            ).strip()
        )

        if not name:

            error = (
                "Period name is required."
            )

        elif not submitted_term_id:

            error = (
                "Academic year is required."
            )

        elif (
            not start_date
            or not end_date
        ):

            error = (
                "Start date and end date "
                "are required."
            )

        elif end_date <= start_date:

            error = (
                "End date must be after "
                "start date."
            )

        else:

            try:

                submitted_term_id = int(
                    submitted_term_id
                )

            except (
                TypeError,
                ValueError,
            ):

                error = (
                    "Invalid academic year."
                )

        if (
            error is None

            and submitted_term_id
            != active_term_id
        ):

            error = (
                "The academic year cannot "
                "be changed to another mandate."
            )

        # ====================================================
        # DUPLICATE
        # ====================================================

        if error is None:

            cursor.execute("""
                SELECT
                    application_period_id

                FROM application_periods

                WHERE LOWER(name) =
                      LOWER(?)

                  AND term_id = ?

                  AND application_period_id != ?
            """, (
                name,
                active_term_id,
                application_period_id,
            ))

            existing_period = (
                cursor.fetchone()
            )

            if existing_period is not None:

                error = (
                    "A recruitment period with "
                    "this name already exists "
                    "for this academic year."
                )

        # ====================================================
        # UPDATE
        # ====================================================

        if error is None:

            cursor.execute("""
                UPDATE application_periods

                SET
                    name = ?,
                    start_date = ?,
                    end_date = ?

                WHERE application_period_id = ?
                  AND term_id = ?
            """, (
                name,
                start_date,
                end_date,
                application_period_id,
                active_term_id,
            ))

            conn.commit()
            conn.close()

            return redirect(
                url_for(
                    "applications.application_periods"
                )
            )

    conn.close()

    return render_template(
        "edit_application_period.html",
        period=period,
        terms=terms,
        error=error,
    )


# ============================================================
# DELETE APPLICATION PERIOD
# ACTIVE MANDATE ONLY
# ============================================================

@applications_bp.route(
    "/applications/periods/<int:application_period_id>/delete",
    methods=["POST"],
)
@login_required
def delete_application_period(
    application_period_id,
):

    current_user = (
        get_current_user()
    )

    if not can_manage_application_periods(
        current_user
    ):

        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = (
        get_active_term_id()
    )

    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    cursor.execute("""
        SELECT
            application_periods.application_period_id,
            application_periods.term_id,

            terms.status
                AS term_status

        FROM application_periods

        JOIN terms
            ON application_periods.term_id =
               terms.term_id

        WHERE application_periods.application_period_id = ?
    """, (
        application_period_id,
    ))

    period = cursor.fetchone()

    if period is None:

        conn.close()

        return (
            "Application period not found",
            404,
        )

    if (
        period["term_id"]
        != active_term_id

        or period[
            "term_status"
        ]
        != "ACTIVE"
    ):

        conn.close()

        return (
            "Archived recruitment periods "
            "are read-only.",
            403,
        )

    cursor.execute("""
        SELECT
            COUNT(*) AS total

        FROM applications

        WHERE application_period_id = ?
    """, (
        application_period_id,
    ))

    applications_count = (
        cursor.fetchone()[
            "total"
        ]
    )

    if applications_count > 0:

        conn.close()

        return (
            "Cannot delete a recruitment period "
            "that already contains applications.",
            400,
        )

    cursor.execute("""
        DELETE FROM application_periods

        WHERE application_period_id = ?
          AND term_id = ?
    """, (
        application_period_id,
        active_term_id,
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "applications.application_periods"
        )
    )


# ============================================================
# APPLICATION DETAIL
# ACTIVE + ARCHIVED HISTORY
# ============================================================

@applications_bp.route(
    "/applications/<int:application_id>"
)
@login_required
def application_detail(
    application_id,
):

    current_user = (
        get_current_user()
    )

    if not can_view_applications(
        current_user
    ):

        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            applications.application_id,
            applications.motivation,
            applications.status,
            applications.submitted_at,

            people.person_id,
            people.first_name,
            people.last_name,
            people.date_of_birth,
            people.phone,
            people.email,
            people.university,
            people.faculty,
            people.profession,
            people.linkedin,

            application_periods.name
                AS period_name,

            application_periods.term_id
                AS term_id,

            terms.name
                AS term_name,

            terms.status
                AS term_status

        FROM applications

        JOIN people
            ON applications.person_id =
               people.person_id

        JOIN application_periods
            ON applications.application_period_id =
               application_periods.application_period_id

        JOIN terms
            ON application_periods.term_id =
               terms.term_id

        WHERE applications.application_id = ?

          AND terms.status IN (
              'ACTIVE',
              'ARCHIVED'
          )
    """, (
        application_id,
    ))

    application = (
        cursor.fetchone()
    )

    if application is None:

        conn.close()

        return (
            "Application not found",
            404,
        )

    # ========================================================
    # SKILLS
    # ========================================================

    cursor.execute("""
        SELECT
            skill

        FROM person_skills

        WHERE person_id = ?

        ORDER BY
            skill
    """, (
        application[
            "person_id"
        ],
    ))

    skills = cursor.fetchall()

    # ========================================================
    # MEETING
    # ========================================================

    cursor.execute("""
        SELECT
            meeting_id,
            meeting_date,
            meeting_time,
            location,
            meeting_link,
            notes,
            status,
            created_at

        FROM application_meetings

        WHERE application_id = ?

        ORDER BY
            created_at DESC

        LIMIT 1
    """, (
        application_id,
    ))

    meeting = cursor.fetchone()

    meeting_participants = []

    if meeting is not None:

        cursor.execute("""
            SELECT
                memberships.membership_id,

                people.first_name,
                people.last_name,

                roles.name
                    AS role_name

            FROM application_meeting_participants

            JOIN memberships
                ON application_meeting_participants.membership_id =
                   memberships.membership_id

            JOIN people
                ON memberships.person_id =
                   people.person_id

            JOIN roles
                ON memberships.role_id =
                   roles.role_id

            WHERE application_meeting_participants.meeting_id = ?

            ORDER BY
                people.first_name ASC,
                people.last_name ASC
        """, (
            meeting[
                "meeting_id"
            ],
        ))

        meeting_participants = (
            cursor.fetchall()
        )

    # ========================================================
    # RH MEMBERS
    # SAME MANDATE AS APPLICATION
    #
    # For an archived application this preserves
    # its historical RH membership information.
    # ========================================================

    cursor.execute("""
        SELECT
            memberships.membership_id,

            people.first_name,
            people.last_name,

            roles.name
                AS role_name

        FROM memberships

        JOIN people
            ON memberships.person_id =
               people.person_id

        LEFT JOIN users
            ON people.person_id =
               users.person_id

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        WHERE memberships.term_id = ?

          AND memberships.department_id = ?

          AND roles.name IN (
              'MEMBER',
              'SUB_HEAD',
              'HEAD'
          )

        ORDER BY
            CASE roles.name
                WHEN 'HEAD' THEN 1
                WHEN 'SUB_HEAD' THEN 2
                WHEN 'MEMBER' THEN 3
                ELSE 4
            END,

            people.first_name ASC,
            people.last_name ASC
    """, (
        application[
            "term_id"
        ],
        RH_DEPARTMENT_ID,
    ))

    rh_members = cursor.fetchall()

    is_active_application = (
        application[
            "term_status"
        ]
        == "ACTIVE"
    )

    can_process = can_process_applications(
        current_user
    )

    conn.close()

    return render_template(
        "application_detail.html",

        application=application,

        skills=skills,

        meeting=meeting,

        rh_members=rh_members,

        meeting_participants=(
            meeting_participants
        ),

        is_active_application=(
            is_active_application
        ),
        can_process=can_process,
    )


# ============================================================
# ACCEPT APPLICATION
# ACTIVE MANDATE ONLY
# ============================================================

@applications_bp.route(
    "/applications/<int:application_id>/accept",
    methods=["POST"],
)
@login_required
def accept_application(
    application_id,
):

    current_user = (
        get_current_user()
    )

    if not can_process_applications(
        current_user
    ):

        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = (
        get_active_term_id()
    )

    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    application = (
        get_application_for_action(
            cursor,
            application_id,
            active_term_id,
        )
    )

    if application is None:

        conn.close()

        return (
            "Application not found or archived "
            "application is read-only",
            404,
        )

    # ========================================================
    # MEETING REQUIRED
    # ========================================================

    if (
        application["status"]
        == "meeting_required"
    ):

        cursor.execute("""
            SELECT
                meeting_id

            FROM application_meetings

            WHERE application_id = ?
              AND status = 'completed'

            ORDER BY
                created_at DESC

            LIMIT 1
        """, (
            application_id,
        ))

        completed_meeting = (
            cursor.fetchone()
        )

        if completed_meeting is None:

            conn.close()

            return (
                "The meeting must be completed "
                "before accepting this application.",
                400,
            )

    # ========================================================
    # VALID STATUS
    # ========================================================

    if application[
        "status"
    ] not in (
        "pending",
        "meeting_required",
    ):

        conn.close()

        return (
            "Application cannot be accepted",
            400,
        )

    # ========================================================
    # TOKEN
    # ========================================================

    onboarding_token = (
        secrets.token_urlsafe(32)
    )

    cursor.execute("""
        UPDATE applications

        SET
            status = 'accepted',
            onboarding_token = ?

        WHERE application_id = ?
    """, (
        onboarding_token,
        application_id,
    ))

    conn.commit()
    conn.close()

    # ========================================================
    # ONBOARDING LINK
    # ========================================================

    onboarding_link = url_for(
        "applications.join_after_acceptance",
        token=onboarding_token,
        _external=True,
    )

    # ========================================================
    # EMAIL
    # ========================================================

    send_email(
        recipient=(
            application["email"]
        ),

        subject=(
            "ORSC - Application Accepted"
        ),

        body=(
            f"Hello {application['first_name']},\n\n"

            "Congratulations! Your application "
            "to join the Operations Research "
            "Society Club has been accepted.\n\n"

            "To complete your registration and "
            "create your ORSC CMS account, please "
            "use the following link:\n\n"

            f"{onboarding_link}\n\n"

            "You will be able to choose your "
            "department and create your password. "
            "Your username will be generated "
            "automatically by the CMS.\n\n"

            "This invitation link is personal "
            "and should not be shared.\n\n"

            "ORSC"
        ),
    )

    return redirect(
        url_for(
            "applications.application_detail",
            application_id=application_id,
        )
    )


# ============================================================
# SEND APPLICATION TO MEETING
# ACTIVE MANDATE ONLY
# ============================================================

@applications_bp.route(
    "/applications/<int:application_id>/meeting-required",
    methods=["POST"],
)
@login_required
def send_application_to_meeting(
    application_id,
):

    current_user = get_current_user()

    if not can_process_applications(
        current_user
    ):
        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    if active_term_id is None:
        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    application = get_application_for_action(
        cursor,
        application_id,
        active_term_id,
    )

    if application is None:
        conn.close()

        return (
            "Application not found or archived "
            "application is read-only",
            404,
        )

    if application["status"] != "pending":
        conn.close()

        return (
            "Application cannot be sent "
            "to a meeting.",
            400,
        )

    cursor.execute("""
        UPDATE applications

        SET status = 'meeting_required'

        WHERE application_id = ?
    """, (
        application_id,
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "applications.application_detail",
            application_id=application_id,
        )
    )


# ============================================================
# REJECT APPLICATION DIRECTLY
# ACTIVE MANDATE ONLY
# ============================================================

@applications_bp.route(
    "/applications/<int:application_id>/reject",
    methods=["POST"],
)
@login_required
def reject_application(
    application_id,
):

    current_user = get_current_user()

    if not can_process_applications(
        current_user
    ):
        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    if active_term_id is None:
        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    application = get_application_for_action(
        cursor,
        application_id,
        active_term_id,
    )

    if application is None:
        conn.close()

        return (
            "Application not found or archived "
            "application is read-only",
            404,
        )

    if application["status"] != "pending":
        conn.close()

        return (
            "Application cannot be rejected.",
            400,
        )

    cursor.execute("""
        UPDATE applications

        SET
            status = 'rejected',
            onboarding_token = NULL

        WHERE application_id = ?
    """, (
        application_id,
    ))

    conn.commit()
    conn.close()

    send_email(
        recipient=application["email"],

        subject="ORSC - Application Update",

        body=(
            f"Hello {application['first_name']},\n\n"

            "Thank you for your interest in joining "
            "the Operations Research Society Club.\n\n"

            "After reviewing your application, "
            "we are sorry to inform you that your "
            "application has not been accepted.\n\n"

            "We appreciate the time and interest "
            "you showed in ORSC and wish you all "
            "the best.\n\n"

            "ORSC"
        ),
    )

    return redirect(
        url_for(
            "applications.application_detail",
            application_id=application_id,
        )
    )


# ============================================================
# SCHEDULE APPLICATION MEETING
# ACTIVE MANDATE ONLY
# ============================================================

@applications_bp.route(
    "/applications/<int:application_id>/meeting",
    methods=["POST"],
)
@login_required
def schedule_application_meeting(
    application_id,
):

    current_user = (
        get_current_user()
    )

    if not can_process_applications(
        current_user
    ):

        return (
            "Access denied",
            403,
        )

    # ========================================================
    # FORM
    # ========================================================

    meeting_date = (
        request.form.get(
            "meeting_date",
            "",
        ).strip()
    )

    meeting_time = (
        request.form.get(
            "meeting_time",
            "",
        ).strip()
    )

    location = (
        request.form.get(
            "location",
            "",
        ).strip()
    )

    meeting_link = (
        request.form.get(
            "meeting_link",
            "",
        ).strip()
    )

    notes = (
        request.form.get(
            "notes",
            "",
        ).strip()
    )

    participant_ids = (
        request.form.getlist(
            "participants"
        )
    )

    if (
        not meeting_date
        or not meeting_time
    ):

        return (
            "Meeting date and time are required.",
            400,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = (
        get_active_term_id()
    )

    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    application = (
        get_application_for_action(
            cursor,
            application_id,
            active_term_id,
        )
    )

    if application is None:

        conn.close()

        return (
            "Application not found or archived "
            "application is read-only",
            404,
        )

    if (
        application["status"]
        != "meeting_required"
    ):

        conn.close()

        return (
            "A meeting can only be scheduled "
            "when a meeting is required.",
            400,
        )

    # ========================================================
    # EXISTING MEETING
    # ========================================================

    cursor.execute("""
        SELECT
            meeting_id

        FROM application_meetings

        WHERE application_id = ?
          AND status = 'scheduled'

        LIMIT 1
    """, (
        application_id,
    ))

    existing_meeting = (
        cursor.fetchone()
    )

    if existing_meeting is not None:

        conn.close()

        return (
            "A meeting is already scheduled "
            "for this application.",
            400,
        )

    # ========================================================
    # VALIDATE RH PARTICIPANTS
    # ACTIVE TERM ONLY
    # ========================================================

    valid_participant_ids = []

    for membership_id in (
        participant_ids
    ):

        cursor.execute("""
            SELECT
                memberships.membership_id

            FROM memberships

            JOIN users
                ON memberships.person_id =
                   users.person_id

            JOIN roles
                ON memberships.role_id =
                   roles.role_id

            WHERE memberships.membership_id = ?

              AND memberships.term_id = ?

              AND memberships.department_id = ?

              AND roles.name IN (
                  'MEMBER',
                  'SUB_HEAD',
                  'HEAD'
              )

              AND users.is_active = 1
        """, (
            membership_id,
            active_term_id,
            RH_DEPARTMENT_ID,
        ))

        participant = (
            cursor.fetchone()
        )

        if participant is None:

            conn.close()

            return (
                "Invalid meeting participant.",
                400,
            )

        if (
            participant[
                "membership_id"
            ]
            not in valid_participant_ids
        ):

            valid_participant_ids.append(
                participant[
                    "membership_id"
                ]
            )

    # ========================================================
    # CREATE MEETING
    # ========================================================

    cursor.execute("""
        INSERT INTO application_meetings (
            application_id,
            meeting_date,
            meeting_time,
            location,
            meeting_link,
            notes,
            status
        )

        VALUES (
            ?, ?, ?, ?, ?, ?, 'scheduled'
        )
    """, (
        application_id,
        meeting_date,
        meeting_time,
        location or None,
        meeting_link or None,
        notes or None,
    ))

    meeting_id = (
        cursor.lastrowid
    )

    # ========================================================
    # PARTICIPANTS
    # ========================================================

    for membership_id in (
        valid_participant_ids
    ):

        cursor.execute("""
            INSERT INTO application_meeting_participants (
                meeting_id,
                membership_id
            )

            VALUES (?, ?)
        """, (
            meeting_id,
            membership_id,
        ))

    conn.commit()
    conn.close()

    # ========================================================
    # EMAIL
    # ========================================================

    send_email(
        recipient=(
            application["email"]
        ),

        subject=(
            "ORSC - Application Meeting"
        ),

        body=(
            f"Hello {application['first_name']},\n\n"

            "Thank you for your application to join "
            "the Operations Research Society Club.\n\n"

            "We would like to meet with you before "
            "making the final decision regarding "
            "your application.\n\n"

            "Here are the meeting details:\n\n"

            f"Date: {meeting_date}\n"
            f"Time: {meeting_time}\n"
            f"Location: {location}\n\n"

            "Please make sure to be available at "
            "the scheduled time.\n\n"

            "ORSC"
        ),
    )

    return redirect(
        url_for(
            "applications.application_detail",
            application_id=application_id,
        )
    )


# ============================================================
# COMPLETE APPLICATION MEETING
# ACTIVE MANDATE ONLY
# ============================================================

@applications_bp.route(
    "/applications/<int:application_id>/meeting/<int:meeting_id>/complete",
    methods=["POST"],
)
@login_required
def complete_application_meeting(
    application_id,
    meeting_id,
):

    current_user = (
        get_current_user()
    )

    if not can_process_applications(
        current_user
    ):

        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = (
        get_active_term_id()
    )

    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    cursor.execute("""
        SELECT
            application_meetings.meeting_id,

            application_meetings.status
                AS meeting_status,

            applications.status
                AS application_status

        FROM application_meetings

        JOIN applications
            ON application_meetings.application_id =
               applications.application_id

        JOIN application_periods
            ON applications.application_period_id =
               application_periods.application_period_id

        JOIN terms
            ON application_periods.term_id =
               terms.term_id

        WHERE application_meetings.meeting_id = ?

          AND application_meetings.application_id = ?

          AND application_periods.term_id = ?

          AND terms.status = 'ACTIVE'
    """, (
        meeting_id,
        application_id,
        active_term_id,
    ))

    meeting = cursor.fetchone()

    if meeting is None:

        conn.close()

        return (
            "Meeting not found or archived "
            "application is read-only",
            404,
        )

    if (
        meeting[
            "application_status"
        ]
        != "meeting_required"
    ):

        conn.close()

        return (
            "This application no longer "
            "requires a meeting.",
            400,
        )

    if (
        meeting[
            "meeting_status"
        ]
        != "scheduled"
    ):

        conn.close()

        return (
            "Meeting cannot be completed.",
            400,
        )

    cursor.execute("""
        UPDATE application_meetings

        SET status = 'completed'

        WHERE meeting_id = ?
          AND application_id = ?
    """, (
        meeting_id,
        application_id,
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "applications.application_detail",
            application_id=application_id,
        )
    )


# ============================================================
# REJECT APPLICATION DEFINITELY
# ACTIVE MANDATE ONLY
# ============================================================

@applications_bp.route(
    "/applications/<int:application_id>/reject-definitely",
    methods=["POST"],
)
@login_required
def reject_application_definitely(
    application_id,
):

    current_user = (
        get_current_user()
    )

    if not can_process_applications(
        current_user
    ):

        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = (
        get_active_term_id()
    )

    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    application = (
        get_application_for_action(
            cursor,
            application_id,
            active_term_id,
        )
    )

    if application is None:

        conn.close()

        return (
            "Application not found or archived "
            "application is read-only",
            404,
        )

    if (
        application[
            "status"
        ]
        != "meeting_required"
    ):

        conn.close()

        return (
            "Application cannot be "
            "rejected definitely.",
            400,
        )

    # ========================================================
    # COMPLETED MEETING REQUIRED
    # ========================================================

    cursor.execute("""
        SELECT
            meeting_id

        FROM application_meetings

        WHERE application_id = ?
          AND status = 'completed'

        ORDER BY
            created_at DESC

        LIMIT 1
    """, (
        application_id,
    ))

    completed_meeting = (
        cursor.fetchone()
    )

    if completed_meeting is None:

        conn.close()

        return (
            "The meeting must be completed "
            "before rejecting this application "
            "definitely.",
            400,
        )

    cursor.execute("""
        UPDATE applications

        SET
            status = 'rejected',
            onboarding_token = NULL

        WHERE application_id = ?
    """, (
        application_id,
    ))

    conn.commit()
    conn.close()


    send_email(
        recipient=application["email"],

        subject="ORSC - Application Update",

        body=(
            f"Hello {application['first_name']},\n\n"

            "Thank you for your interest in joining "
            "the Operations Research Society Club "
            "and for taking the time to meet with us.\n\n"

            "After completing the recruitment process, "
            "we are sorry to inform you that your "
            "application has not been accepted.\n\n"

            "We appreciate your time and interest "
            "in ORSC and wish you all the best.\n\n"

            "ORSC"
        ),
    )
    

    return redirect(
        url_for(
            "applications.application_detail",
            application_id=application_id,
        )
    )


# ============================================================
# APPLICATIONS LIST
# ACTIVE + ARCHIVED HISTORY
# ============================================================

@applications_bp.route(
    "/applications"
)
@login_required
def applications():

    current_user = (
        get_current_user()
    )

    if not can_view_applications(
        current_user
    ):

        return (
            "Access denied",
            403,
        )

    status_filter = request.args.get(
        "status",
        "all",
    )

    allowed_statuses = [
        "all",
        "pending",
        "meeting_required",
        "accepted",
        "rejected",
    ]

    if (
        status_filter
        not in allowed_statuses
    ):

        status_filter = "all"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            applications.application_id,
            applications.status,
            applications.submitted_at,
            applications.motivation,

            people.person_id,
            people.first_name,
            people.last_name,
            people.email,
            people.phone,

            application_periods.application_period_id,

            application_periods.name
                AS period_name,

            terms.term_id,

            terms.name
                AS term_name,

            terms.status
                AS term_status

        FROM applications

        JOIN people
            ON applications.person_id =
               people.person_id

        JOIN application_periods
            ON applications.application_period_id =
               application_periods.application_period_id

        JOIN terms
            ON application_periods.term_id =
               terms.term_id

        WHERE terms.status IN (
            'ACTIVE',
            'ARCHIVED'
        )

          AND (
                ? = 'all'
                OR applications.status = ?
          )

        ORDER BY
            CASE terms.status
                WHEN 'ACTIVE' THEN 1
                WHEN 'ARCHIVED' THEN 2
                ELSE 3
            END,

            CASE applications.status
                WHEN 'pending' THEN 1
                WHEN 'meeting_required' THEN 2
                WHEN 'accepted' THEN 3
                WHEN 'rejected' THEN 4
                ELSE 5
            END,

            applications.submitted_at DESC
    """, (
        status_filter,
        status_filter,
    ))

    all_applications = (
        cursor.fetchall()
    )

    conn.close()

    return render_template(
        "applications.html",

        applications=(
            all_applications
        ),

        status_filter=(
            status_filter
        ),
    )


# ============================================================
# PUBLIC APPLICATION FORM
# ACTIVE RECRUITMENT PERIOD ONLY
# ============================================================

@applications_bp.route(
    "/apply",
    methods=[
        "GET",
        "POST",
    ],
)
def apply():

    conn = get_db_connection()
    cursor = conn.cursor()

    # Only a recruitment period belonging to
    # the ACTIVE mandate can open the public form.

    cursor.execute("""
        SELECT
            application_periods.application_period_id,
            application_periods.name,
            application_periods.start_date,
            application_periods.end_date,

            terms.term_id,

            terms.name
                AS term_name

        FROM application_periods

        JOIN terms
            ON application_periods.term_id =
               terms.term_id

        WHERE terms.status = 'ACTIVE'

          AND DATE('now')
              BETWEEN
              application_periods.start_date
              AND
              application_periods.end_date

        ORDER BY
            application_periods.start_date DESC

        LIMIT 1
    """)

    active_period = (
        cursor.fetchone()
    )

    error = None
    success = False

    # ========================================================
    # CLOSED
    # ========================================================

    if active_period is None:

        conn.close()

        return render_template(
            "apply.html",
            active_period=None,
            error=None,
            success=False,
        )

    # ========================================================
    # SUBMISSION
    # ========================================================

    if request.method == "POST":

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

        date_of_birth = (
            request.form.get(
                "date_of_birth",
                "",
            ).strip()
        )

        phone = (
            request.form.get(
                "phone",
                "",
            ).strip()
        )

        email = (
            request.form.get(
                "email",
                "",
            ).strip()
        )

        university = (
            request.form.get(
                "university",
                "",
            ).strip()
        )

        faculty = (
            request.form.get(
                "faculty",
                "",
            ).strip()
        )

        profession = (
            request.form.get(
                "profession",
                "",
            ).strip()
        )

        linkedin = (
            request.form.get(
                "linkedin",
                "",
            ).strip()
        )

        motivation = (
            request.form.get(
                "motivation",
                "",
            ).strip()
        )

        skills_text = (
            request.form.get(
                "skills",
                "",
            ).strip()
        )

        # ====================================================
        # REQUIRED
        # ====================================================

        if not first_name:

            error = (
                "First name is required."
            )

        elif not last_name:

            error = (
                "Last name is required."
            )

        elif not date_of_birth:

            error = (
                "Date of birth is required."
            )

        elif not phone:

            error = (
                "Phone number is required."
            )

        elif not email:

            error = (
                "Email is required."
            )

        elif not profession:

            error = (
                "Profession is required."
            )

        elif not motivation:

            error = (
                "Motivation is required."
            )

        existing_person = None
        person_id = None

        # ====================================================
        # EXISTING PERSON / APPLICATION
        # ====================================================

        if error is None:

            cursor.execute("""
                SELECT
                    person_id

                FROM people

                WHERE LOWER(email) =
                      LOWER(?)

                LIMIT 1
            """, (
                email,
            ))

            existing_person = (
                cursor.fetchone()
            )

            if existing_person is not None:

                person_id = (
                    existing_person[
                        "person_id"
                    ]
                )

                cursor.execute("""
                    SELECT
                        application_id

                    FROM applications

                    WHERE person_id = ?

                      AND application_period_id = ?
                """, (
                    person_id,
                    active_period[
                        "application_period_id"
                    ],
                ))

                existing_application = (
                    cursor.fetchone()
                )

                if (
                    existing_application
                    is not None
                ):

                    error = (
                        "An application with this "
                        "email has already been "
                        "submitted for this "
                        "recruitment period."
                    )

        # ====================================================
        # SAVE
        # ====================================================

        if error is None:

            try:

                if existing_person is None:

                    cursor.execute("""
                        INSERT INTO people (
                            first_name,
                            last_name,
                            date_of_birth,
                            phone,
                            email,
                            university,
                            faculty,
                            linkedin,
                            profession
                        )

                        VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    """, (
                        first_name,
                        last_name,
                        date_of_birth,
                        phone,
                        email,
                        university or None,
                        faculty or None,
                        linkedin or None,
                        profession,
                    ))

                    person_id = (
                        cursor.lastrowid
                    )

                cursor.execute("""
                    INSERT INTO applications (
                        application_period_id,
                        person_id,
                        motivation,
                        status
                    )

                    VALUES (
                        ?, ?, ?, 'pending'
                    )
                """, (
                    active_period[
                        "application_period_id"
                    ],
                    person_id,
                    motivation,
                ))

                # ============================================
                # SKILLS
                # ============================================

                if skills_text:

                    skills = [
                        skill.strip()

                        for skill
                        in skills_text.split(",")

                        if skill.strip()
                    ]

                    for skill in skills:

                        cursor.execute("""
                            INSERT OR IGNORE
                            INTO person_skills (
                                person_id,
                                skill
                            )

                            VALUES (?, ?)
                        """, (
                            person_id,
                            skill,
                        ))

                conn.commit()

                success = True

            except Exception:

                conn.rollback()
                conn.close()

                raise

    conn.close()

    return render_template(
        "apply.html",
        active_period=active_period,
        error=error,
        success=success,
    )


# ============================================================
# ACCEPTED CANDIDATE ONBOARDING
# PUBLIC - SECURE TOKEN
# ACTIVE MANDATE ONLY
# ============================================================

@applications_bp.route(
    "/join/<string:token>",
    methods=[
        "GET",
        "POST",
    ],
)
def join_after_acceptance(
    token,
):

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = (
        get_active_term_id()
    )

    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    # ========================================================
    # FIND ACCEPTED APPLICATION
    #
    # The invitation automatically becomes invalid
    # if its mandate is no longer ACTIVE.
    # ========================================================

    cursor.execute("""
        SELECT
            applications.application_id,
            applications.person_id,
            applications.status,
            applications.onboarding_token,

            people.first_name,
            people.last_name,
            people.email,

            application_periods.term_id,

            terms.name
                AS term_name,

            terms.status
                AS term_status

        FROM applications

        JOIN people
            ON applications.person_id =
               people.person_id

        JOIN application_periods
            ON applications.application_period_id =
               application_periods.application_period_id

        JOIN terms
            ON application_periods.term_id =
               terms.term_id

        WHERE applications.onboarding_token = ?

          AND applications.status = 'accepted'

          AND application_periods.term_id = ?

          AND terms.status = 'ACTIVE'

        LIMIT 1
    """, (
        token,
        active_term_id,
    ))

    application = (
        cursor.fetchone()
    )

    if application is None:

        conn.close()

        return (
            "Invalid or expired invitation link",
            404,
        )

    # ========================================================
    # ACCOUNT MUST NOT ALREADY EXIST
    # ========================================================

    cursor.execute("""
        SELECT
            user_id

        FROM users

        WHERE person_id = ?
    """, (
        application[
            "person_id"
        ],
    ))

    existing_user = (
        cursor.fetchone()
    )

    if existing_user is not None:

        conn.close()

        return (
            "Account already created",
            400,
        )

    # ========================================================
    # DEPARTMENTS
    # ========================================================

    cursor.execute("""
        SELECT
            department_id,
            name

        FROM departments

        ORDER BY
            name
    """)

    departments = (
        cursor.fetchall()
    )

    # ========================================================
    # USERNAME
    # ========================================================

    generated_username = (
        generate_member_username(
            cursor,
            application[
                "first_name"
            ],
            application[
                "last_name"
            ],
        )
    )

    error = None

    account_created = False

    # ========================================================
    # CREATE ACCOUNT
    # ========================================================

    if request.method == "POST":

        password = request.form.get(
            "password",
            "",
        )

        department_id = (
            request.form.get(
                "department_id",
                "",
            ).strip()
        )

        if not password:

            error = (
                "Password is required."
            )

        elif len(password) < 8:

            error = (
                "Password must contain at least "
                "8 characters."
            )

        elif not department_id:

            error = (
                "Department is required."
            )

        # ====================================================
        # VALID DEPARTMENT
        # ====================================================

        if error is None:

            cursor.execute("""
                SELECT
                    department_id

                FROM departments

                WHERE department_id = ?
            """, (
                department_id,
            ))

            if cursor.fetchone() is None:

                error = (
                    "Invalid department."
                )

        # ====================================================
        # MEMBER ROLE
        # ====================================================

        member_role = None

        if error is None:

            cursor.execute("""
                SELECT
                    role_id

                FROM roles

                WHERE name = 'MEMBER'

                LIMIT 1
            """)

            member_role = (
                cursor.fetchone()
            )

            if member_role is None:

                error = (
                    "MEMBER role not found."
                )

        # ====================================================
        # RE-CHECK ACTIVE MANDATE
        #
        # Important if the mandate changed while
        # the user had the page open.
        # ====================================================

        if error is None:

            cursor.execute("""
                SELECT
                    term_id

                FROM terms

                WHERE term_id = ?
                  AND status = 'ACTIVE'

                LIMIT 1
            """, (
                application[
                    "term_id"
                ],
            ))

            if cursor.fetchone() is None:

                error = (
                    "This invitation is no longer "
                    "valid for the active mandate."
                )

        # ====================================================
        # CREATE USER + MEMBERSHIP
        # ====================================================

        if error is None:

            password_hash = (
                generate_password_hash(
                    password
                )
            )

            try:

                cursor.execute("""
                    INSERT INTO users (
                        person_id,
                        username,
                        password_hash,
                        is_active
                    )

                    VALUES (
                        ?, ?, ?, 1
                    )
                """, (
                    application[
                        "person_id"
                    ],
                    generated_username,
                    password_hash,
                ))

                cursor.execute("""
                    INSERT INTO memberships (
                        person_id,
                        term_id,
                        role_id,
                        department_id
                    )

                    VALUES (?, ?, ?, ?)
                """, (
                    application[
                        "person_id"
                    ],
                    application[
                        "term_id"
                    ],
                    member_role[
                        "role_id"
                    ],
                    department_id,
                ))

                # Token used once.

                cursor.execute("""
                    UPDATE applications

                    SET onboarding_token = NULL

                    WHERE application_id = ?
                      AND onboarding_token = ?
                """, (
                    application[
                        "application_id"
                    ],
                    token,
                ))

                conn.commit()

                account_created = True

            except Exception:

                conn.rollback()
                conn.close()

                raise

    conn.close()

    return render_template(
        "join_after_acceptance.html",

        application=application,

        departments=departments,

        generated_username=(
            generated_username
        ),

        error=error,

        account_created=(
            account_created
        ),
    )