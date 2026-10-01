from flask import (
    Blueprint,
    render_template,
    request,
    session
)

from datetime import date

from database import get_db_connection
from context import get_active_term_id

from permissions import (
    login_required,
    current_member_required
)


dashboard_bp = Blueprint(
    "dashboard",
    __name__
)


HR_DEPARTMENT_ID = 1


# =========================================================
# PROTECT DASHBOARD
# CURRENT MEMBERS ONLY
# =========================================================

@dashboard_bp.before_request
@current_member_required
def protect_dashboard_module():
    pass


# =========================================================
# CURRENT DASHBOARD USER
# =========================================================

def get_dashboard_user(conn, active_term_id):

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            memberships.membership_id,
            memberships.department_id,

            departments.name
                AS department_name,

            roles.name
                AS role_name

        FROM users

        JOIN memberships
            ON users.person_id =
               memberships.person_id

        LEFT JOIN departments
            ON memberships.department_id =
               departments.department_id

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        WHERE users.user_id = ?
          AND memberships.term_id = ?

        LIMIT 1
    """, (
        session["user_id"],
        active_term_id
    ))

    return cursor.fetchone()


# =========================================================
# MEMBERS STATISTICS
# =========================================================

def get_member_statistics(
    conn,
    active_term_id,
    department_id=None
):

    cursor = conn.cursor()

    query = """
        SELECT
            memberships.membership_id

        FROM memberships

        JOIN users
            ON memberships.person_id =
               users.person_id

        WHERE memberships.term_id = ?
          AND users.is_active = 1
    """

    params = [
        active_term_id
    ]


    if department_id is not None:

        query += """
            AND memberships.department_id = ?
        """

        params.append(
            department_id
        )


    query += """
        ORDER BY memberships.membership_id
    """


    cursor.execute(
        query,
        params
    )

    members = cursor.fetchall()


    total_members = len(
        members
    )


    # =====================================================
    # PROGRESS FOR EACH MEMBER
    # =====================================================

    members_with_tasks = 0

    members_all_completed = 0

    members_with_open_tasks = 0

    members_with_overdue_tasks = 0

    members_without_tasks = 0


    today = date.today().isoformat()


    for member in members:

        membership_id = (
            member["membership_id"]
        )


        cursor.execute("""
            SELECT
                COUNT(
                    DISTINCT tasks.task_id
                ) AS assigned_count,

                COUNT(
                    DISTINCT CASE
                        WHEN tasks.status != 'completed'
                        THEN tasks.task_id
                    END
                ) AS open_count,

                COUNT(
                    DISTINCT CASE

                        WHEN tasks.status != 'completed'

                         AND tasks.due_date IS NOT NULL

                         AND DATE(tasks.due_date)
                             < DATE(?)

                        THEN tasks.task_id

                    END
                ) AS overdue_count

            FROM task_assignees

            JOIN tasks
                ON task_assignees.task_id =
                   tasks.task_id

            WHERE task_assignees.membership_id = ?
        """, (
            today,
            membership_id
        ))


        progress = cursor.fetchone()


        assigned_count = (
            progress["assigned_count"]
            or 0
        )

        open_count = (
            progress["open_count"]
            or 0
        )

        overdue_count = (
            progress["overdue_count"]
            or 0
        )


        if assigned_count == 0:

            members_without_tasks += 1


        else:

            members_with_tasks += 1


            if open_count == 0:

                members_all_completed += 1


            else:

                members_with_open_tasks += 1


            if overdue_count > 0:

                members_with_overdue_tasks += 1


    # =====================================================
    # MEMBER COMPLETION RATE
    # =====================================================

    if members_with_tasks > 0:

        member_completion_rate = round(
            (
                members_all_completed
                /
                members_with_tasks
            )
            *
            100
        )

    else:

        member_completion_rate = 0


    return {
        "total_members":
            total_members,

        "members_with_tasks":
            members_with_tasks,

        "members_all_completed":
            members_all_completed,

        "members_with_open_tasks":
            members_with_open_tasks,

        "members_with_overdue_tasks":
            members_with_overdue_tasks,

        "members_without_tasks":
            members_without_tasks,

        "member_completion_rate":
            member_completion_rate
    }


# =========================================================
# TASK STATISTICS
# =========================================================

def get_task_statistics(
    conn,
    active_term_id,
    department_id=None
):

    cursor = conn.cursor()

    today = date.today().isoformat()


    query = """
        SELECT

            COUNT(
                DISTINCT tasks.task_id
            ) AS total_tasks,


            COUNT(
                DISTINCT CASE
                    WHEN tasks.status = 'completed'
                    THEN tasks.task_id
                END
            ) AS completed_tasks,


            COUNT(
                DISTINCT CASE
                    WHEN tasks.status = 'in_progress'
                    THEN tasks.task_id
                END
            ) AS in_progress_tasks,


            COUNT(
                DISTINCT CASE
                    WHEN tasks.status = 'pending'
                    THEN tasks.task_id
                END
            ) AS pending_tasks,


            COUNT(
                DISTINCT CASE

                    WHEN tasks.status != 'completed'

                     AND tasks.due_date IS NOT NULL

                     AND DATE(tasks.due_date)
                         < DATE(?)

                    THEN tasks.task_id

                END
            ) AS overdue_tasks


        FROM tasks

        JOIN task_assignees
            ON tasks.task_id =
               task_assignees.task_id

        JOIN memberships
            ON task_assignees.membership_id =
               memberships.membership_id

        JOIN users
            ON memberships.person_id =
               users.person_id

        WHERE memberships.term_id = ?

          AND users.is_active = 1
    """


    params = [
        today,
        active_term_id
    ]


    if department_id is not None:

        query += """
            AND memberships.department_id = ?
        """

        params.append(
            department_id
        )


    cursor.execute(
        query,
        params
    )


    stats = cursor.fetchone()


    total_tasks = (
        stats["total_tasks"]
        or 0
    )

    completed_tasks = (
        stats["completed_tasks"]
        or 0
    )

    in_progress_tasks = (
        stats["in_progress_tasks"]
        or 0
    )

    pending_tasks = (
        stats["pending_tasks"]
        or 0
    )

    overdue_tasks = (
        stats["overdue_tasks"]
        or 0
    )


    # =====================================================
    # TASK COMPLETION RATE
    # =====================================================

    if total_tasks > 0:

        task_completion_rate = round(
            (
                completed_tasks
                /
                total_tasks
            )
            *
            100
        )

    else:

        task_completion_rate = 0


    return {
        "total_tasks":
            total_tasks,

        "completed_tasks":
            completed_tasks,

        "in_progress_tasks":
            in_progress_tasks,

        "pending_tasks":
            pending_tasks,

        "overdue_tasks":
            overdue_tasks,

        "task_completion_rate":
            task_completion_rate
    }


# =========================================================
# ATTENDANCE CATEGORY
# =========================================================

def get_attendance_category(
    conn,
    table_name,
    active_term_id,
    department_id=None
):

    cursor = conn.cursor()


    allowed_tables = (
        "event_attendance",
        "training_attendance",
        "meeting_attendance"
    )


    if table_name not in allowed_tables:

        return {
            "total": 0,
            "present": 0,
            "rate": 0
        }


    query = f"""
        SELECT

            COUNT(*) AS total,

            SUM(
                CASE

                    WHEN LOWER(
                        {table_name}.attendance_status
                    ) = 'present'

                    THEN 1

                    ELSE 0

                END
            ) AS present

        FROM {table_name}

        JOIN memberships
            ON {table_name}.membership_id =
               memberships.membership_id

        JOIN users
            ON memberships.person_id =
               users.person_id

        WHERE memberships.term_id = ?

          AND users.is_active = 1
    """


    params = [
        active_term_id
    ]


    if department_id is not None:

        query += """
            AND memberships.department_id = ?
        """

        params.append(
            department_id
        )


    cursor.execute(
        query,
        params
    )


    result = cursor.fetchone()


    total = (
        result["total"]
        or 0
    )

    present = (
        result["present"]
        or 0
    )


    if total > 0:

        rate = round(
            (
                present
                /
                total
            )
            *
            100
        )

    else:

        rate = 0


    return {
        "total": total,
        "present": present,
        "rate": rate
    }


# =========================================================
# ALL ATTENDANCE STATISTICS
# =========================================================

def get_attendance_statistics(
    conn,
    active_term_id,
    department_id=None
):

    events = get_attendance_category(
        conn,
        "event_attendance",
        active_term_id,
        department_id
    )


    trainings = get_attendance_category(
        conn,
        "training_attendance",
        active_term_id,
        department_id
    )


    meetings = get_attendance_category(
        conn,
        "meeting_attendance",
        active_term_id,
        department_id
    )


    total_records = (
        events["total"]
        +
        trainings["total"]
        +
        meetings["total"]
    )


    total_present = (
        events["present"]
        +
        trainings["present"]
        +
        meetings["present"]
    )


    if total_records > 0:

        overall_rate = round(
            (
                total_present
                /
                total_records
            )
            *
            100
        )

    else:

        overall_rate = 0


    return {
        "overall_rate":
            overall_rate,

        "events":
            events,

        "trainings":
            trainings,

        "meetings":
            meetings
    }


# =========================================================
# DEPARTMENTS OVERVIEW
# GLOBAL DASHBOARD ONLY
# =========================================================

def get_departments_overview(
    conn,
    active_term_id
):

    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT

            departments.department_id,
            departments.name

        FROM departments

        JOIN memberships
            ON departments.department_id =
               memberships.department_id

        JOIN users
            ON memberships.person_id =
               users.person_id

        WHERE memberships.term_id = ?

          AND users.is_active = 1

        ORDER BY departments.name
    """, (
        active_term_id,
    ))

    departments = cursor.fetchall()

    overview = []

    for department in departments:

        department_id = (
            department["department_id"]
        )

        member_stats = (
            get_member_statistics(
                conn,
                active_term_id,
                department_id
            )
        )

        task_stats = (
            get_task_statistics(
                conn,
                active_term_id,
                department_id
            )
        )

        attendance_stats = (
            get_attendance_statistics(
                conn,
                active_term_id,
                department_id
            )
        )

        overview.append({

            "department_id":
                department_id,

            "department_name":
                department["name"],

            "members":
                member_stats[
                    "total_members"
                ],

            "task_completion_rate":
                task_stats[
                    "task_completion_rate"
                ],

            "attendance_rate":
                attendance_stats[
                    "overall_rate"
                ]
        })

    return overview


