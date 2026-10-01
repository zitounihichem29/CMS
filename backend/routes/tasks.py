from datetime import date
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
)
from werkzeug.utils import secure_filename

from context import get_active_term_id
from database import get_db_connection
from permissions import current_member_required, login_required, role_required
from routes.notifications import create_notification


tasks_bp = Blueprint("tasks", __name__)


TASK_CREATOR_ROLES = (
    "HEAD",
    "SUB_HEAD",
    "PRESIDENT",
    "VICE_PRESIDENT",
)

PRESIDENCY_ROLES = (
    "PRESIDENT",
    "VICE_PRESIDENT",
)

ALLOWED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "ppt",
    "pptx",
    "txt",
    "jpg",
    "jpeg",
    "png",
    "gif",
    "webp",
    "mp4",
    "mov",
    "avi",
    "mkv",
    "webm",
}


# ============================================================
# PROTECT TASKS MODULE
# CURRENT MEMBERS ONLY
# ============================================================

@tasks_bp.before_request
@current_member_required
def protect_tasks_module():
    pass


# ============================================================
# HELPERS
# ============================================================

def update_pending_reviews(conn, active_term_id):
    """
    Move overdue tasks from the ACTIVE mandate to pending review.

    Archived mandates are never modified here.
    """

    today = date.today().isoformat()

    conn.execute(
        """
        UPDATE tasks

        SET review_status = 'pending_review'

        WHERE due_date IS NOT NULL
          AND due_date < ?
          AND review_status = 'not_reviewed'

          AND task_id IN (

                SELECT tasks.task_id

                FROM tasks

                JOIN memberships AS creator_membership
                    ON tasks.assigned_by_membership_id =
                       creator_membership.membership_id

                WHERE creator_membership.term_id = ?
          )
        """,
        (
            today,
            active_term_id,
        ),
    )

    conn.commit()


def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ============================================================
# CURRENT MEMBERSHIP
# ============================================================

def get_current_membership(cursor):
    """
    Logged-in user's membership for ACTIVE mandate only.
    """

    active_term_id = get_active_term_id()

    if active_term_id is None:
        return None

    cursor.execute(
        """
        SELECT
            memberships.membership_id,
            memberships.term_id,
            memberships.department_id,

            roles.name AS role_name

        FROM users

        JOIN memberships
            ON users.person_id =
               memberships.person_id

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        WHERE users.user_id = ?
          AND memberships.term_id = ?

        LIMIT 1
        """,
        (
            session["user_id"],
            active_term_id,
        ),
    )

    return cursor.fetchone()


# ============================================================
# TASK ASSIGNMENT
# ============================================================

def get_task_assignment(
    cursor,
    task_id,
    membership_id,
):

    cursor.execute(
        """
        SELECT
            task_assignee_id

        FROM task_assignees

        WHERE task_id = ?
          AND membership_id = ?
        """,
        (
            task_id,
            membership_id,
        ),
    )

    return cursor.fetchone()


# ============================================================
# MANAGE TASK PERMISSION
# ============================================================

def can_manage_task(
    current_role,
    current_membership_id,
    current_department_id,
    task_creator_membership_id,
    task_department_id,
):

    # HEAD / SUB_HEAD:
    # manage tasks created in their department.

    if current_role in (
        "HEAD",
        "SUB_HEAD",
    ):

        return (
            current_department_id
            == task_department_id
        )

    # PRESIDENT / VP:
    # manage only tasks they personally created.

    if current_role in PRESIDENCY_ROLES:

        return (
            current_membership_id
            == task_creator_membership_id
        )

    return False


# ============================================================
# VIEW TASK PERMISSION
# ============================================================

def can_view_task(
    current_role,
    is_assigned,
    current_membership_id,
    current_department_id,
    task_creator_membership_id,
    task_department_id,
):

    # MEMBER:
    # only assigned tasks.

    if current_role == "MEMBER":

        return is_assigned

    # HEAD / SUB_HEAD / PRESIDENT / VP

    return can_manage_task(
        current_role=current_role,
        current_membership_id=(
            current_membership_id
        ),
        current_department_id=(
            current_department_id
        ),
        task_creator_membership_id=(
            task_creator_membership_id
        ),
        task_department_id=(
            task_department_id
        ),
    )


# ============================================================
# ASSIGNABLE MEMBERS
# ============================================================

def get_assignable_members(
    cursor,
    current_role,
    current_department_id,
    active_term_id,
):

    # ========================================================
    # HEAD / SUB_HEAD
    # ========================================================

    if current_role in (
        "HEAD",
        "SUB_HEAD",
    ):

        cursor.execute(
            """
            SELECT
                memberships.membership_id,

                people.first_name,
                people.last_name

            FROM memberships

            JOIN people
                ON memberships.person_id =
                   people.person_id

            JOIN users
                ON people.person_id =
                   users.person_id

            JOIN roles
                ON memberships.role_id =
                   roles.role_id

            WHERE memberships.term_id = ?
              AND memberships.department_id = ?
              AND users.is_active = 1

              AND roles.name NOT IN (
                    'PRESIDENT',
                    'VICE_PRESIDENT'
              )

            ORDER BY
                people.last_name,
                people.first_name
            """,
            (
                active_term_id,
                current_department_id,
            ),
        )

    # ========================================================
    # PRESIDENT / VICE PRESIDENT
    # ========================================================

    elif current_role in PRESIDENCY_ROLES:

        cursor.execute(
            """
            SELECT
                memberships.membership_id,

                people.first_name,
                people.last_name

            FROM memberships

            JOIN people
                ON memberships.person_id =
                   people.person_id

            JOIN users
                ON people.person_id =
                   users.person_id

            JOIN roles
                ON memberships.role_id =
                   roles.role_id

            WHERE memberships.term_id = ?
              AND users.is_active = 1

              AND roles.name NOT IN (
                    'PRESIDENT',
                    'VICE_PRESIDENT'
              )

            ORDER BY
                people.last_name,
                people.first_name
            """,
            (
                active_term_id,
            ),
        )

    else:

        return []

    return cursor.fetchall()


# ============================================================
# VERIFY ASSIGNEE
# ============================================================

