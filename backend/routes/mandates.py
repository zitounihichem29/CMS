import os
import sqlite3
import uuid
from datetime import datetime

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

from context import get_active_term_id, get_current_user
from database import get_db_connection
from permissions import login_required


mandates_bp = Blueprint("mandates", __name__)

HR_DEPARTMENT_ID = 1

EXECUTIVE_ROLES = {
    "PRESIDENT",
    "VICE_PRESIDENT",
    "SECRETARY_GENERAL",
}

BOARD_EDITABLE_ROLES = {
    "MEMBER",
    "SUB_HEAD",
    "HEAD",
}

ELECTION_REPORT_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
}


def _redirect_to_mandate(term_id):
    return redirect(
        url_for(
            "mandates.mandate_detail",
            term_id=term_id,
        )
    )


def _parse_date(value, label):
    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d",
        )

    except (TypeError, ValueError) as error:
        raise ValueError(
            f"Invalid {label}."
        ) from error


def _validate_term_fields(
    cursor,
    name,
    start_date,
    end_date,
    exclude_term_id=None,
):
    if not name:
        return "Mandate name is required."

    if not start_date or not end_date:
        return "Start date and end date are required."

    try:
        parsed_start = _parse_date(
            start_date,
            "start date",
        )

        parsed_end = _parse_date(
            end_date,
            "end date",
        )

    except ValueError as error:
        return str(error)

    if parsed_end <= parsed_start:
        return "End date must be after start date."

    if exclude_term_id is None:
        cursor.execute(
            """
            SELECT term_id
            FROM terms
            WHERE LOWER(name) = LOWER(?)
            LIMIT 1
            """,
            (name,),
        )

    else:
        cursor.execute(
            """
            SELECT term_id
            FROM terms
            WHERE LOWER(name) = LOWER(?)
              AND term_id != ?
            LIMIT 1
            """,
            (
                name,
                exclude_term_id,
            ),
        )

    if cursor.fetchone() is not None:
        return (
            "A mandate with this name "
            "already exists."
        )

    return None


def _emergency_reason(
    current_user,
    normal_permission,
):
    if (
        is_platform_admin(current_user)
        and not normal_permission
    ):
        reason = request.form.get(
            "emergency_reason",
            "",
        ).strip()

        if not reason:
            raise ValueError(
                "An emergency reason is required "
                "for Platform Administrator action."
            )

        return reason

    return None


def save_election_report_file(
    report_file,
    term_id,
):
    if (
        report_file is None
        or not report_file.filename
    ):
        return None

    filename = secure_filename(
        report_file.filename
    )

    if not filename:
        raise ValueError(
            "Invalid election report filename."
        )

    extension = os.path.splitext(
        filename
    )[1].lower()

    if extension not in ELECTION_REPORT_EXTENSIONS:
        raise ValueError(
            "Election report must be a PDF "
            "or Word document."
        )

    unique_filename = (
        f"{uuid.uuid4().hex}_{filename}"
    )

    upload_folder = os.path.join(
        current_app.root_path,
        "uploads",
        "mandates",
        "elections",
        str(term_id),
    )

    os.makedirs(
        upload_folder,
        exist_ok=True,
    )

    full_path = os.path.join(
        upload_folder,
        unique_filename,
    )

    report_file.save(
        full_path
    )

    return (
        f"uploads/mandates/elections/"
        f"{term_id}/{unique_filename}"
    )


def delete_election_report_file(
    relative_path,
):
    if not relative_path:
        return

    normalized_path = (
        relative_path.replace(
            "\\",
            "/",
        )
    )

    full_path = os.path.realpath(
        os.path.join(
            current_app.root_path,
            *normalized_path.split("/"),
        )
    )

    root_path = os.path.realpath(
        current_app.root_path
    )

    try:
        if (
            os.path.commonpath(
                [
                    root_path,
                    full_path,
                ]
            )
            != root_path
        ):
            return

    except ValueError:
        return

    if os.path.isfile(
        full_path
    ):
        try:
            os.remove(
                full_path
            )
        except OSError:
            pass


def is_platform_admin(user):
    return (
        user is not None
        and bool(
            user["is_platform_admin"]
        )
    )


def is_current_president(user):
    return (
        user is not None
        and not user["is_alumni"]
        and user["role_name"] == "PRESIDENT"
    )


def is_current_vice_president(user):
    return (
        user is not None
        and not user["is_alumni"]
        and user["role_name"]
        == "VICE_PRESIDENT"
    )


def is_current_presidency(user):
    return (
        is_current_president(user)
        or is_current_vice_president(user)
    )


def is_current_hr_head(user):
    return (
        user is not None
        and not user["is_alumni"]
        and user["role_name"] == "HEAD"
        and user["department_id"]
        == HR_DEPARTMENT_ID
    )


def can_view_mandates(user):
    return (
        is_platform_admin(user)
        or is_current_presidency(user)
        or is_current_hr_head(user)
    )


def can_create_draft(user):
    return (
        is_platform_admin(user)
        or is_current_presidency(user)
    )


def can_edit_draft_basic_info(user):
    return (
        is_platform_admin(user)
        or is_current_presidency(user)
    )


def can_manage_election(user):
    return (
        is_platform_admin(user)
        or is_current_presidency(user)
    )


def can_edit_draft_board(user):
    return (
        is_platform_admin(user)
        or is_current_hr_head(user)
    )


def can_approve_as_president(user):
    return (
        is_platform_admin(user)
        or is_current_president(user)
    )


def can_approve_as_vice_president(user):
    return (
        is_platform_admin(user)
        or is_current_vice_president(user)
    )


def can_activate_draft(user):
    return (
        is_platform_admin(user)
        or is_current_president(user)
    )


def can_delete_draft(user):
    return (
        is_platform_admin(user)
        or is_current_president(user)
    )


def can_emergency_manage_mandates(user):
    return is_platform_admin(user)


def get_term(
    cursor,
    term_id,
):
    cursor.execute(
        """
        SELECT
            term_id,
            name,
            start_date,
            end_date,
            status
        FROM terms
        WHERE term_id = ?
        """,
        (term_id,),
    )

    return cursor.fetchone()


def get_draft_term(
    cursor,
    term_id,
):
    cursor.execute(
        """
        SELECT
            term_id,
            name,
            start_date,
            end_date,
            status
        FROM terms
        WHERE term_id = ?
          AND status = 'DRAFT'
        """,
        (term_id,),
    )

    return cursor.fetchone()


def get_role(
    cursor,
    role_id,
):
    cursor.execute(
        """
        SELECT
            role_id,
            name,
            description
        FROM roles
        WHERE role_id = ?
        """,
        (role_id,),
    )

    return cursor.fetchone()


def person_exists(
    cursor,
    person_id,
):
    cursor.execute(
        """
        SELECT person_id
        FROM people
        WHERE person_id = ?
        """,
        (person_id,),
    )

    return (
        cursor.fetchone()
        is not None
    )


def department_exists(
    cursor,
    department_id,
):
    cursor.execute(
        """
        SELECT department_id
        FROM departments
        WHERE department_id = ?
        """,
        (department_id,),
    )

    return (
        cursor.fetchone()
        is not None
    )