# =========================================================
# DASHBOARD
# =========================================================

@dashboard_bp.route("/dashboard")
@login_required
def dashboard():

    conn = get_db_connection()

    active_term_id = get_active_term_id()

    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503
        )


    # =====================================================
    # CURRENT USER
    # =====================================================

    current_user = (
        get_dashboard_user(
            conn,
            active_term_id
        )
    )
    


    if current_user is None:

        conn.close()

        return (
            "Current membership not found",
            404
        )


    current_role = (
        current_user["role_name"]
    )

    current_department_id = (
        current_user["department_id"]
    )

    current_department_name = (
        current_user["department_name"]
    )


    # =====================================================
    # ACCESS RULES
    # =====================================================

    is_presidency = (
        current_role
        in (
            "PRESIDENT",
            "VICE_PRESIDENT"
        )
    )


    is_hr_head = (
        current_role == "HEAD"
        and
        current_department_id
        == HR_DEPARTMENT_ID
    )


    is_department_head = (
        current_role == "HEAD"
        and
        current_department_id
        != HR_DEPARTMENT_ID
    )


    # MEMBER / SUB_HEAD / OTHER ROLES
    # CANNOT ACCESS DASHBOARD

    if not (
        is_presidency
        or is_hr_head
        or is_department_head
    ):

        conn.close()

        return (
            "Access denied",
            403
        )


    # =====================================================
    # DASHBOARD SCOPE
    # =====================================================

    can_switch_scope = False


    # PRESIDENT / VP
    # ALWAYS WHOLE CLUB

    if is_presidency:

        scope = "club"

        dashboard_department_id = None

        scope_title = "Whole Club"


    # HEAD RH
    # CAN SWITCH RH / WHOLE CLUB

    elif is_hr_head:

        can_switch_scope = True


        requested_scope = (
            request.args.get(
                "scope",
                "department"
            )
        )


        if requested_scope not in (
            "department",
            "club"
        ):

            requested_scope = (
                "department"
            )


        scope = requested_scope


        if scope == "club":

            dashboard_department_id = None

            scope_title = "Whole Club"


        else:

            dashboard_department_id = (
                current_department_id
            )

            scope_title = (
                current_department_name
            )


    # OTHER HEAD
    # OWN DEPARTMENT ONLY

    else:

        scope = "department"

        dashboard_department_id = (
            current_department_id
        )

        scope_title = (
            current_department_name
        )


    # =====================================================
    # STATISTICS
    # =====================================================

    member_stats = (
        get_member_statistics(
            conn,
            active_term_id,
            dashboard_department_id
        )
    )


    task_stats = (
        get_task_statistics(
            conn,
            active_term_id,
            dashboard_department_id
        )
    )


    attendance_stats = (
        get_attendance_statistics(
            conn,
            active_term_id,
            dashboard_department_id
        )
    )


    # =====================================================
    # DEPARTMENT OVERVIEW
    # ONLY WHEN VIEWING WHOLE CLUB
    # =====================================================

    if scope == "club":

        departments_overview = (
            get_departments_overview(
                conn,
                active_term_id
            )
        )

    else:

        departments_overview = []


    conn.close()


    # =====================================================
    # TEMPLATE
    # =====================================================

    return render_template(

        "dashboard.html",

        scope=scope,

        scope_title=scope_title,

        can_switch_scope=(
            can_switch_scope
        ),

        current_role=(
            current_role
        ),

        current_department_name=(
            current_department_name
        ),

        member_stats=(
            member_stats
        ),

        task_stats=(
            task_stats
        ),

        attendance_stats=(
            attendance_stats
        ),

        departments_overview=(
            departments_overview
        )
    )