def verify_assignee(
    cursor,
    membership_id,
    current_role,
    current_department_id,
    active_term_id,
):

    cursor.execute(
        """
        SELECT
            memberships.membership_id,
            memberships.department_id,

            roles.name AS role_name

        FROM memberships

        JOIN users
            ON memberships.person_id =
               users.person_id

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        WHERE memberships.membership_id = ?
          AND memberships.term_id = ?
          AND users.is_active = 1
        """,
        (
            membership_id,
            active_term_id,
        ),
    )

    member = cursor.fetchone()

    if member is None:

        return (
            False,
            "Invalid or inactive member",
        )

    # President and VP cannot receive tasks.

    if member["role_name"] in PRESIDENCY_ROLES:

        return (
            False,
            "President and Vice-President cannot receive tasks",
        )

    # HEAD / SUB_HEAD:
    # own department only.

    if current_role in (
        "HEAD",
        "SUB_HEAD",
    ):

        if (
            member["department_id"]
            != current_department_id
        ):

            return (
                False,
                "You cannot assign a task outside your department",
            )

    # PRESIDENT / VP:
    # can assign throughout the club.

    elif current_role not in PRESIDENCY_ROLES:

        return (
            False,
            "Access denied",
        )

    return True, None


# ============================================================
# TASK FOR ACCESS CHECK
# ============================================================

def get_task_for_access_check(
    cursor,
    task_id,
    active_term_id,
):

    cursor.execute(
        """
        SELECT
            tasks.task_id,
            tasks.review_status,
            tasks.assigned_by_membership_id,

            creator_membership.department_id
                AS department_id

        FROM tasks

        JOIN memberships AS creator_membership
            ON tasks.assigned_by_membership_id =
               creator_membership.membership_id

        WHERE tasks.task_id = ?
          AND creator_membership.term_id = ?
        """,
        (
            task_id,
            active_term_id,
        ),
    )

    return cursor.fetchone()


# ============================================================
# TASKS LIST
# ============================================================