def get_mandate_election(
    cursor,
    term_id,
):
    cursor.execute(
        """
        SELECT
            election_id,
            term_id,
            election_date,
            report_path,
            notes,
            recorded_by_user_id,
            recorded_at,
            updated_by_user_id,
            updated_at
        FROM mandate_elections
        WHERE term_id = ?
        """,
        (term_id,),
    )

    return cursor.fetchone()


def get_mandate_approvals(
    cursor,
    term_id,
):
    cursor.execute(
        """
        SELECT
            mandate_approvals.approval_id,
            mandate_approvals.approval_type,
            mandate_approvals.approved_by_user_id,
            mandate_approvals.approved_at,
            users.username,
            people.first_name,
            people.last_name
        FROM mandate_approvals
        JOIN users
            ON mandate_approvals.approved_by_user_id =
               users.user_id
        JOIN people
            ON users.person_id =
               people.person_id
        WHERE mandate_approvals.term_id = ?
        ORDER BY mandate_approvals.approval_type
        """,
        (term_id,),
    )

    approvals = {
        "PRESIDENT": None,
        "VICE_PRESIDENT": None,
    }

    for row in cursor.fetchall():
        approvals[
            row["approval_type"]
        ] = row

    return approvals


def log_mandate_action(
    cursor,
    term_id,
    actor_user_id,
    action,
    details=None,
    emergency_reason=None,
):
    term = get_term(
        cursor,
        term_id,
    )

    if term is None:
        raise ValueError(
            "Cannot log an action "
            "for an unknown mandate."
        )

    cursor.execute(
        """
        INSERT INTO mandate_audit_log (
            term_id,
            term_name,
            actor_user_id,
            action,
            details,
            emergency_reason
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            term_id,
            term["name"],
            actor_user_id,
            action,
            details,
            emergency_reason,
        ),
    )


def reset_mandate_approvals(
    cursor,
    term_id,
    actor_user_id,
    reason=None,
    emergency_reason=None,
):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM mandate_approvals
        WHERE term_id = ?
        """,
        (term_id,),
    )

    approval_count = (
        cursor.fetchone()[0]
    )

    if approval_count == 0:
        return False

    cursor.execute(
        """
        DELETE FROM mandate_approvals
        WHERE term_id = ?
        """,
        (term_id,),
    )

    log_mandate_action(
        cursor=cursor,
        term_id=term_id,
        actor_user_id=actor_user_id,
        action="APPROVALS_RESET",
        details=(
            reason
            or
            "Draft mandate changed "
            "after approval."
        ),
        emergency_reason=(
            emergency_reason
        ),
    )

    return True


def get_person_cms_account(
    cursor,
    person_id,
):
    cursor.execute(
        """
        SELECT
            user_id,
            username,
            is_active,
            is_platform_admin
        FROM users
        WHERE person_id = ?
        LIMIT 1
        """,
        (person_id,),
    )

    return cursor.fetchone()


def get_role_holder(
    cursor,
    term_id,
    role_name,
):
    cursor.execute(
        """
        SELECT
            memberships.membership_id,
            memberships.person_id,
            memberships.department_id,
            people.first_name,
            people.last_name,
            roles.role_id,
            roles.name AS role_name,
            users.user_id,
            users.username,
            users.is_active AS user_is_active
        FROM memberships
        JOIN people
            ON memberships.person_id =
               people.person_id
        JOIN roles
            ON memberships.role_id =
               roles.role_id
        LEFT JOIN users
            ON memberships.person_id =
               users.person_id
        WHERE memberships.term_id = ?
          AND roles.name = ?
        LIMIT 1
        """,
        (
            term_id,
            role_name,
        ),
    )

    return cursor.fetchone()


def get_hr_head(
    cursor,
    term_id,
):
    cursor.execute(
        """
        SELECT
            memberships.membership_id,
            memberships.person_id,
            memberships.department_id,
            people.first_name,
            people.last_name,
            roles.role_id,
            roles.name AS role_name,
            users.user_id,
            users.username,
            users.is_active AS user_is_active
        FROM memberships
        JOIN people
            ON memberships.person_id =
               people.person_id
        JOIN roles
            ON memberships.role_id =
               roles.role_id
        LEFT JOIN users
            ON memberships.person_id =
               users.person_id
        WHERE memberships.term_id = ?
          AND roles.name = 'HEAD'
          AND memberships.department_id = ?
        LIMIT 1
        """,
        (
            term_id,
            HR_DEPARTMENT_ID,
        ),
    )

    return cursor.fetchone()


def get_required_board_state(
    cursor,
    term_id,
):
    cursor.execute(
        """
        SELECT
            SUM(
                CASE
                    WHEN roles.name = 'PRESIDENT'
                    THEN 1 ELSE 0
                END
            ) AS president_count,

            SUM(
                CASE
                    WHEN roles.name = 'VICE_PRESIDENT'
                    THEN 1 ELSE 0
                END
            ) AS vice_president_count,

            SUM(
                CASE
                    WHEN roles.name = 'SECRETARY_GENERAL'
                    THEN 1 ELSE 0
                END
            ) AS secretary_general_count,

            SUM(
                CASE
                    WHEN roles.name = 'HEAD'
                     AND memberships.department_id = ?
                    THEN 1 ELSE 0
                END
            ) AS hr_head_count

        FROM memberships

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        WHERE memberships.term_id = ?
        """,
        (
            HR_DEPARTMENT_ID,
            term_id,
        ),
    )

    row = cursor.fetchone()

    return {
        "president_count":
            row["president_count"] or 0,

        "vice_president_count":
            row["vice_president_count"] or 0,

        "secretary_general_count":
            row["secretary_general_count"] or 0,

        "hr_head_count":
            row["hr_head_count"] or 0,
    }


def get_required_account_state(
    cursor,
    term_id,
):
    holders = [
        (
            "President",
            get_role_holder(
                cursor,
                term_id,
                "PRESIDENT",
            ),
        ),
        (
            "Vice President",
            get_role_holder(
                cursor,
                term_id,
                "VICE_PRESIDENT",
            ),
        ),
        (
            "Secretary General",
            get_role_holder(
                cursor,
                term_id,
                "SECRETARY_GENERAL",
            ),
        ),
        (
            "Human Resources Head",
            get_hr_head(
                cursor,
                term_id,
            ),
        ),
    ]

    result = []

    for label, holder in holders:

        result.append(
            {
                "label": label,
                "holder": holder,
                "account_ready": bool(
                    holder
                    and holder["user_id"]
                    and holder["user_is_active"]
                ),
            }
        )

    return result


