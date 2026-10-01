from flask import Blueprint, render_template

from database import get_db_connection
from context import get_active_term_id
from permissions import current_member_required


departments_bp = Blueprint(
    "departments",
    __name__
)


# =========================================================
# PROTECT DEPARTMENTS MODULE
# CURRENT MEMBERS ONLY
# =========================================================

@departments_bp.before_request
@current_member_required
def protect_departments_module():
    pass


# =========================================================
# DEPARTMENTS LIST
# =========================================================

@departments_bp.route("/departments")
def departments():

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    if active_term_id is None:
        conn.close()
        return "No active mandate configured.", 503

    # =====================================================
    # GET ALL DEPARTMENTS
    # =====================================================

    cursor.execute("""
        SELECT
            department_id,
            name,
            description

        FROM departments

        ORDER BY
            department_id ASC
    """)

    department_rows = cursor.fetchall()

    departments_list = []

    # =====================================================
    # INFORMATION FOR EACH DEPARTMENT
    # =====================================================

    for department in department_rows:

        department_id = department["department_id"]

        # -------------------------------------------------
        # NUMBER OF CURRENT ACTIVE MEMBERS
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                COUNT(DISTINCT memberships.membership_id)
                    AS total_members

            FROM memberships

            JOIN users
                ON memberships.person_id =
                   users.person_id

            WHERE memberships.term_id = ?
              AND memberships.department_id = ?
              AND users.is_active = 1
        """, (
            active_term_id,
            department_id
        ))

        member_count = cursor.fetchone()

        total_members = (
            member_count["total_members"]
            or 0
        )

        # -------------------------------------------------
        # DEPARTMENT HEAD
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                memberships.membership_id,
                people.person_id,
                people.first_name,
                people.last_name,
                people.profile_photo

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
              AND roles.name = 'HEAD'
              AND users.is_active = 1

            ORDER BY
                people.first_name,
                people.last_name

            LIMIT 1
        """, (
            active_term_id,
            department_id
        ))

        department_head = cursor.fetchone()

        # -------------------------------------------------
        # SUB HEAD
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                memberships.membership_id,
                people.person_id,
                people.first_name,
                people.last_name,
                people.profile_photo

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
              AND roles.name = 'SUB_HEAD'
              AND users.is_active = 1

            ORDER BY
                people.first_name,
                people.last_name

            LIMIT 1
        """, (
            active_term_id,
            department_id
        ))

        department_sub_head = cursor.fetchone()

        # -------------------------------------------------
        # BUILD DEPARTMENT DATA
        # -------------------------------------------------

        departments_list.append({

            "department_id":
                department["department_id"],

            "name":
                department["name"],

            "description":
                department["description"],

            "total_members":
                total_members,

            "head":
                department_head,

            "sub_head":
                department_sub_head
        })

    conn.close()

    return render_template(
        "departments.html",
        departments=departments_list
    )


# =========================================================
# DEPARTMENT DETAIL
# =========================================================

@departments_bp.route(
    "/departments/<int:department_id>"
)
def department_detail(department_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    if active_term_id is None:
        conn.close()
        return "No active mandate configured.", 503

    # =====================================================
    # DEPARTMENT
    # =====================================================

    cursor.execute("""
        SELECT
            department_id,
            name,
            description

        FROM departments

        WHERE department_id = ?
    """, (
        department_id,
    ))

    department = cursor.fetchone()

    if department is None:

        conn.close()

        return (
            "Department not found",
            404
        )

    # =====================================================
    # DEPARTMENT HEAD
    # =====================================================

    cursor.execute("""
        SELECT
            memberships.membership_id,

            people.person_id,
            people.first_name,
            people.last_name,
            people.profile_photo,

            roles.name AS role_name

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
          AND roles.name = 'HEAD'
          AND users.is_active = 1

        ORDER BY
            people.first_name,
            people.last_name

        LIMIT 1
    """, (
        active_term_id,
        department_id
    ))

    department_head = cursor.fetchone()

    # =====================================================
    # DEPARTMENT SUB HEAD
    # =====================================================

    cursor.execute("""
        SELECT
            memberships.membership_id,

            people.person_id,
            people.first_name,
            people.last_name,
            people.profile_photo,

            roles.name AS role_name

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
          AND roles.name = 'SUB_HEAD'
          AND users.is_active = 1

        ORDER BY
            people.first_name,
            people.last_name

        LIMIT 1
    """, (
        active_term_id,
        department_id
    ))

    department_sub_head = cursor.fetchone()

    # =====================================================
    # CURRENT DEPARTMENT MEMBERS
    # =====================================================

    cursor.execute("""
        SELECT
            memberships.membership_id,

            people.person_id,
            people.first_name,
            people.last_name,
            people.profile_photo,

            roles.name AS role_name

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
        active_term_id,
        department_id
    ))

    department_members = cursor.fetchall()

    total_members = len(
        department_members
    )

    conn.close()

    # =====================================================
    # TEMPLATE
    # =====================================================

    return render_template(
        "department_detail.html",
        department=department,
        department_head=department_head,
        department_sub_head=department_sub_head,
        department_members=department_members,
        total_members=total_members
    )