@tasks_bp.route("/tasks")
@login_required
def tasks():

    status_filter = request.args.get(
        "status",
        "all",
    )

    if status_filter not in {
        "all",
        "pending",
        "in_progress",
        "completed",
    }:

        status_filter = "all"

    conn = get_db_connection()
    cursor = conn.cursor()

    current_membership = (
        get_current_membership(
            cursor
        )
    )

    if current_membership is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    current_membership_id = (
        current_membership[
            "membership_id"
        ]
    )

    active_term_id = (
        current_membership[
            "term_id"
        ]
    )

    current_department_id = (
        current_membership[
            "department_id"
        ]
    )

    current_role = (
        current_membership[
            "role_name"
        ]
    )

    update_pending_reviews(
        conn,
        active_term_id,
    )

    # ========================================================
    # MEMBER
    # ========================================================

    if current_role == "MEMBER":

        cursor.execute(
            """
            SELECT DISTINCT

                tasks.task_id,
                tasks.title,
                tasks.description,
                tasks.due_date,
                tasks.status,
                tasks.review_status,
                tasks.created_at,

                creator_people.first_name
                    AS creator_first_name,

                creator_people.last_name
                    AS creator_last_name

            FROM tasks

            JOIN task_assignees
                ON tasks.task_id =
                   task_assignees.task_id

            JOIN memberships AS creator_membership
                ON tasks.assigned_by_membership_id =
                   creator_membership.membership_id

            JOIN people AS creator_people
                ON creator_membership.person_id =
                   creator_people.person_id

            WHERE task_assignees.membership_id = ?
              AND creator_membership.term_id = ?

              AND (
                    ? = 'all'
                    OR tasks.status = ?
              )

            ORDER BY

                CASE

                    WHEN tasks.due_date IS NULL
                    THEN 1

                    ELSE 0

                END,

                tasks.due_date ASC,
                tasks.created_at DESC
            """,
            (
                current_membership_id,
                active_term_id,
                status_filter,
                status_filter,
            ),
        )

    # ========================================================
    # HEAD / SUB_HEAD
    # ========================================================

    elif current_role in (
        "HEAD",
        "SUB_HEAD",
    ):

        cursor.execute(
            """
            SELECT DISTINCT

                tasks.task_id,
                tasks.title,
                tasks.description,
                tasks.due_date,
                tasks.status,
                tasks.review_status,
                tasks.created_at,

                creator_people.first_name
                    AS creator_first_name,

                creator_people.last_name
                    AS creator_last_name

            FROM tasks

            JOIN memberships AS creator_membership
                ON tasks.assigned_by_membership_id =
                   creator_membership.membership_id

            JOIN people AS creator_people
                ON creator_membership.person_id =
                   creator_people.person_id

            WHERE creator_membership.term_id = ?
              AND creator_membership.department_id = ?

              AND (
                    ? = 'all'
                    OR tasks.status = ?
              )

            ORDER BY

                CASE

                    WHEN tasks.due_date IS NULL
                    THEN 1

                    ELSE 0

                END,

                tasks.due_date ASC,
                tasks.created_at DESC
            """,
            (
                active_term_id,
                current_department_id,
                status_filter,
                status_filter,
            ),
        )

    # ========================================================
    # PRESIDENT / VICE PRESIDENT
    # ========================================================

    elif current_role in PRESIDENCY_ROLES:

        cursor.execute(
            """
            SELECT DISTINCT

                tasks.task_id,
                tasks.title,
                tasks.description,
                tasks.due_date,
                tasks.status,
                tasks.review_status,
                tasks.created_at,

                creator_people.first_name
                    AS creator_first_name,

                creator_people.last_name
                    AS creator_last_name

            FROM tasks

            JOIN memberships AS creator_membership
                ON tasks.assigned_by_membership_id =
                   creator_membership.membership_id

            JOIN people AS creator_people
                ON creator_membership.person_id =
                   creator_people.person_id

            WHERE tasks.assigned_by_membership_id = ?
              AND creator_membership.term_id = ?

              AND (
                    ? = 'all'
                    OR tasks.status = ?
              )

            ORDER BY

                CASE

                    WHEN tasks.due_date IS NULL
                    THEN 1

                    ELSE 0

                END,

                tasks.due_date ASC,
                tasks.created_at DESC
            """,
            (
                current_membership_id,
                active_term_id,
                status_filter,
                status_filter,
            ),
        )

    else:

        conn.close()

        return (
            "Access denied",
            403,
        )

    task_rows = cursor.fetchall()

    # ========================================================
    # SUMMARY COUNTS
    # ========================================================

    # ========================================================
    # MEMBER
    # ========================================================

    if current_role == "MEMBER":

        cursor.execute(
            """
            SELECT

                COUNT(
                    DISTINCT tasks.task_id
                ) AS all_count,

                COUNT(
                    DISTINCT CASE

                        WHEN tasks.status = 'pending'
                        THEN tasks.task_id

                    END
                ) AS pending_count,

                COUNT(
                    DISTINCT CASE

                        WHEN tasks.status = 'in_progress'
                        THEN tasks.task_id

                    END
                ) AS in_progress_count,

                COUNT(
                    DISTINCT CASE

                        WHEN tasks.status = 'completed'
                        THEN tasks.task_id

                    END
                ) AS completed_count

            FROM tasks

            JOIN task_assignees
                ON tasks.task_id =
                   task_assignees.task_id

            JOIN memberships AS creator_membership
                ON tasks.assigned_by_membership_id =
                   creator_membership.membership_id

            WHERE task_assignees.membership_id = ?
              AND creator_membership.term_id = ?
            """,
            (
                current_membership_id,
                active_term_id,
            ),
        )

    # ========================================================
    # HEAD / SUB_HEAD
    # ========================================================

    elif current_role in (
        "HEAD",
        "SUB_HEAD",
    ):

        cursor.execute(
            """
            SELECT

                COUNT(
                    DISTINCT tasks.task_id
                ) AS all_count,

                COUNT(
                    DISTINCT CASE

                        WHEN tasks.status = 'pending'
                        THEN tasks.task_id

                    END
                ) AS pending_count,

                COUNT(
                    DISTINCT CASE

                        WHEN tasks.status = 'in_progress'
                        THEN tasks.task_id

                    END
                ) AS in_progress_count,

                COUNT(
                    DISTINCT CASE

                        WHEN tasks.status = 'completed'
                        THEN tasks.task_id

                    END
                ) AS completed_count

            FROM tasks

            JOIN memberships AS creator_membership
                ON tasks.assigned_by_membership_id =
                   creator_membership.membership_id

            WHERE creator_membership.term_id = ?
              AND creator_membership.department_id = ?
            """,
            (
                active_term_id,
                current_department_id,
            ),
        )

    # ========================================================
    # PRESIDENT / VP
    # ========================================================

    else:

        cursor.execute(
            """
            SELECT

                COUNT(
                    DISTINCT tasks.task_id
                ) AS all_count,

                COUNT(
                    DISTINCT CASE

                        WHEN tasks.status = 'pending'
                        THEN tasks.task_id

                    END
                ) AS pending_count,

                COUNT(
                    DISTINCT CASE

                        WHEN tasks.status = 'in_progress'
                        THEN tasks.task_id

                    END
                ) AS in_progress_count,

                COUNT(
                    DISTINCT CASE

                        WHEN tasks.status = 'completed'
                        THEN tasks.task_id

                    END
                ) AS completed_count

            FROM tasks

            JOIN memberships AS creator_membership
                ON tasks.assigned_by_membership_id =
                   creator_membership.membership_id

            WHERE tasks.assigned_by_membership_id = ?
              AND creator_membership.term_id = ?
            """,
            (
                current_membership_id,
                active_term_id,
            ),
        )

    counts = cursor.fetchone()

    all_tasks_count = (
        counts["all_count"]
        or 0
    )

    pending_count = (
        counts["pending_count"]
        or 0
    )

    in_progress_count = (
        counts["in_progress_count"]
        or 0
    )

    completed_count = (
        counts["completed_count"]
        or 0
    )

    # ========================================================
    # ASSIGNEES FOR EACH TASK
    # ========================================================

    task_assignees = {}
    task_assignee_ids = {}

    for task in task_rows:

        cursor.execute(
            """
            SELECT

                people.first_name,
                people.last_name

            FROM task_assignees

            JOIN memberships
                ON task_assignees.membership_id =
                   memberships.membership_id

            JOIN people
                ON memberships.person_id =
                   people.person_id

            WHERE task_assignees.task_id = ?
              AND memberships.term_id = ?

            ORDER BY
                people.last_name,
                people.first_name
            """,
            (
                task["task_id"],
                active_term_id,
            ),
        )

        task_assignees[
            task["task_id"]
        ] = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                task_assignees.membership_id

            FROM task_assignees

            JOIN memberships
                ON task_assignees.membership_id =
                   memberships.membership_id

            WHERE task_assignees.task_id = ?
              AND memberships.term_id = ?
            """,
            (
                task["task_id"],
                active_term_id,
            ),
        )

        task_assignee_ids[
            task["task_id"]
        ] = [

            row["membership_id"]

            for row in cursor.fetchall()
        ]

    conn.close()

    return render_template(
        "tasks.html",

        tasks=task_rows,

        all_tasks_count=(
            all_tasks_count
        ),

        pending_count=(
            pending_count
        ),

        in_progress_count=(
            in_progress_count
        ),

        completed_count=(
            completed_count
        ),

        task_assignees=(
            task_assignees
        ),

        task_assignee_ids=(
            task_assignee_ids
        ),

        current_role=(
            current_role
        ),

        current_membership_id=(
            current_membership_id
        ),

        can_create_task=(
            current_role
            in TASK_CREATOR_ROLES
        ),
    )


# ============================================================
# NEW TASK
# ============================================================

@tasks_bp.route(
    "/tasks/new",
    methods=[
        "GET",
        "POST",
    ],
)
@role_required(
    "HEAD",
    "SUB_HEAD",
    "PRESIDENT",
    "VICE_PRESIDENT",
)
def new_task():

    conn = get_db_connection()
    cursor = conn.cursor()

    current_membership = (
        get_current_membership(
            cursor
        )
    )

    if current_membership is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    current_membership_id = (
        current_membership[
            "membership_id"
        ]
    )

    active_term_id = (
        current_membership[
            "term_id"
        ]
    )

    current_department_id = (
        current_membership[
            "department_id"
        ]
    )

    current_role = (
        current_membership[
            "role_name"
        ]
    )

    # ========================================================
    # ASSIGNABLE MEMBERS
    # ========================================================

    assignable_members = (
        get_assignable_members(
            cursor,
            current_role,
            current_department_id,
            active_term_id,
        )
    )

    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        title = request.form.get(
            "title",
            "",
        ).strip()

        description = request.form.get(
            "description",
            "",
        ).strip()

        due_date = request.form.get(
            "due_date",
            "",
        ).strip()

        selected_members = (
            request.form.getlist(
                "assignees"
            )
        )

        # ====================================================
        # TITLE
        # ====================================================

        if not title:

            conn.close()

            return (
                "Task title is required",
                400,
            )

        # ====================================================
        # ASSIGNEES
        # ====================================================

        if not selected_members:

            conn.close()

            return (
                "Please select at least one member",
                400,
            )

        selected_members = list(
            dict.fromkeys(
                selected_members
            )
        )

        # ====================================================
        # VERIFY ASSIGNEES
        # ====================================================

        for membership_id in selected_members:

            valid, error_message = (
                verify_assignee(
                    cursor=cursor,

                    membership_id=(
                        membership_id
                    ),

                    current_role=(
                        current_role
                    ),

                    current_department_id=(
                        current_department_id
                    ),

                    active_term_id=(
                        active_term_id
                    ),
                )
            )

            if not valid:

                conn.close()

                return (
                    error_message,
                    403,
                )

        # ====================================================
        # CREATE TASK
        # ====================================================

        cursor.execute(
            """
            INSERT INTO tasks (

                assigned_by_membership_id,

                title,

                description,

                due_date
            )

            VALUES (
                ?,
                ?,
                ?,
                ?
            )
            """,
            (
                current_membership_id,

                title,

                description,

                due_date
                if due_date
                else None,
            ),
        )

        task_id = cursor.lastrowid

        # ====================================================
        # ADD ASSIGNEES
        # ====================================================

        for membership_id in selected_members:

            cursor.execute(
                """
                INSERT INTO task_assignees (

                    task_id,

                    membership_id
                )

                VALUES (
                    ?,
                    ?
                )
                """,
                (
                    task_id,

                    membership_id,
                ),
            )

            # =================================================
            # USER ACCOUNT
            # =================================================

            cursor.execute(
                """
                SELECT
                    users.user_id

                FROM memberships

                JOIN users
                    ON memberships.person_id =
                       users.person_id

                WHERE memberships.membership_id = ?
                  AND memberships.term_id = ?
                  AND users.is_active = 1

                LIMIT 1
                """,
                (
                    membership_id,
                    active_term_id,
                ),
            )

            recipient_user = (
                cursor.fetchone()
            )

            # =================================================
            # NOTIFICATION
            # =================================================

            if recipient_user is not None:

                create_notification(

                    recipient_user_id=(
                        recipient_user[
                            "user_id"
                        ]
                    ),

                    notification_type=(
                        "task"
                    ),

                    title=(
                        "New task assigned"
                    ),

                    message=(
                        f'You have been assigned '
                        f'to "{title}".'
                    ),

                    target_url=(
                        f"/tasks/{task_id}"
                    ),

                    conn=conn,
                )

        conn.commit()

        conn.close()

        return redirect(
            "/tasks"
        )

    # ========================================================
    # GET
    # ========================================================

    conn.close()

    return render_template(
        "new_task.html",

        assignable_members=(
            assignable_members
        ),

        current_role=(
            current_role
        ),
    )


# ============================================================
# UPDATE TASK STATUS
# ============================================================

@tasks_bp.route(
    "/tasks/<int:task_id>/status",
    methods=["POST"],
)
@login_required
def update_task_status(task_id):

    new_status = request.form.get(
        "status",
        "",
    )

    allowed_statuses = [
        "pending",
        "in_progress",
        "completed",
    ]

    if new_status not in allowed_statuses:

        return (
            "Invalid status",
            400,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    current_membership = (
        get_current_membership(
            cursor
        )
    )

    if current_membership is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    current_membership_id = (
        current_membership[
            "membership_id"
        ]
    )

    active_term_id = (
        current_membership[
            "term_id"
        ]
    )

    update_pending_reviews(
        conn,
        active_term_id,
    )

    # ========================================================
    # TASK
    # ========================================================

    cursor.execute(
        """
        SELECT
            tasks.review_status

        FROM tasks

        JOIN memberships AS creator_membership
            ON tasks.assigned_by_membership_id =
               creator_membership.membership_id

        WHERE tasks.task_id = ?
          AND creator_membership.term_id = ?
        """,
        (
            task_id,
            active_term_id,
        ),
    )

    task = cursor.fetchone()

    if task is None:

        conn.close()

        return (
            "Task not found",
            404,
        )

    # Task locked after review starts.

    if (
        task["review_status"]
        != "not_reviewed"
    ):

        conn.close()

        return (
            "This task is locked for review",
            403,
        )

    # ========================================================
    # CHECK ASSIGNMENT
    # ========================================================

    assignment = (
        get_task_assignment(
            cursor,
            task_id,
            current_membership_id,
        )
    )

    if assignment is None:

        conn.close()

        return (
            "You are not assigned to this task",
            403,
        )

    # ========================================================
    # UPDATE STATUS
    # ========================================================

    cursor.execute(
        """
        UPDATE tasks

        SET status = ?

        WHERE task_id = ?

          AND task_id IN (

                SELECT tasks.task_id

                FROM tasks

                JOIN memberships AS creator_membership
                    ON tasks.assigned_by_membership_id =
                       creator_membership.membership_id

                WHERE creator_membership.term_id = ?
          )
        """,
        (
            new_status,
            task_id,
            active_term_id,
        ),
    )

    conn.commit()

    conn.close()

    return redirect(
        "/tasks"
    )


# ============================================================
# TASK DETAIL
# ============================================================

@tasks_bp.route(
    "/tasks/<int:task_id>"
)
@login_required
def task_detail(task_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_membership = (
        get_current_membership(
            cursor
        )
    )

    if current_membership is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    current_membership_id = (
        current_membership[
            "membership_id"
        ]
    )

    active_term_id = (
        current_membership[
            "term_id"
        ]
    )

    current_department_id = (
        current_membership[
            "department_id"
        ]
    )

    current_role = (
        current_membership[
            "role_name"
        ]
    )

    update_pending_reviews(
        conn,
        active_term_id,
    )

    # ========================================================
    # TASK INFORMATION
    # ========================================================

    cursor.execute(
        """
        SELECT

            tasks.task_id,

            tasks.title,

            tasks.description,

            tasks.due_date,

            tasks.status,

            tasks.review_status,

            tasks.reviewed_at,

            tasks.created_at,

            tasks.assigned_by_membership_id,

            creator_membership.department_id
                AS department_id,

            creator_people.first_name
                AS creator_first_name,

            creator_people.last_name
                AS creator_last_name

        FROM tasks

        JOIN memberships AS creator_membership

            ON tasks.assigned_by_membership_id =
               creator_membership.membership_id

        JOIN people AS creator_people

            ON creator_membership.person_id =
               creator_people.person_id

        WHERE tasks.task_id = ?
          AND creator_membership.term_id = ?
        """,
        (
            task_id,
            active_term_id,
        ),
    )

    task = cursor.fetchone()

    if task is None:

        conn.close()

        return (
            "Task not found",
            404,
        )

    # ========================================================
    # CURRENT USER ASSIGNED?
    # ========================================================

    assignment = (
        get_task_assignment(
            cursor,

            task_id,

            current_membership_id,
        )
    )

    is_assigned = (
        assignment is not None
    )

    # ========================================================
    # VIEW PERMISSION
    # ========================================================

    allowed_to_view = (
        can_view_task(

            current_role=(
                current_role
            ),

            is_assigned=(
                is_assigned
            ),

            current_membership_id=(
                current_membership_id
            ),

            current_department_id=(
                current_department_id
            ),

            task_creator_membership_id=(
                task[
                    "assigned_by_membership_id"
                ]
            ),

            task_department_id=(
                task[
                    "department_id"
                ]
            ),
        )
    )

    if not allowed_to_view:

        conn.close()

        return (
            "Access denied",
            403,
        )

    # ========================================================
    # UPLOAD PERMISSION
    # ========================================================

    can_upload_attachment = (
        is_assigned
    )

    # ========================================================
    # ASSIGNEES
    # ========================================================

    cursor.execute(
        """
        SELECT

            memberships.membership_id,

            people.first_name,

            people.last_name

        FROM task_assignees

        JOIN memberships

            ON task_assignees.membership_id =
               memberships.membership_id

        JOIN people

            ON memberships.person_id =
               people.person_id

        WHERE task_assignees.task_id = ?
          AND memberships.term_id = ?

        ORDER BY
            people.last_name,
            people.first_name
        """,
        (
            task_id,
            active_term_id,
        ),
    )

    assignees = cursor.fetchall()

    # ========================================================
    # ATTACHMENTS
    # ========================================================

    cursor.execute(
        """
        SELECT

            task_attachments.task_attachment_id,

            task_attachments.original_filename,

            task_attachments.mime_type,

            task_attachments.file_size,

            task_attachments.uploaded_at,

            people.first_name
                AS uploader_first_name,

            people.last_name
                AS uploader_last_name

        FROM task_attachments

        JOIN memberships

            ON task_attachments.uploaded_by_membership_id =
               memberships.membership_id

        JOIN people

            ON memberships.person_id =
               people.person_id

        WHERE task_attachments.task_id = ?
          AND memberships.term_id = ?

        ORDER BY
            task_attachments.uploaded_at DESC
        """,
        (
            task_id,
            active_term_id,
        ),
    )

    attachments = cursor.fetchall()

    # ========================================================
    # MANAGEMENT PERMISSION
    # ========================================================

    can_manage_current_task = (
        can_manage_task(

            current_role=(
                current_role
            ),

            current_membership_id=(
                current_membership_id
            ),

            current_department_id=(
                current_department_id
            ),

            task_creator_membership_id=(
                task[
                    "assigned_by_membership_id"
                ]
            ),

            task_department_id=(
                task[
                    "department_id"
                ]
            ),
        )
    )

    conn.close()

    return render_template(
        "task_detail.html",

        task=task,

        assignees=assignees,

        can_upload_attachment=(
            can_upload_attachment
        ),

        attachments=attachments,

        current_role=(
            current_role
        ),

        can_manage_task=(
            can_manage_current_task
        ),
    )


# ============================================================
# UPLOAD TASK ATTACHMENT
# ============================================================

@tasks_bp.route(
    "/tasks/<int:task_id>/attachments",
    methods=["POST"],
)
@login_required
def upload_task_attachment(task_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_membership = (
        get_current_membership(
            cursor
        )
    )

    if current_membership is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    current_membership_id = (
        current_membership[
            "membership_id"
        ]
    )

    active_term_id = (
        current_membership[
            "term_id"
        ]
    )

    update_pending_reviews(
        conn,
        active_term_id,
    )

    # ========================================================
    # TASK
    # ========================================================

    task = (
        get_task_for_access_check(
            cursor,
            task_id,
            active_term_id,
        )
    )

    if task is None:

        conn.close()

        return (
            "Task not found",
            404,
        )

    # ========================================================
    # LOCK
    # ========================================================

    if (
        task["review_status"]
        != "not_reviewed"
    ):

        conn.close()

        return (
            "This task is locked for review",
            403,
        )

    # ========================================================
    # CHECK ASSIGNMENT
    # ========================================================

    assignment = (
        get_task_assignment(
            cursor,

            task_id,

            current_membership_id,
        )
    )

    if assignment is None:

        conn.close()

        return (
            "You are not assigned to this task",
            403,
        )

    # ========================================================
    # FILE
    # ========================================================

    file = request.files.get(
        "attachment"
    )

    if (
        file is None
        or file.filename == ""
    ):

        conn.close()

        return (
            "No file selected",
            400,
        )

    if not allowed_file(
        file.filename
    ):

        conn.close()

        return (
            "File type not allowed",
            400,
        )

    original_filename = (
        secure_filename(
            file.filename
        )
    )

    extension = (
        os.path.splitext(
            original_filename
        )[1]
    )

    stored_filename = (
        uuid.uuid4().hex
        + extension
    )

    save_path = os.path.join(

        current_app.config[
            "UPLOAD_FOLDER"
        ],

        stored_filename,
    )

    file.save(
        save_path
    )

    file_size = os.path.getsize(
        save_path
    )

    relative_path = os.path.join(

        "uploads",

        "tasks",

        stored_filename,

    ).replace(
        "\\",
        "/",
    )

    # ========================================================
    # SAVE DATABASE
    # ========================================================

    cursor.execute(
        """
        INSERT INTO task_attachments (

            task_id,

            uploaded_by_membership_id,

            original_filename,

            stored_filename,

            file_path,

            mime_type,

            file_size
        )

        VALUES (
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
            task_id,

            current_membership_id,

            original_filename,

            stored_filename,

            relative_path,

            file.mimetype,

            file_size,
        ),
    )

    conn.commit()

    conn.close()

    return redirect(
        f"/tasks/{task_id}"
    )