def get_mandate_validation_errors(
    cursor,
    term_id,
    include_approvals=True,
):
    errors = []

    election = get_mandate_election(
        cursor,
        term_id,
    )

    if election is None:
        errors.append(
            "The official election result "
            "has not been recorded."
        )

    board = get_required_board_state(
        cursor,
        term_id,
    )

    if board["president_count"] != 1:
        errors.append(
            "The draft mandate must contain "
            "exactly one President."
        )

    if (
        board["vice_president_count"]
        != 1
    ):
        errors.append(
            "The draft mandate must contain "
            "exactly one Vice President."
        )

    if (
        board["secretary_general_count"]
        != 1
    ):
        errors.append(
            "The draft mandate must contain "
            "exactly one Secretary General."
        )

    if board["hr_head_count"] != 1:
        errors.append(
            "The draft mandate must contain "
            "exactly one Human Resources Head."
        )

    for item in get_required_account_state(
        cursor,
        term_id,
    ):
        if (
            item["holder"] is not None
            and not item["account_ready"]
        ):
            errors.append(
                f"{item['label']} must have "
                "an active CMS account "
                "before activation."
            )

    if include_approvals:

        approvals = get_mandate_approvals(
            cursor,
            term_id,
        )

        if (
            approvals["PRESIDENT"]
            is None
        ):
            errors.append(
                "Outgoing President approval "
                "is required."
            )

        if (
            approvals["VICE_PRESIDENT"]
            is None
        ):
            errors.append(
                "Outgoing Vice President "
                "approval is required."
            )

    return errors


def get_mandate_audit_log(
    cursor,
    term_id,
    limit=30,
):
    cursor.execute(
        """
        SELECT
            mandate_audit_log.log_id,
            mandate_audit_log.action,
            mandate_audit_log.details,
            mandate_audit_log.emergency_reason,
            mandate_audit_log.created_at,
            users.username,
            people.first_name,
            people.last_name

        FROM mandate_audit_log

        LEFT JOIN users
            ON mandate_audit_log.actor_user_id =
               users.user_id

        LEFT JOIN people
            ON users.person_id =
               people.person_id

        WHERE mandate_audit_log.term_id = ?

        ORDER BY mandate_audit_log.log_id DESC

        LIMIT ?
        """,
        (
            term_id,
            limit,
        ),
    )

    return cursor.fetchall()


@mandates_bp.route(
    "/mandates"
)
@login_required
def mandates():

    current_user = (
        get_current_user()
    )

    if not can_view_mandates(
        current_user
    ):
        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            terms.term_id,
            terms.name,
            terms.start_date,
            terms.end_date,
            terms.status,
            COUNT(
                memberships.membership_id
            ) AS membership_count

        FROM terms

        LEFT JOIN memberships
            ON terms.term_id =
               memberships.term_id

        GROUP BY
            terms.term_id,
            terms.name,
            terms.start_date,
            terms.end_date,
            terms.status

        ORDER BY
            terms.start_date DESC
        """
    )

    terms = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            term_id,
            name,
            start_date,
            end_date,
            status
        FROM terms
        WHERE status = 'ACTIVE'
        LIMIT 1
        """
    )

    active_term = cursor.fetchone()

    cursor.execute(
        """
        SELECT
            term_id,
            name,
            start_date,
            end_date,
            status
        FROM terms
        WHERE status = 'DRAFT'
        LIMIT 1
        """
    )

    draft_term = cursor.fetchone()

    conn.close()

    return render_template(
        "mandates/mandates.html",

        terms=terms,

        active_term=active_term,

        draft_term=draft_term,

        can_create_draft=(
            can_create_draft(
                current_user
            )
        ),

        is_platform_admin=(
            is_platform_admin(
                current_user
            )
        ),
    )


@mandates_bp.route(
    "/mandates/new",
    methods=[
        "GET",
        "POST",
    ],
)
@login_required
def create_draft():

    current_user = (
        get_current_user()
    )

    if not can_create_draft(
        current_user
    ):
        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            term_id,
            name,
            start_date,
            end_date
        FROM terms
        WHERE status = 'DRAFT'
        LIMIT 1
        """
    )

    existing_draft = (
        cursor.fetchone()
    )

    error = None

    if request.method == "POST":

        if existing_draft is not None:

            conn.close()

            return (
                "A draft mandate "
                "already exists.",
                400,
            )

        name = request.form.get(
            "name",
            "",
        ).strip()

        start_date = request.form.get(
            "start_date",
            "",
        ).strip()

        end_date = request.form.get(
            "end_date",
            "",
        ).strip()

        error = _validate_term_fields(
            cursor,
            name,
            start_date,
            end_date,
        )

        emergency_reason = None

        if error is None:

            try:
                emergency_reason = (
                    _emergency_reason(
                        current_user,
                        is_current_presidency(
                            current_user
                        ),
                    )
                )

            except ValueError as reason_error:
                error = str(
                    reason_error
                )

        if error is None:

            try:
                cursor.execute(
                    """
                    INSERT INTO terms (
                        name,
                        start_date,
                        end_date,
                        status
                    )
                    VALUES (?, ?, ?, 'DRAFT')
                    """,
                    (
                        name,
                        start_date,
                        end_date,
                    ),
                )

                draft_term_id = (
                    cursor.lastrowid
                )

                log_mandate_action(
                    cursor=cursor,
                    term_id=draft_term_id,
                    actor_user_id=(
                        current_user[
                            "user_id"
                        ]
                    ),
                    action="DRAFT_CREATED",
                    details=(
                        "Draft mandate created."
                    ),
                    emergency_reason=(
                        emergency_reason
                    ),
                )

                conn.commit()
                conn.close()

                return (
                    _redirect_to_mandate(
                        draft_term_id
                    )
                )

            except sqlite3.IntegrityError as db_error:

                conn.rollback()

                error = (
                    "Draft mandate could "
                    "not be created: "
                    f"{db_error}"
                )

    requires_emergency_reason = (
        is_platform_admin(
            current_user
        )
        and not is_current_presidency(
            current_user
        )
    )

    conn.close()

    return render_template(
        "mandates/new_mandate.html",

        existing_draft=(
            existing_draft
        ),

        error=error,

        requires_emergency_reason=(
            requires_emergency_reason
        ),
    )


@mandates_bp.route(
    "/mandates/<int:term_id>"
)
@login_required
def mandate_detail(
    term_id,
):

    current_user = (
        get_current_user()
    )

    if not can_view_mandates(
        current_user
    ):
        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    term = get_term(
        cursor,
        term_id,
    )

    if term is None:

        conn.close()

        return (
            "Mandate not found",
            404,
        )

    cursor.execute(
        """
        SELECT
            memberships.membership_id,
            memberships.person_id,
            memberships.role_id,
            memberships.department_id,

            people.first_name,
            people.last_name,

            roles.name AS role_name,

            departments.name
                AS department_name,

            users.username,

            users.is_active
                AS user_is_active

        FROM memberships

        JOIN people
            ON memberships.person_id =
               people.person_id

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        LEFT JOIN departments
            ON memberships.department_id =
               departments.department_id

        LEFT JOIN users
            ON memberships.person_id =
               users.person_id

        WHERE memberships.term_id = ?

        ORDER BY
            CASE roles.name
                WHEN 'PRESIDENT'
                    THEN 1
                WHEN 'VICE_PRESIDENT'
                    THEN 2
                WHEN 'SECRETARY_GENERAL'
                    THEN 3
                WHEN 'HEAD'
                    THEN 4
                WHEN 'SUB_HEAD'
                    THEN 5
                WHEN 'MEMBER'
                    THEN 6
                WHEN 'ALUMNI'
                    THEN 7
                ELSE 8
            END,

            departments.department_id,

            people.first_name,
            people.last_name
        """,
        (term_id,),
    )

    memberships = (
        cursor.fetchall()
    )

    active_term_id = (
        get_active_term_id()
    )

    cursor.execute(
        """
        SELECT
            people.person_id,
            people.first_name,
            people.last_name,
            people.email,

            users.username,
            users.is_active,

            active_roles.name
                AS active_role_name,

            active_departments.name
                AS active_department_name

        FROM people

        LEFT JOIN users
            ON people.person_id =
               users.person_id

        LEFT JOIN memberships
            AS active_membership

            ON people.person_id =
               active_membership.person_id

           AND active_membership.term_id = ?

        LEFT JOIN roles
            AS active_roles

            ON active_membership.role_id =
               active_roles.role_id

        LEFT JOIN departments
            AS active_departments

            ON active_membership.department_id =
               active_departments.department_id

        ORDER BY
            people.first_name,
            people.last_name
        """,
        (active_term_id,),
    )

    people = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            role_id,
            name,
            description

        FROM roles

        WHERE name IN (
            'MEMBER',
            'SUB_HEAD',
            'HEAD'
        )

        ORDER BY
            CASE name
                WHEN 'HEAD'
                    THEN 1
                WHEN 'SUB_HEAD'
                    THEN 2
                WHEN 'MEMBER'
                    THEN 3
                ELSE 4
            END
        """
    )

    board_roles = (
        cursor.fetchall()
    )

    cursor.execute(
        """
        SELECT
            department_id,
            name
        FROM departments
        ORDER BY department_id
        """
    )

    departments = (
        cursor.fetchall()
    )

    election = (
        get_mandate_election(
            cursor,
            term_id,
        )
    )

    approvals = (
        get_mandate_approvals(
            cursor,
            term_id,
        )
    )

    incoming_president = (
        get_role_holder(
            cursor,
            term_id,
            "PRESIDENT",
        )
    )

    incoming_vice_president = (
        get_role_holder(
            cursor,
            term_id,
            "VICE_PRESIDENT",
        )
    )

    incoming_secretary_general = (
        get_role_holder(
            cursor,
            term_id,
            "SECRETARY_GENERAL",
        )
    )

    required_accounts = (
        get_required_account_state(
            cursor,
            term_id,
        )
    )

    audit_log = (
        get_mandate_audit_log(
            cursor,
            term_id,
        )
    )

    validation_errors = []
    preapproval_errors = []

    if term["status"] == "DRAFT":

        validation_errors = (
            get_mandate_validation_errors(
                cursor,
                term_id,
                include_approvals=True,
            )
        )

        preapproval_errors = (
            get_mandate_validation_errors(
                cursor,
                term_id,
                include_approvals=False,
            )
        )

    can_basic = (
        term["status"] == "DRAFT"
        and can_edit_draft_basic_info(
            current_user
        )
    )

    can_election = (
        term["status"] == "DRAFT"
        and can_manage_election(
            current_user
        )
    )

    can_board = (
        term["status"] == "DRAFT"
        and can_edit_draft_board(
            current_user
        )
    )

    can_president_approve = (
        term["status"] == "DRAFT"
        and can_approve_as_president(
            current_user
        )
    )

    can_vp_approve = (
        term["status"] == "DRAFT"
        and can_approve_as_vice_president(
            current_user
        )
    )

    can_activate = (
        term["status"] == "DRAFT"
        and can_activate_draft(
            current_user
        )
    )

    can_delete = (
        term["status"] == "DRAFT"
        and can_delete_draft(
            current_user
        )
    )

    template_context = {

        "term": term,

        "memberships":
            memberships,

        "people":
            people,

        "board_roles":
            board_roles,

        "departments":
            departments,

        "election":
            election,

        "approvals":
            approvals,

        "incoming_president":
            incoming_president,

        "incoming_vice_president":
            incoming_vice_president,

        "incoming_secretary_general":
            incoming_secretary_general,

        "required_accounts":
            required_accounts,

        "audit_log":
            audit_log,

        "validation_errors":
            validation_errors,

        "preapproval_errors":
            preapproval_errors,

        "can_edit_basic":
            can_basic,

        "can_manage_election":
            can_election,

        "can_edit_board":
            can_board,

        "can_approve_president":
            can_president_approve,

        "can_approve_vp":
            can_vp_approve,

        "can_activate":
            can_activate,

        "can_delete_draft":
            can_delete,

        "is_platform_admin":
            is_platform_admin(
                current_user
            ),

        "basic_emergency_reason": (
            can_basic
            and is_platform_admin(
                current_user
            )
            and not is_current_presidency(
                current_user
            )
        ),

        "election_emergency_reason": (
            can_election
            and is_platform_admin(
                current_user
            )
            and not is_current_presidency(
                current_user
            )
        ),

        "board_emergency_reason": (
            can_board
            and is_platform_admin(
                current_user
            )
            and not is_current_hr_head(
                current_user
            )
        ),

        "president_approval_emergency_reason": (
            can_president_approve
            and is_platform_admin(
                current_user
            )
            and not is_current_president(
                current_user
            )
        ),

        "vp_approval_emergency_reason": (
            can_vp_approve
            and is_platform_admin(
                current_user
            )
            and not is_current_vice_president(
                current_user
            )
        ),

        "activation_emergency_reason": (
            can_activate
            and is_platform_admin(
                current_user
            )
            and not is_current_president(
                current_user
            )
        ),

        "delete_emergency_reason": (
            can_delete
            and is_platform_admin(
                current_user
            )
            and not is_current_president(
                current_user
            )
        ),
    }

    conn.close()

    return render_template(
        "mandates/mandate_detail.html",
        **template_context,
    )


@mandates_bp.route(
    "/mandates/<int:term_id>/basic/save",
    methods=["POST"],
)
@login_required
def save_draft_basic_info(
    term_id,
):

    current_user = (
        get_current_user()
    )

    if not can_edit_draft_basic_info(
        current_user
    ):
        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    term = get_draft_term(
        cursor,
        term_id,
    )

    if term is None:

        conn.close()

        return (
            "Draft mandate not found",
            404,
        )

    name = request.form.get(
        "name",
        "",
    ).strip()

    start_date = request.form.get(
        "start_date",
        "",
    ).strip()

    end_date = request.form.get(
        "end_date",
        "",
    ).strip()

    error = _validate_term_fields(
        cursor,
        name,
        start_date,
        end_date,
        exclude_term_id=term_id,
    )

    if error:

        conn.close()

        return (
            error,
            400,
        )

    try:
        emergency_reason = (
            _emergency_reason(
                current_user,
                is_current_presidency(
                    current_user
                ),
            )
        )

    except ValueError as reason_error:

        conn.close()

        return (
            str(reason_error),
            400,
        )

    changed = (
        name != term["name"]
        or start_date
        != term["start_date"]
        or end_date
        != term["end_date"]
    )

    if not changed:

        conn.close()

        return (
            _redirect_to_mandate(
                term_id
            )
        )

    try:
        cursor.execute(
            """
            UPDATE terms
            SET
                name = ?,
                start_date = ?,
                end_date = ?
            WHERE term_id = ?
              AND status = 'DRAFT'
            """,
            (
                name,
                start_date,
                end_date,
                term_id,
            ),
        )

        reset_mandate_approvals(
            cursor=cursor,
            term_id=term_id,
            actor_user_id=(
                current_user[
                    "user_id"
                ]
            ),
            reason=(
                "Basic mandate "
                "information changed."
            ),
            emergency_reason=(
                emergency_reason
            ),
        )

        log_mandate_action(
            cursor=cursor,
            term_id=term_id,
            actor_user_id=(
                current_user[
                    "user_id"
                ]
            ),
            action=(
                "BASIC_INFO_UPDATED"
            ),
            details=(
                "Mandate name or dates "
                "were updated."
            ),
            emergency_reason=(
                emergency_reason
            ),
        )

        conn.commit()

    except sqlite3.IntegrityError as db_error:

        conn.rollback()
        conn.close()

        return (
            "Mandate information could "
            f"not be saved: {db_error}",
            400,
        )

    conn.close()

    return _redirect_to_mandate(
        term_id
    )