# ============================================================
# DOWNLOAD ATTACHMENT
# ============================================================

@tasks_bp.route(
    "/attachments/<int:attachment_id>/download"
)
@login_required
def download_task_attachment(
    attachment_id,
):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_membership = (
        get_current_membership(
            cursor
        )
    )

    if current_membership is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    current_membership_id = (
        current_membership[
            "membership_id"
        ]
    )

    active_term_id = (
        current_membership[
            "term_id"
        ]
    )

    current_department_id = (
        current_membership[
            "department_id"
        ]
    )

    current_role = (
        current_membership[
            "role_name"
        ]
    )

    # ========================================================
    # ATTACHMENT
    # ========================================================

    cursor.execute(
        """
        SELECT

            task_attachments.task_attachment_id,

            task_attachments.task_id,

            task_attachments.original_filename,

            task_attachments.stored_filename,

            tasks.assigned_by_membership_id,

            creator_membership.department_id
                AS task_department_id

        FROM task_attachments

        JOIN tasks

            ON task_attachments.task_id =
               tasks.task_id

        JOIN memberships AS creator_membership

            ON tasks.assigned_by_membership_id =
               creator_membership.membership_id

        WHERE task_attachments.task_attachment_id = ?
          AND creator_membership.term_id = ?
        """,
        (
            attachment_id,
            active_term_id,
        ),
    )

    attachment = (
        cursor.fetchone()
    )

    if attachment is None:

        conn.close()

        return (
            "Attachment not found",
            404,
        )

    # ========================================================
    # ASSIGNMENT
    # ========================================================

    assignment = (
        get_task_assignment(

            cursor,

            attachment[
                "task_id"
            ],

            current_membership_id,
        )
    )

    is_assigned = (
        assignment is not None
    )

    # ========================================================
    # PERMISSION
    # ========================================================

    allowed_to_view = (
        can_view_task(

            current_role=(
                current_role
            ),

            is_assigned=(
                is_assigned
            ),

            current_membership_id=(
                current_membership_id
            ),

            current_department_id=(
                current_department_id
            ),

            task_creator_membership_id=(
                attachment[
                    "assigned_by_membership_id"
                ]
            ),

            task_department_id=(
                attachment[
                    "task_department_id"
                ]
            ),
        )
    )

    conn.close()

    if not allowed_to_view:

        return (
            "Access denied",
            403,
        )

    return send_from_directory(

        current_app.config[
            "UPLOAD_FOLDER"
        ],

        attachment[
            "stored_filename"
        ],

        as_attachment=True,

        download_name=(
            attachment[
                "original_filename"
            ]
        ),
    )


# ============================================================
# VIEW ATTACHMENT
# ============================================================

@tasks_bp.route(
    "/attachments/<int:attachment_id>/view"
)
@login_required
def view_task_attachment(
    attachment_id,
):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_membership = (
        get_current_membership(
            cursor
        )
    )

    if current_membership is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    current_membership_id = (
        current_membership[
            "membership_id"
        ]
    )

    active_term_id = (
        current_membership[
            "term_id"
        ]
    )

    current_department_id = (
        current_membership[
            "department_id"
        ]
    )

    current_role = (
        current_membership[
            "role_name"
        ]
    )

    # ========================================================
    # ATTACHMENT
    # ========================================================

    cursor.execute(
        """
        SELECT

            task_attachments.task_attachment_id,

            task_attachments.task_id,

            task_attachments.stored_filename,

            tasks.assigned_by_membership_id,

            creator_membership.department_id
                AS task_department_id

        FROM task_attachments

        JOIN tasks

            ON task_attachments.task_id =
               tasks.task_id

        JOIN memberships AS creator_membership

            ON tasks.assigned_by_membership_id =
               creator_membership.membership_id

        WHERE task_attachments.task_attachment_id = ?
          AND creator_membership.term_id = ?
        """,
        (
            attachment_id,
            active_term_id,
        ),
    )

    attachment = (
        cursor.fetchone()
    )

    if attachment is None:

        conn.close()

        return (
            "Attachment not found",
            404,
        )

    # ========================================================
    # ASSIGNMENT
    # ========================================================

    assignment = (
        get_task_assignment(

            cursor,

            attachment[
                "task_id"
            ],

            current_membership_id,
        )
    )

    is_assigned = (
        assignment is not None
    )

    # ========================================================
    # PERMISSION
    # ========================================================

    allowed_to_view = (
        can_view_task(

            current_role=(
                current_role
            ),

            is_assigned=(
                is_assigned
            ),

            current_membership_id=(
                current_membership_id
            ),

            current_department_id=(
                current_department_id
            ),

            task_creator_membership_id=(
                attachment[
                    "assigned_by_membership_id"
                ]
            ),

            task_department_id=(
                attachment[
                    "task_department_id"
                ]
            ),
        )
    )

    conn.close()

    if not allowed_to_view:

        return (
            "Access denied",
            403,
        )

    return send_from_directory(

        current_app.config[
            "UPLOAD_FOLDER"
        ],

        attachment[
            "stored_filename"
        ],

        as_attachment=False,
    )