@mandates_bp.route(
    "/mandates/<int:term_id>/election/report"
)
@login_required
def election_report(
    term_id,
):

    current_user = (
        get_current_user()
    )

    if not can_view_mandates(
        current_user
    ):
        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    term = get_term(
        cursor,
        term_id,
    )

    if term is None:

        conn.close()

        return (
            "Mandate not found",
            404,
        )

    election = (
        get_mandate_election(
            cursor,
            term_id,
        )
    )

    if (
        election is None
        or not election[
            "report_path"
        ]
    ):
        conn.close()

        return (
            "Election report not found",
            404,
        )

    report_path = (
        election[
            "report_path"
        ].replace(
            "\\",
            "/",
        )
    )

    conn.close()

    return send_from_directory(
        current_app.root_path,
        report_path,
        as_attachment=False,
    )


@mandates_bp.route(
    "/mandates/<int:term_id>/election/save",
    methods=["POST"],
)
@login_required
def save_election_result(
    term_id,
):

    current_user = (
        get_current_user()
    )

    if not can_manage_election(
        current_user
    ):
        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    term = get_draft_term(
        cursor,
        term_id,
    )

    if term is None:

        conn.close()

        return (
            "Draft mandate not found",
            404,
        )

    try:
        emergency_reason = (
            _emergency_reason(
                current_user,
                is_current_presidency(
                    current_user
                ),
            )
        )

    except ValueError as reason_error:

        conn.close()

        return (
            str(reason_error),
            400,
        )

    election_date = (
        request.form.get(
            "election_date",
            "",
        ).strip()
    )

    president_person_id = (
        request.form.get(
            "president_person_id",
            "",
        ).strip()
    )

    vice_president_person_id = (
        request.form.get(
            "vice_president_person_id",
            "",
        ).strip()
    )

    secretary_general_person_id = (
        request.form.get(
            "secretary_general_person_id",
            "",
        ).strip()
    )

    notes = request.form.get(
        "notes",
        "",
    ).strip()

    report_file = (
        request.files.get(
            "report_file"
        )
    )

    remove_report = (
        request.form.get(
            "remove_report"
        )
        == "1"
    )

    if not election_date:

        conn.close()

        return (
            "Election date is required.",
            400,
        )

    try:
        _parse_date(
            election_date,
            "election date",
        )

    except ValueError as date_error:

        conn.close()

        return (
            str(date_error),
            400,
        )

    raw_person_ids = [
        president_person_id,
        vice_president_person_id,
        secretary_general_person_id,
    ]

    if any(
        not value
        for value
        in raw_person_ids
    ):
        conn.close()

        return (
            "President, Vice President "
            "and Secretary General "
            "are required.",
            400,
        )

    try:
        president_person_id = int(
            president_person_id
        )

        vice_president_person_id = int(
            vice_president_person_id
        )

        secretary_general_person_id = int(
            secretary_general_person_id
        )

    except (
        TypeError,
        ValueError,
    ):
        conn.close()

        return (
            "Invalid election result.",
            400,
        )

    selected_people = {
        president_person_id,
        vice_president_person_id,
        secretary_general_person_id,
    }

    if len(selected_people) != 3:

        conn.close()

        return (
            "President, Vice President "
            "and Secretary General must "
            "be three different people.",
            400,
        )

    for person_id in selected_people:

        if not person_exists(
            cursor,
            person_id,
        ):
            conn.close()

            return (
                "One of the selected "
                "people does not exist.",
                404,
            )

    cursor.execute(
        """
        SELECT
            role_id,
            name
        FROM roles
        WHERE name IN (
            'PRESIDENT',
            'VICE_PRESIDENT',
            'SECRETARY_GENERAL'
        )
        """
    )

    executive_roles = {
        row["name"]:
            row["role_id"]

        for row
        in cursor.fetchall()
    }

    if (
        set(executive_roles)
        != EXECUTIVE_ROLES
    ):
        conn.close()

        return (
            "Required executive roles "
            "are not configured correctly.",
            500,
        )

    existing_election = (
        get_mandate_election(
            cursor,
            term_id,
        )
    )

    old_report_path = (
        existing_election[
            "report_path"
        ]
        if existing_election
        else None
    )

    new_report_path = None

    if (
        report_file is not None
        and report_file.filename
    ):
        try:
            new_report_path = (
                save_election_report_file(
                    report_file,
                    term_id,
                )
            )

        except (
            ValueError,
            OSError,
        ) as file_error:

            conn.close()

            return (
                str(file_error),
                400,
            )

    if new_report_path:

        report_path = (
            new_report_path
        )

    elif remove_report:

        report_path = None

    else:

        report_path = (
            old_report_path
        )

    old_holders = {
        "PRESIDENT":
            get_role_holder(
                cursor,
                term_id,
                "PRESIDENT",
            ),

        "VICE_PRESIDENT":
            get_role_holder(
                cursor,
                term_id,
                "VICE_PRESIDENT",
            ),

        "SECRETARY_GENERAL":
            get_role_holder(
                cursor,
                term_id,
                "SECRETARY_GENERAL",
            ),
    }

    requested_holders = {
        "PRESIDENT":
            president_person_id,

        "VICE_PRESIDENT":
            vice_president_person_id,

        "SECRETARY_GENERAL":
            secretary_general_person_id,
    }

    election_changed = (
        existing_election is None
        or existing_election[
            "election_date"
        ] != election_date
        or (
            existing_election[
                "notes"
            ]
            or ""
        ) != notes
        or old_report_path
        != report_path
        or any(
            old_holders[
                role_name
            ] is None

            or old_holders[
                role_name
            ][
                "person_id"
            ] != person_id

            for (
                role_name,
                person_id,
            )
            in requested_holders.items()
        )
    )

    if not election_changed:

        if new_report_path:
            delete_election_report_file(
                new_report_path
            )

        conn.close()

        return (
            _redirect_to_mandate(
                term_id
            )
        )

    try:
        conn.execute(
            "BEGIN IMMEDIATE"
        )

        executive_assignments = [
            (
                president_person_id,
                executive_roles[
                    "PRESIDENT"
                ],
            ),
            (
                vice_president_person_id,
                executive_roles[
                    "VICE_PRESIDENT"
                ],
            ),
            (
                secretary_general_person_id,
                executive_roles[
                    "SECRETARY_GENERAL"
                ],
            ),
        ]

        for (
            executive_person_id,
            executive_role_id,
        ) in executive_assignments:

            cursor.execute(
                """
                UPDATE memberships
                SET
                    role_id = ?,
                    department_id = NULL
                WHERE term_id = ?
                  AND person_id = ?
                """,
                (
                    executive_role_id,
                    term_id,
                    executive_person_id,
                ),
            )

            if cursor.rowcount == 0:

                cursor.execute(
                    """
                    INSERT INTO memberships (
                        person_id,
                        term_id,
                        role_id,
                        department_id
                    )
                    VALUES (?, ?, ?, NULL)
                    """,
                    (
                        executive_person_id,
                        term_id,
                        executive_role_id,
                    ),
                )

        cursor.execute(
            """
            SELECT
                memberships.membership_id,
                memberships.person_id,
                people.first_name,
                people.last_name

            FROM memberships

            JOIN roles
                ON memberships.role_id =
                   roles.role_id

            JOIN people
                ON memberships.person_id =
                   people.person_id

            WHERE memberships.term_id = ?

              AND roles.name IN (
                  'PRESIDENT',
                  'VICE_PRESIDENT',
                  'SECRETARY_GENERAL'
              )

              AND memberships.person_id
                  NOT IN (?, ?, ?)
            """,
            (
                term_id,
                president_person_id,
                vice_president_person_id,
                secretary_general_person_id,
            ),
        )

        for obsolete in (
            cursor.fetchall()
        ):
            try:
                cursor.execute(
                    """
                    DELETE FROM memberships
                    WHERE membership_id = ?
                    """,
                    (
                        obsolete[
                            "membership_id"
                        ],
                    ),
                )

            except sqlite3.IntegrityError as fk_error:

                raise ValueError(
                    "The previous executive "
                    "assignment for "
                    f"{obsolete['first_name']} "
                    f"{obsolete['last_name']} "
                    "is still referenced by "
                    "other draft data. Those "
                    "references must be cleaned "
                    "before changing the "
                    "election result."
                ) from fk_error

        if existing_election is None:

            cursor.execute(
                """
                INSERT INTO mandate_elections (
                    term_id,
                    election_date,
                    report_path,
                    notes,
                    recorded_by_user_id
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    term_id,
                    election_date,
                    report_path,
                    notes or None,
                    current_user[
                        "user_id"
                    ],
                ),
            )

            audit_action = (
                "ELECTION_RECORDED"
            )

        else:

            cursor.execute(
                """
                UPDATE mandate_elections
                SET
                    election_date = ?,
                    report_path = ?,
                    notes = ?,
                    updated_by_user_id = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE term_id = ?
                """,
                (
                    election_date,
                    report_path,
                    notes or None,
                    current_user[
                        "user_id"
                    ],
                    term_id,
                ),
            )

            audit_action = (
                "ELECTION_UPDATED"
            )

        reset_mandate_approvals(
            cursor=cursor,
            term_id=term_id,
            actor_user_id=(
                current_user[
                    "user_id"
                ]
            ),
            reason=(
                "Election result was "
                "created or modified."
            ),
            emergency_reason=(
                emergency_reason
            ),
        )

        log_mandate_action(
            cursor=cursor,
            term_id=term_id,
            actor_user_id=(
                current_user[
                    "user_id"
                ]
            ),
            action=audit_action,
            details=(
                "Official election result "
                "saved: "
                f"President person_id="
                f"{president_person_id}, "
                f"Vice President person_id="
                f"{vice_president_person_id}, "
                f"Secretary General person_id="
                f"{secretary_general_person_id}."
            ),
            emergency_reason=(
                emergency_reason
            ),
        )

        conn.commit()

    except Exception as error:

        conn.rollback()

        if new_report_path:
            delete_election_report_file(
                new_report_path
            )

        conn.close()

        return (
            "Election result could not "
            f"be saved: {error}",
            400,
        )

    if (
        old_report_path
        and old_report_path
        != report_path
    ):
        delete_election_report_file(
            old_report_path
        )

    conn.close()

    return _redirect_to_mandate(
        term_id
    )


@mandates_bp.route(
    "/mandates/<int:term_id>/memberships/save",
    methods=["POST"],
)
@login_required
def save_draft_membership(
    term_id,
):

    current_user = (
        get_current_user()
    )

    if not can_edit_draft_board(
        current_user
    ):
        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    term = get_draft_term(
        cursor,
        term_id,
    )

    if term is None:

        conn.close()

        return (
            "Draft mandate not found",
            404,
        )

    try:
        emergency_reason = (
            _emergency_reason(
                current_user,
                is_current_hr_head(
                    current_user
                ),
            )
        )

    except ValueError as reason_error:

        conn.close()

        return (
            str(reason_error),
            400,
        )

    person_id = request.form.get(
        "person_id",
        "",
    ).strip()

    role_id = request.form.get(
        "role_id",
        "",
    ).strip()

    department_id = (
        request.form.get(
            "department_id",
            "",
        ).strip()
    )

    if (
        not person_id
        or not role_id
    ):
        conn.close()

        return (
            "Person and role "
            "are required.",
            400,
        )

    try:
        person_id = int(
            person_id
        )

        role_id = int(
            role_id
        )

    except (
        TypeError,
        ValueError,
    ):
        conn.close()

        return (
            "Invalid person or role.",
            400,
        )

    if not person_exists(
        cursor,
        person_id,
    ):
        conn.close()

        return (
            "Person not found",
            404,
        )

    role = get_role(
        cursor,
        role_id,
    )

    if role is None:

        conn.close()

        return (
            "Invalid role",
            400,
        )

    role_name = (
        role["name"]
    )

    if (
        role_name
        not in BOARD_EDITABLE_ROLES
    ):
        conn.close()

        return (
            "President, Vice President "
            "and Secretary General are "
            "managed only through the "
            "Election Result step. "
            "Alumni are not managed in "
            "future mandate construction.",
            400,
        )

    if not department_id:

        conn.close()

        return (
            "This role requires "
            "a department.",
            400,
        )

    try:
        department_id = int(
            department_id
        )

    except (
        TypeError,
        ValueError,
    ):
        conn.close()

        return (
            "Invalid department.",
            400,
        )

    if not department_exists(
        cursor,
        department_id,
    ):
        conn.close()

        return (
            "Invalid department.",
            400,
        )

    cursor.execute(
        """
        SELECT
            memberships.membership_id,
            roles.name AS role_name
        FROM memberships
        JOIN roles
            ON memberships.role_id =
               roles.role_id
        WHERE memberships.term_id = ?
          AND memberships.person_id = ?
        LIMIT 1
        """,
        (
            term_id,
            person_id,
        ),
    )

    existing_membership = (
        cursor.fetchone()
    )

    if (
        existing_membership
        is not None
        and existing_membership[
            "role_name"
        ]
        in EXECUTIVE_ROLES
    ):
        conn.close()

        return (
            "This person holds an elected "
            "executive position. Change "
            "the Election Result instead "
            "of Board & Members.",
            400,
        )

    if (
        role_name == "HEAD"
        and department_id
        == HR_DEPARTMENT_ID
    ):
        cursor.execute(
            """
            SELECT
                memberships.membership_id

            FROM memberships

            JOIN roles
                ON memberships.role_id =
                   roles.role_id

            WHERE memberships.term_id = ?
              AND roles.name = 'HEAD'
              AND memberships.department_id = ?
              AND memberships.person_id != ?

            LIMIT 1
            """,
            (
                term_id,
                HR_DEPARTMENT_ID,
                person_id,
            ),
        )

        if (
            cursor.fetchone()
            is not None
        ):
            conn.close()

            return (
                "The Human Resources Head "
                "is already assigned.",
                400,
            )

    cursor.execute(
        """
        SELECT
            role_id,
            department_id
        FROM memberships
        WHERE term_id = ?
          AND person_id = ?
        LIMIT 1
        """,
        (
            term_id,
            person_id,
        ),
    )

    old_assignment = (
        cursor.fetchone()
    )

    unchanged = (
        old_assignment
        is not None
        and old_assignment[
            "role_id"
        ] == role_id
        and old_assignment[
            "department_id"
        ] == department_id
    )

    if unchanged:

        conn.close()

        return (
            _redirect_to_mandate(
                term_id
            )
        )

    try:
        cursor.execute(
            """
            INSERT INTO memberships (
                person_id,
                term_id,
                role_id,
                department_id
            )

            VALUES (?, ?, ?, ?)

            ON CONFLICT(
                person_id,
                term_id
            )

            DO UPDATE SET
                role_id =
                    excluded.role_id,
                department_id =
                    excluded.department_id
            """,
            (
                person_id,
                term_id,
                role_id,
                department_id,
            ),
        )

        reset_mandate_approvals(
            cursor=cursor,
            term_id=term_id,
            actor_user_id=(
                current_user[
                    "user_id"
                ]
            ),
            reason=(
                "Board or member "
                "assignment changed."
            ),
            emergency_reason=(
                emergency_reason
            ),
        )

        log_mandate_action(
            cursor=cursor,
            term_id=term_id,
            actor_user_id=(
                current_user[
                    "user_id"
                ]
            ),
            action=(
                "BOARD_ASSIGNMENT_SAVED"
            ),
            details=(
                f"person_id={person_id}, "
                f"role={role_name}, "
                f"department_id="
                f"{department_id}."
            ),
            emergency_reason=(
                emergency_reason
            ),
        )

        conn.commit()

    except sqlite3.IntegrityError as db_error:

        conn.rollback()
        conn.close()

        return (
            "Board assignment could not "
            f"be saved: {db_error}",
            400,
        )

    conn.close()

    return _redirect_to_mandate(
        term_id
    )


@mandates_bp.route(
    "/mandates/<int:term_id>/memberships/"
    "<int:membership_id>/delete",
    methods=["POST"],
)
@login_required
def delete_draft_membership(
    term_id,
    membership_id,
):

    current_user = (
        get_current_user()
    )

    if not can_edit_draft_board(
        current_user
    ):
        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    term = get_draft_term(
        cursor,
        term_id,
    )

    if term is None:

        conn.close()

        return (
            "Draft mandate not found",
            404,
        )

    try:
        emergency_reason = (
            _emergency_reason(
                current_user,
                is_current_hr_head(
                    current_user
                ),
            )
        )

    except ValueError as reason_error:

        conn.close()

        return (
            str(reason_error),
            400,
        )

    cursor.execute(
        """
        SELECT
            memberships.membership_id,
            memberships.person_id,
            people.first_name,
            people.last_name,
            roles.name AS role_name

        FROM memberships

        JOIN people
            ON memberships.person_id =
               people.person_id

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        WHERE memberships.membership_id = ?
          AND memberships.term_id = ?

        LIMIT 1
        """,
        (
            membership_id,
            term_id,
        ),
    )

    membership = (
        cursor.fetchone()
    )

    if membership is None:

        conn.close()

        return (
            "Membership not found",
            404,
        )

    if (
        membership["role_name"]
        in EXECUTIVE_ROLES
    ):
        conn.close()

        return (
            "Elected executive positions "
            "cannot be removed from "
            "Board & Members. Change the "
            "Election Result instead.",
            400,
        )

    try:
        cursor.execute(
            """
            DELETE FROM memberships
            WHERE membership_id = ?
              AND term_id = ?
            """,
            (
                membership_id,
                term_id,
            ),
        )

        reset_mandate_approvals(
            cursor=cursor,
            term_id=term_id,
            actor_user_id=(
                current_user[
                    "user_id"
                ]
            ),
            reason=(
                "A draft board/member "
                "assignment was removed."
            ),
            emergency_reason=(
                emergency_reason
            ),
        )

        log_mandate_action(
            cursor=cursor,
            term_id=term_id,
            actor_user_id=(
                current_user[
                    "user_id"
                ]
            ),
            action=(
                "BOARD_ASSIGNMENT_REMOVED"
            ),
            details=(
                f"Removed "
                f"{membership['first_name']} "
                f"{membership['last_name']} "
                f"({membership['role_name']})."
            ),
            emergency_reason=(
                emergency_reason
            ),
        )

        conn.commit()

    except sqlite3.IntegrityError:

        conn.rollback()
        conn.close()

        return (
            "This draft membership is "
            "already referenced by other "
            "CMS data and cannot be "
            "deleted safely.",
            400,
        )

    conn.close()

    return _redirect_to_mandate(
        term_id
    )


@mandates_bp.route(
    "/mandates/<int:term_id>/approve/<approval_type>",
    methods=["POST"],
)
@login_required
def approve_mandate(
    term_id,
    approval_type,
):

    approval_type = (
        approval_type.upper()
    )

    if approval_type not in {
        "PRESIDENT",
        "VICE_PRESIDENT",
    }:
        return (
            "Invalid approval type",
            400,
        )

    current_user = (
        get_current_user()
    )

    if approval_type == "PRESIDENT":

        permitted = (
            can_approve_as_president(
                current_user
            )
        )

        normal_permission = (
            is_current_president(
                current_user
            )
        )

    else:

        permitted = (
            can_approve_as_vice_president(
                current_user
            )
        )

        normal_permission = (
            is_current_vice_president(
                current_user
            )
        )

    if not permitted:

        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    term = get_draft_term(
        cursor,
        term_id,
    )

    if term is None:

        conn.close()

        return (
            "Draft mandate not found",
            404,
        )

    try:
        emergency_reason = (
            _emergency_reason(
                current_user,
                normal_permission,
            )
        )

    except ValueError as reason_error:

        conn.close()

        return (
            str(reason_error),
            400,
        )

    preapproval_errors = (
        get_mandate_validation_errors(
            cursor,
            term_id,
            include_approvals=False,
        )
    )

    if preapproval_errors:

        conn.close()

        return (
            "Mandate cannot be approved "
            "yet: "
            + " ".join(
                preapproval_errors
            ),
            400,
        )

    cursor.execute(
        """
        INSERT INTO mandate_approvals (
            term_id,
            approval_type,
            approved_by_user_id
        )

        VALUES (?, ?, ?)

        ON CONFLICT(
            term_id,
            approval_type
        )

        DO UPDATE SET
            approved_by_user_id =
                excluded.approved_by_user_id,

            approved_at =
                CURRENT_TIMESTAMP
        """,
        (
            term_id,
            approval_type,
            current_user[
                "user_id"
            ],
        ),
    )

    log_mandate_action(
        cursor=cursor,
        term_id=term_id,
        actor_user_id=(
            current_user[
                "user_id"
            ]
        ),
        action=(
            f"{approval_type}_APPROVED"
        ),
        details=(
            f"{approval_type.replace('_', ' ').title()} "
            "approval recorded."
        ),
        emergency_reason=(
            emergency_reason
        ),
    )

    conn.commit()
    conn.close()

    return _redirect_to_mandate(
        term_id
    )


@mandates_bp.route(
    "/mandates/<int:term_id>/approve/"
    "<approval_type>/revoke",
    methods=["POST"],
)
@login_required
def revoke_mandate_approval(
    term_id,
    approval_type,
):

    approval_type = (
        approval_type.upper()
    )

    if approval_type not in {
        "PRESIDENT",
        "VICE_PRESIDENT",
    }:
        return (
            "Invalid approval type",
            400,
        )

    current_user = (
        get_current_user()
    )

    if approval_type == "PRESIDENT":

        permitted = (
            can_approve_as_president(
                current_user
            )
        )

        normal_permission = (
            is_current_president(
                current_user
            )
        )

    else:

        permitted = (
            can_approve_as_vice_president(
                current_user
            )
        )

        normal_permission = (
            is_current_vice_president(
                current_user
            )
        )

    if not permitted:

        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    if (
        get_draft_term(
            cursor,
            term_id,
        )
        is None
    ):
        conn.close()

        return (
            "Draft mandate not found",
            404,
        )

    try:
        emergency_reason = (
            _emergency_reason(
                current_user,
                normal_permission,
            )
        )

    except ValueError as reason_error:

        conn.close()

        return (
            str(reason_error),
            400,
        )

    cursor.execute(
        """
        DELETE FROM mandate_approvals
        WHERE term_id = ?
          AND approval_type = ?
        """,
        (
            term_id,
            approval_type,
        ),
    )

    if cursor.rowcount:

        log_mandate_action(
            cursor=cursor,
            term_id=term_id,
            actor_user_id=(
                current_user[
                    "user_id"
                ]
            ),
            action=(
                f"{approval_type}_"
                "APPROVAL_REVOKED"
            ),
            details=(
                f"{approval_type.replace('_', ' ').title()} "
                "approval was revoked."
            ),
            emergency_reason=(
                emergency_reason
            ),
        )

    conn.commit()
    conn.close()

    return _redirect_to_mandate(
        term_id
    )


@mandates_bp.route(
    "/mandates/<int:term_id>/activate",
    methods=["POST"],
)
@login_required
def activate_mandate(
    term_id,
):

    current_user = (
        get_current_user()
    )

    if not can_activate_draft(
        current_user
    ):
        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    target_term = (
        get_draft_term(
            cursor,
            term_id,
        )
    )

    if target_term is None:

        conn.close()

        return (
            "Draft mandate not found",
            404,
        )

    try:
        emergency_reason = (
            _emergency_reason(
                current_user,
                is_current_president(
                    current_user
                ),
            )
        )

    except ValueError as reason_error:

        conn.close()

        return (
            str(reason_error),
            400,
        )

    validation_errors = (
        get_mandate_validation_errors(
            cursor,
            term_id,
            include_approvals=True,
        )
    )

    if validation_errors:

        conn.close()

        return (
            "Mandate cannot be "
            "activated: "
            + " ".join(
                validation_errors
            ),
            400,
        )

    try:
        conn.execute(
            "BEGIN IMMEDIATE"
        )

        if (
            get_draft_term(
                cursor,
                term_id,
            )
            is None
        ):
            raise ValueError(
                "The target mandate is "
                "no longer DRAFT."
            )

        validation_errors = (
            get_mandate_validation_errors(
                cursor,
                term_id,
                include_approvals=True,
            )
        )

        if validation_errors:

            raise ValueError(
                " ".join(
                    validation_errors
                )
            )

        cursor.execute(
            """
            UPDATE terms
            SET status = 'ARCHIVED'
            WHERE status = 'ACTIVE'
            """
        )

        cursor.execute(
            """
            UPDATE terms
            SET status = 'ACTIVE'
            WHERE term_id = ?
              AND status = 'DRAFT'
            """,
            (term_id,),
        )

        if cursor.rowcount != 1:

            raise ValueError(
                "The mandate could not "
                "be activated."
            )

        log_mandate_action(
            cursor=cursor,
            term_id=term_id,
            actor_user_id=(
                current_user[
                    "user_id"
                ]
            ),
            action=(
                "MANDATE_ACTIVATED"
            ),
            details=(
                "Draft mandate activated "
                "and the previous active "
                "mandate archived."
            ),
            emergency_reason=(
                emergency_reason
            ),
        )

        conn.commit()

    except Exception as error:

        conn.rollback()
        conn.close()

        return (
            "Mandate activation failed: "
            f"{error}",
            400,
        )

    conn.close()

    return _redirect_to_mandate(
        term_id
    )


@mandates_bp.route(
    "/mandates/<int:term_id>/delete",
    methods=["POST"],
)
@login_required
def delete_draft(
    term_id,
):

    current_user = (
        get_current_user()
    )

    if not can_delete_draft(
        current_user
    ):
        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    term = get_draft_term(
        cursor,
        term_id,
    )

    if term is None:

        conn.close()

        return (
            "Draft mandate not found",
            404,
        )

    confirmation = (
        request.form.get(
            "confirmation",
            "",
        ).strip()
    )

    if confirmation != term["name"]:

        conn.close()

        return (
            "Type the exact mandate "
            "name to confirm deletion.",
            400,
        )

    try:
        emergency_reason = (
            _emergency_reason(
                current_user,
                is_current_president(
                    current_user
                ),
            )
        )

    except ValueError as reason_error:

        conn.close()

        return (
            str(reason_error),
            400,
        )

    election = (
        get_mandate_election(
            cursor,
            term_id,
        )
    )

    report_path = (
        election["report_path"]
        if election
        else None
    )

    try:
        conn.execute(
            "BEGIN IMMEDIATE"
        )

        log_mandate_action(
            cursor=cursor,
            term_id=term_id,
            actor_user_id=(
                current_user[
                    "user_id"
                ]
            ),
            action="DRAFT_DELETED",
            details=(
                "Draft mandate deleted "
                "before activation."
            ),
            emergency_reason=(
                emergency_reason
            ),
        )

        cursor.execute(
            """
            DELETE FROM memberships
            WHERE term_id = ?
            """,
            (term_id,),
        )

        cursor.execute(
            """
            DELETE FROM terms
            WHERE term_id = ?
              AND status = 'DRAFT'
            """,
            (term_id,),
        )

        if cursor.rowcount != 1:

            raise ValueError(
                "Draft mandate could "
                "not be deleted."
            )

        conn.commit()

    except sqlite3.IntegrityError:

        conn.rollback()
        conn.close()

        return (
            "This draft already contains "
            "CMS data that references its "
            "memberships or term. Delete "
            "or move those draft records "
            "before deleting the mandate.",
            400,
        )

    except Exception as error:

        conn.rollback()
        conn.close()

        return (
            "Draft deletion failed: "
            f"{error}",
            400,
        )

    if report_path:

        delete_election_report_file(
            report_path
        )

    conn.close()

    return redirect(
        url_for(
            "mandates.mandates"
        )
    )