# ============================================================
# DELETE ATTACHMENT
# ============================================================

@tasks_bp.route(
    "/attachments/<int:attachment_id>/delete",
    methods=["POST"],
)
@login_required
def delete_task_attachment(
    attachment_id,
):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_membership = (
        get_current_membership(
            cursor
        )
    )

    if current_membership is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    current_membership_id = (
        current_membership[
            "membership_id"
        ]
    )

    active_term_id = (
        current_membership[
            "term_id"
        ]
    )

    current_department_id = (
        current_membership[
            "department_id"
        ]
    )

    current_role = (
        current_membership[
            "role_name"
        ]
    )

    # ========================================================
    # ATTACHMENT
    # ========================================================

    cursor.execute(
        """
        SELECT

            task_attachments.task_attachment_id,

            task_attachments.task_id,

            task_attachments.stored_filename,

            tasks.review_status,

            tasks.assigned_by_membership_id,

            creator_membership.department_id
                AS task_department_id

        FROM task_attachments

        JOIN tasks

            ON task_attachments.task_id =
               tasks.task_id

        JOIN memberships AS creator_membership

            ON tasks.assigned_by_membership_id =
               creator_membership.membership_id

        WHERE task_attachments.task_attachment_id = ?
          AND creator_membership.term_id = ?
        """,
        (
            attachment_id,
            active_term_id,
        ),
    )

    attachment = (
        cursor.fetchone()
    )

    if attachment is None:

        conn.close()

        return (
            "Attachment not found",
            404,
        )

    # ========================================================
    # MANAGEMENT PERMISSION
    # ========================================================

    allowed_to_manage = (
        can_manage_task(

            current_role=(
                current_role
            ),

            current_membership_id=(
                current_membership_id
            ),

            current_department_id=(
                current_department_id
            ),

            task_creator_membership_id=(
                attachment[
                    "assigned_by_membership_id"
                ]
            ),

            task_department_id=(
                attachment[
                    "task_department_id"
                ]
            ),
        )
    )

    if not allowed_to_manage:

        conn.close()

        return (
            "Access denied",
            403,
        )

    # ========================================================
    # TASK LOCK
    # ========================================================

    if (
        attachment[
            "review_status"
        ]
        != "not_reviewed"
    ):

        conn.close()

        return (
            "This task is locked",
            403,
        )

    # ========================================================
    # DELETE PHYSICAL FILE
    # ========================================================

    file_path = os.path.join(

        current_app.config[
            "UPLOAD_FOLDER"
        ],

        attachment[
            "stored_filename"
        ],
    )

    if os.path.exists(
        file_path
    ):

        os.remove(
            file_path
        )

    # ========================================================
    # DELETE DATABASE RECORD
    # ========================================================

    cursor.execute(
        """
        DELETE FROM task_attachments

        WHERE task_attachment_id = ?
        """,
        (
            attachment_id,
        ),
    )

    conn.commit()

    task_id = (
        attachment[
            "task_id"
        ]
    )

    conn.close()

    return redirect(
        f"/tasks/{task_id}"
    )


# ============================================================
# APPROVE TASK
# ============================================================

@tasks_bp.route(
    "/tasks/<int:task_id>/approve",
    methods=["POST"],
)
@login_required
def approve_task(task_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_membership = (
        get_current_membership(
            cursor
        )
    )

    if current_membership is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    current_membership_id = (
        current_membership[
            "membership_id"
        ]
    )

    active_term_id = (
        current_membership[
            "term_id"
        ]
    )

    current_department_id = (
        current_membership[
            "department_id"
        ]
    )

    current_role = (
        current_membership[
            "role_name"
        ]
    )

    update_pending_reviews(
        conn,
        active_term_id,
    )

    # ========================================================
    # TASK
    # ========================================================

    cursor.execute(
        """
        SELECT

            tasks.review_status,

            tasks.assigned_by_membership_id,

            creator_membership.department_id
                AS task_department_id

        FROM tasks

        JOIN memberships AS creator_membership

            ON tasks.assigned_by_membership_id =
               creator_membership.membership_id

        WHERE tasks.task_id = ?
          AND creator_membership.term_id = ?
        """,
        (
            task_id,
            active_term_id,
        ),
    )

    task = cursor.fetchone()

    if task is None:

        conn.close()

        return (
            "Task not found",
            404,
        )

    # ========================================================
    # MANAGEMENT PERMISSION
    # ========================================================

    allowed_to_manage = (
        can_manage_task(

            current_role=(
                current_role
            ),

            current_membership_id=(
                current_membership_id
            ),

            current_department_id=(
                current_department_id
            ),

            task_creator_membership_id=(
                task[
                    "assigned_by_membership_id"
                ]
            ),

            task_department_id=(
                task[
                    "task_department_id"
                ]
            ),
        )
    )

    if not allowed_to_manage:

        conn.close()

        return (
            "Access denied",
            403,
        )

    # ========================================================
    # REVIEW STATUS
    # ========================================================

    if (
        task[
            "review_status"
        ]
        != "pending_review"
    ):

        conn.close()

        return (
            "This task cannot be approved",
            403,
        )

    # ========================================================
    # APPROVE
    # ========================================================

    cursor.execute(
        """
        UPDATE tasks

        SET
            review_status = 'approved',

            reviewed_by_membership_id = ?,

            reviewed_at =
                CURRENT_TIMESTAMP

        WHERE task_id = ?

          AND task_id IN (

                SELECT tasks.task_id

                FROM tasks

                JOIN memberships AS creator_membership
                    ON tasks.assigned_by_membership_id =
                       creator_membership.membership_id

                WHERE creator_membership.term_id = ?
          )
        """,
        (
            current_membership_id,

            task_id,

            active_term_id,
        ),
    )

    conn.commit()

    conn.close()

    return redirect(
        f"/tasks/{task_id}"
    )


# ============================================================
# REJECT TASK
# ============================================================

@tasks_bp.route(
    "/tasks/<int:task_id>/reject",
    methods=["POST"],
)
@login_required
def reject_task(task_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_membership = (
        get_current_membership(
            cursor
        )
    )

    if current_membership is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    current_membership_id = (
        current_membership[
            "membership_id"
        ]
    )

    active_term_id = (
        current_membership[
            "term_id"
        ]
    )

    current_department_id = (
        current_membership[
            "department_id"
        ]
    )

    current_role = (
        current_membership[
            "role_name"
        ]
    )

    update_pending_reviews(
        conn,
        active_term_id,
    )

    # ========================================================
    # TASK
    # ========================================================

    cursor.execute(
        """
        SELECT

            tasks.review_status,

            tasks.assigned_by_membership_id,

            creator_membership.department_id
                AS task_department_id

        FROM tasks

        JOIN memberships AS creator_membership

            ON tasks.assigned_by_membership_id =
               creator_membership.membership_id

        WHERE tasks.task_id = ?
          AND creator_membership.term_id = ?
        """,
        (
            task_id,
            active_term_id,
        ),
    )

    task = (
        cursor.fetchone()
    )

    if task is None:

        conn.close()

        return (
            "Task not found",
            404,
        )

    # ========================================================
    # MANAGEMENT PERMISSION
    # ========================================================

    allowed_to_manage = (
        can_manage_task(

            current_role=(
                current_role
            ),

            current_membership_id=(
                current_membership_id
            ),

            current_department_id=(
                current_department_id
            ),

            task_creator_membership_id=(
                task[
                    "assigned_by_membership_id"
                ]
            ),

            task_department_id=(
                task[
                    "task_department_id"
                ]
            ),
        )
    )

    if not allowed_to_manage:

        conn.close()

        return (
            "Access denied",
            403,
        )

    # ========================================================
    # REVIEW STATUS
    # ========================================================

    if (
        task[
            "review_status"
        ]
        != "pending_review"
    ):

        conn.close()

        return (
            "This task cannot be rejected",
            403,
        )

    # ========================================================
    # REJECT
    # ========================================================

    cursor.execute(
        """
        UPDATE tasks

        SET
            review_status = 'rejected',

            reviewed_by_membership_id = ?,

            reviewed_at =
                CURRENT_TIMESTAMP

        WHERE task_id = ?

          AND task_id IN (

                SELECT tasks.task_id

                FROM tasks

                JOIN memberships AS creator_membership
                    ON tasks.assigned_by_membership_id =
                       creator_membership.membership_id

                WHERE creator_membership.term_id = ?
          )
        """,
        (
            current_membership_id,

            task_id,

            active_term_id,
        ),
    )

    conn.commit()

    conn.close()

    return redirect(
        f"/tasks/{task_id}"
    )


# ============================================================
# CORRECTION
# ============================================================

@tasks_bp.route(
    "/tasks/<int:task_id>/correction",
    methods=["POST"],
)
@login_required
def upload_task_correction(task_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_membership = (
        get_current_membership(
            cursor
        )
    )

    if current_membership is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    current_membership_id = (
        current_membership[
            "membership_id"
        ]
    )

    active_term_id = (
        current_membership[
            "term_id"
        ]
    )

    current_department_id = (
        current_membership[
            "department_id"
        ]
    )

    current_role = (
        current_membership[
            "role_name"
        ]
    )

    update_pending_reviews(
        conn,
        active_term_id,
    )

    # ========================================================
    # TASK
    # ========================================================

    cursor.execute(
        """
        SELECT

            tasks.task_id,

            tasks.review_status,

            tasks.assigned_by_membership_id,

            creator_membership.department_id
                AS task_department_id

        FROM tasks

        JOIN memberships AS creator_membership

            ON tasks.assigned_by_membership_id =
               creator_membership.membership_id

        WHERE tasks.task_id = ?
          AND creator_membership.term_id = ?
        """,
        (
            task_id,
            active_term_id,
        ),
    )

    task = (
        cursor.fetchone()
    )

    if task is None:

        conn.close()

        return (
            "Task not found",
            404,
        )

    # ========================================================
    # MANAGEMENT PERMISSION
    # ========================================================

    allowed_to_manage = (
        can_manage_task(

            current_role=(
                current_role
            ),

            current_membership_id=(
                current_membership_id
            ),

            current_department_id=(
                current_department_id
            ),

            task_creator_membership_id=(
                task[
                    "assigned_by_membership_id"
                ]
            ),

            task_department_id=(
                task[
                    "task_department_id"
                ]
            ),
        )
    )

    if not allowed_to_manage:

        conn.close()

        return (
            "Access denied",
            403,
        )

    # ========================================================
    # ONLY AFTER REJECTION
    # ========================================================

    if (
        task[
            "review_status"
        ]
        != "rejected"
    ):

        conn.close()

        return (
            "This task is not waiting for correction",
            403,
        )

    # ========================================================
    # FILE
    # ========================================================

    file = request.files.get(
        "attachment"
    )

    if (
        file is None
        or file.filename == ""
    ):

        conn.close()

        return (
            "No file selected",
            400,
        )

    if not allowed_file(
        file.filename
    ):

        conn.close()

        return (
            "File type not allowed",
            400,
        )

    original_filename = (
        secure_filename(
            file.filename
        )
    )

    extension = (
        os.path.splitext(
            original_filename
        )[1]
    )

    stored_filename = (
        uuid.uuid4().hex
        + extension
    )

    save_path = (
        os.path.join(

            current_app.config[
                "UPLOAD_FOLDER"
            ],

            stored_filename,
        )
    )

    file.save(
        save_path
    )

    file_size = (
        os.path.getsize(
            save_path
        )
    )

    relative_path = (
        os.path.join(

            "uploads",

            "tasks",

            stored_filename,

        ).replace(
            "\\",
            "/",
        )
    )

    # ========================================================
    # SAVE CORRECTED FILE
    # ========================================================

    cursor.execute(
        """
        INSERT INTO task_attachments (

            task_id,

            uploaded_by_membership_id,

            original_filename,

            stored_filename,

            file_path,

            mime_type,

            file_size
        )

        VALUES (
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
            task_id,

            current_membership_id,

            original_filename,

            stored_filename,

            relative_path,

            file.mimetype,

            file_size,
        ),
    )

    # ========================================================
    # CLOSE TASK AFTER CORRECTION
    # ========================================================

    cursor.execute(
        """
        UPDATE tasks

        SET
            review_status = 'corrected',

            reviewed_by_membership_id = ?,

            reviewed_at =
                CURRENT_TIMESTAMP

        WHERE task_id = ?

          AND task_id IN (

                SELECT tasks.task_id

                FROM tasks

                JOIN memberships AS creator_membership
                    ON tasks.assigned_by_membership_id =
                       creator_membership.membership_id

                WHERE creator_membership.term_id = ?
          )
        """,
        (
            current_membership_id,

            task_id,

            active_term_id,
        ),
    )

    conn.commit()

    conn.close()

    return redirect(
        f"/tasks/{task_id}"
    )