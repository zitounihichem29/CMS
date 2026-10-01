from flask import Blueprint, render_template, session, redirect, url_for, request
from database import get_db_connection
from context import get_active_term_id
from permissions import login_required, current_member_required
from werkzeug.security import generate_password_hash


members_bp = Blueprint("members", __name__)

HR_DEPARTMENT_ID = 1

EXECUTIVE_ROLES = (
    "PRESIDENT",
    "VICE_PRESIDENT",
    "SECRETARY_GENERAL",
)


# ============================================================
# PROTECT MODULE
# ============================================================

@members_bp.before_request
@current_member_required
def protect_members_module():
    pass


# ============================================================
# CURRENT MEMBER
# ============================================================

def get_current_member_permissions(conn):

    active_term_id = get_active_term_id()

    if active_term_id is None:
        return None

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            memberships.membership_id,
            memberships.department_id,
            departments.name AS department_name,
            roles.name AS role_name

        FROM users

        JOIN memberships
            ON users.person_id = memberships.person_id

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
        active_term_id,
    ))

    return cursor.fetchone()


# ============================================================
# MEMBERS LIST
# ============================================================

@members_bp.route("/members")
@login_required
def members():

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    if active_term_id is None:
        conn.close()
        return "No active mandate configured.", 503

    current_member = get_current_member_permissions(conn)

    if current_member is None:
        conn.close()
        return "Current membership not found", 404

    current_role = current_member["role_name"]
    current_department_id = current_member["department_id"]

    # ========================================================
    # PERMISSIONS
    # ========================================================

    is_hr = current_department_id == HR_DEPARTMENT_ID

    is_presidency = current_role in (
        "PRESIDENT",
        "VICE_PRESIDENT",
    )

    is_head_or_subhead = current_role in (
        "HEAD",
        "SUB_HEAD",
    )

    can_add_person = (
        current_department_id == HR_DEPARTMENT_ID
        and current_role in (
            "HEAD",
            "SUB_HEAD",
        )
    )

    if (
        not is_hr
        and not is_presidency
        and not is_head_or_subhead
    ):
        conn.close()
        return "Access denied", 403

    can_view_all_departments = (
        is_hr
        or is_presidency
    )

    can_view_member_details = (
        is_hr
        or is_presidency
        or current_role == "HEAD"
    )

    # ========================================================
    # MEMBERS QUERY
    # ========================================================

    base_query = """
        SELECT
            users.user_id,
            users.username,
            users.is_active,

            people.person_id,
            people.first_name,
            people.last_name,

            memberships.membership_id,

            departments.department_id,
            departments.name AS department_name,

            roles.role_id,
            roles.name AS role_name,

            terms.term_id,
            terms.name AS term_name,

            CASE
                WHEN EXISTS (
                    SELECT 1

                    FROM memberships AS current_membership

                    WHERE current_membership.person_id =
                              people.person_id
                      AND current_membership.term_id = ?
                )
                THEN 0
                ELSE 1
            END AS is_alumni

        FROM memberships

        JOIN people
            ON memberships.person_id =
               people.person_id

        JOIN users
            ON people.person_id =
               users.person_id

        LEFT JOIN departments
            ON memberships.department_id =
               departments.department_id

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        JOIN terms
            ON memberships.term_id =
               terms.term_id
           AND terms.status IN ('ACTIVE', 'ARCHIVED')
    """

    if can_view_all_departments:

        cursor.execute(
            base_query + """
                ORDER BY
                    terms.start_date DESC,
                    people.last_name,
                    people.first_name
            """,
            (active_term_id,),
        )

    else:

        cursor.execute(
            base_query + """
                WHERE memberships.department_id = ?

                ORDER BY
                    terms.start_date DESC,
                    people.last_name,
                    people.first_name
            """,
            (
                active_term_id,
                current_department_id,
            ),
        )

    members = cursor.fetchall()

    # ========================================================
    # DEPARTMENTS
    # ========================================================

    cursor.execute("""
        SELECT
            department_id,
            name

        FROM departments

        ORDER BY name
    """)

    departments = cursor.fetchall()

    # ========================================================
    # ROLES
    # ========================================================

    cursor.execute("""
        SELECT
            role_id,
            name

        FROM roles

        ORDER BY name
    """)

    roles = cursor.fetchall()

    # ========================================================
    # TERMS
    # ========================================================

    cursor.execute("""
        SELECT
            term_id,
            name,
            start_date,
            end_date,
            status

        FROM terms

        WHERE status IN ('ACTIVE', 'ARCHIVED')

        ORDER BY start_date DESC
    """)

    terms = cursor.fetchall()

    conn.close()

    return render_template(
        "members.html",
        members=members,
        departments=departments,
        roles=roles,
        terms=terms,
        can_view_all_departments=can_view_all_departments,
        can_view_member_details=can_view_member_details,
        can_add_person=can_add_person,
    )


# ============================================================
# MEMBER DETAIL
# ============================================================

@members_bp.route("/members/<int:membership_id>")
@login_required
def member_detail(membership_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    if active_term_id is None:
        conn.close()
        return "No active mandate configured.", 503

    current_member = get_current_member_permissions(conn)

    if current_member is None:
        conn.close()
        return "Current membership not found", 404

    current_role = current_member["role_name"]
    current_department_id = current_member["department_id"]

    # ========================================================
    # PERMISSIONS
    # ========================================================

    can_manage_member = (
        current_department_id == HR_DEPARTMENT_ID
        and current_role in (
            "HEAD",
            "SUB_HEAD",
        )
    )

    is_hr = current_department_id == HR_DEPARTMENT_ID

    is_presidency = current_role in (
        "PRESIDENT",
        "VICE_PRESIDENT",
    )

    # ========================================================
    # TARGET MEMBERSHIP
    # ========================================================

    cursor.execute("""
        SELECT
            memberships.department_id,
            memberships.term_id,
            terms.status AS term_status

        FROM memberships

        JOIN terms
            ON memberships.term_id = terms.term_id

        WHERE memberships.membership_id = ?
          AND terms.status IN ('ACTIVE', 'ARCHIVED')
    """, (membership_id,))

    target_membership = cursor.fetchone()

    if target_membership is None:
        conn.close()
        return "Member not found", 404

    target_department_id = target_membership["department_id"]
    target_term_id = target_membership["term_id"]

    # Archived memberships are read-only.
    can_manage_member = (
        can_manage_member
        and target_term_id == active_term_id
    )

    # ========================================================
    # VIEW PERMISSION
    # ========================================================

    can_view_details = False

    if is_hr:
        can_view_details = True

    elif is_presidency:
        can_view_details = True

    elif (
        current_role == "HEAD"
        and target_department_id == current_department_id
    ):
        can_view_details = True

    if not can_view_details:
        conn.close()
        return "Access denied", 403

    # ========================================================
    # MEMBER DATA
    # ========================================================

    cursor.execute("""
        SELECT
            memberships.membership_id,

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
            people.cv,
            people.profession,
            people.profile_photo,

            users.user_id,
            users.username,
            users.is_active,
            users.is_platform_admin,

            departments.department_id,
            departments.name AS department_name,

            roles.role_id,
            roles.name AS role_name,

            terms.term_id,
            terms.name AS term_name,
            terms.start_date,
            terms.end_date,
            terms.status AS term_status

        FROM memberships

        JOIN people
            ON memberships.person_id =
               people.person_id

        JOIN users
            ON people.person_id =
               users.person_id

        LEFT JOIN departments
            ON memberships.department_id =
               departments.department_id

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        JOIN terms
            ON memberships.term_id =
               terms.term_id

        WHERE memberships.membership_id = ?
          AND terms.status IN ('ACTIVE', 'ARCHIVED')
    """, (membership_id,))

    member = cursor.fetchone()

    if member is None:
        conn.close()
        return "Member not found", 404

    # ========================================================
    # APPLICATION MOTIVATION
    # ========================================================

    cursor.execute("""
        SELECT
            applications.motivation

        FROM applications

        JOIN application_periods
            ON applications.application_period_id =
               application_periods.application_period_id

        WHERE applications.person_id = ?
          AND application_periods.term_id = ?

        ORDER BY applications.submitted_at DESC

        LIMIT 1
    """, (
        member["person_id"],
        member["term_id"],
    ))

    application = cursor.fetchone()

    # ========================================================
    # SKILLS
    # ========================================================

    cursor.execute("""
        SELECT
            skill

        FROM person_skills

        WHERE person_id = ?

        ORDER BY skill
    """, (member["person_id"],))

    skills = cursor.fetchall()

    # ========================================================
    # MEMBERSHIP HISTORY
    # ========================================================

    cursor.execute("""
        SELECT
            memberships.membership_id,

            departments.name AS department_name,
            roles.name AS role_name,

            terms.term_id,
            terms.name AS term_name,
            terms.start_date,
            terms.end_date,
            terms.status AS term_status

        FROM memberships

        LEFT JOIN departments
            ON memberships.department_id =
               departments.department_id

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        JOIN terms
            ON memberships.term_id =
               terms.term_id

        WHERE memberships.person_id = ?
          AND terms.status IN ('ACTIVE', 'ARCHIVED')

        ORDER BY terms.start_date DESC
    """, (member["person_id"],))

    membership_history = cursor.fetchall()

    conn.close()

    return render_template(
        "member_detail.html",
        member=member,
        application=application,
        skills=skills,
        membership_history=membership_history,
        can_manage_member=can_manage_member,
    )


# ============================================================
# EDIT MEMBER
# ============================================================

@members_bp.route(
    "/members/<int:membership_id>/edit",
    methods=["GET", "POST"],
)
@login_required
def edit_member(membership_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    if active_term_id is None:
        conn.close()
        return "No active mandate configured.", 503

    current_member = get_current_member_permissions(conn)

    if current_member is None:
        conn.close()
        return "Current membership not found", 404

    current_role = current_member["role_name"]
    current_department_id = current_member["department_id"]

    # ========================================================
    # PERMISSION
    # ========================================================

    can_manage_member = (
        current_department_id == HR_DEPARTMENT_ID
        and current_role in (
            "HEAD",
            "SUB_HEAD",
        )
    )

    if not can_manage_member:
        conn.close()
        return "Access denied", 403

    # ========================================================
    # MEMBER
    # Only ACTIVE mandate can be modified here.
    # ========================================================

    cursor.execute("""
        SELECT
            memberships.membership_id,

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
            people.cv,
            people.profession,
            people.profile_photo,

            users.user_id,
            users.username,
            users.is_platform_admin,

            memberships.department_id,
            memberships.role_id,

            departments.name AS department_name,
            roles.name AS role_name,

            terms.term_id,
            terms.name AS term_name

        FROM memberships

        JOIN people
            ON memberships.person_id =
               people.person_id

        JOIN users
            ON people.person_id =
               users.person_id

        LEFT JOIN departments
            ON memberships.department_id =
               departments.department_id

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        JOIN terms
            ON memberships.term_id =
               terms.term_id

        WHERE memberships.membership_id = ?
          AND memberships.term_id = ?
    """, (
        membership_id,
        active_term_id,
    ))

    member = cursor.fetchone()

    if member is None:
        conn.close()
        return "Member not found", 404

    current_target_is_hr_head = (
        member["role_name"] == "HEAD"
        and member["department_id"] == HR_DEPARTMENT_ID
    )

    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        first_name = request.form[
            "first_name"
        ].strip()

        last_name = request.form[
            "last_name"
        ].strip()

        date_of_birth = request.form.get(
            "date_of_birth",
            "",
        ).strip()

        phone = request.form.get(
            "phone",
            "",
        ).strip()

        email = request.form.get(
            "email",
            "",
        ).strip()

        profession = request.form.get(
            "profession",
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

        username = request.form[
            "username"
        ].strip()

        department_id = (
            request.form.get("department_id")
            or None
        )

        role_id = request.form.get(
            "role_id"
        )

        if not first_name or not last_name:
            conn.close()
            return (
                "First name and last name are required",
                400,
            )

        if not username:
            conn.close()
            return "Username is required", 400

        if not role_id:
            conn.close()
            return "Role is required", 400

        # ====================================================
        # VERIFY ROLE
        # ====================================================

        cursor.execute("""
            SELECT
                role_id,
                name

            FROM roles

            WHERE role_id = ?
              AND name != 'ALUMNI'
        """, (role_id,))

        valid_role = cursor.fetchone()

        if valid_role is None:
            conn.close()
            return "Invalid role", 400

        selected_role_name = valid_role["name"]

        # PRESIDENT / VP / SG cannot be assigned or removed
        # from the normal Members module.
        if (
            member["role_name"] in EXECUTIVE_ROLES
            or selected_role_name in EXECUTIVE_ROLES
        ):

            if selected_role_name != member["role_name"]:

                conn.close()

                return (
                    "Executive roles are managed through "
                    "mandate transition.",
                    403,
                )

        # ====================================================
        # VERIFY DEPARTMENT
        # ====================================================

        if selected_role_name in EXECUTIVE_ROLES:

            department_id = None

        else:

            if not department_id:

                conn.close()

                return (
                    "Department is required for this role",
                    400,
                )

            cursor.execute("""
                SELECT
                    department_id

                FROM departments

                WHERE department_id = ?
            """, (department_id,))

            if cursor.fetchone() is None:

                conn.close()

                return "Department not found", 404

        if department_id is not None:

            try:
                selected_department_id = int(department_id)

            except (TypeError, ValueError):

                conn.close()

                return "Invalid department", 400

        else:

            selected_department_id = None

        selected_is_hr_head = (
            selected_role_name == "HEAD"
            and selected_department_id == HR_DEPARTMENT_ID
        )

        # HR HEAD cannot be assigned or removed here.
        if current_target_is_hr_head or selected_is_hr_head:

            role_changed = (
                selected_role_name != member["role_name"]
            )

            department_changed = (
                selected_department_id
                != member["department_id"]
            )

            if role_changed or department_changed:

                conn.close()

                return (
                    "The HR Head role is managed through "
                    "mandate transition.",
                    403,
                )

        # ====================================================
        # PROTECT PLATFORM ADMIN USERNAME
        # ====================================================

        if (
            member["is_platform_admin"]
            and username != member["username"]
        ):

            conn.close()

            return (
                "Platform admin usernames are managed through "
                "platform administration.",
                403,
            )

        # ====================================================
        # USERNAME UNIQUE
        # ====================================================

        cursor.execute("""
            SELECT
                user_id

            FROM users

            WHERE LOWER(username) = LOWER(?)
              AND user_id != ?
        """, (
            username,
            member["user_id"],
        ))

        existing_username = cursor.fetchone()

        if existing_username is not None:

            conn.close()

            return "Username already exists", 400

        # ====================================================
        # UPDATE PEOPLE
        # ====================================================

        cursor.execute("""
            UPDATE people

            SET
                first_name = ?,
                last_name = ?,
                date_of_birth = ?,
                phone = ?,
                email = ?,
                profession = ?,
                university = ?,
                faculty = ?,
                bio = ?,
                linkedin = ?,
                facebook = ?,
                discord = ?,
                github = ?

            WHERE person_id = ?
        """, (
            first_name,
            last_name,
            date_of_birth or None,
            phone or None,
            email or None,
            profession or None,
            university or None,
            faculty or None,
            bio or None,
            linkedin or None,
            facebook or None,
            discord or None,
            github or None,
            member["person_id"],
        ))

        # ====================================================
        # UPDATE USER
        # ====================================================

        cursor.execute("""
            UPDATE users

            SET username = ?

            WHERE user_id = ?
        """, (
            username,
            member["user_id"],
        ))

        # ====================================================
        # UPDATE MEMBERSHIP
        # ====================================================

        cursor.execute("""
            UPDATE memberships

            SET
                department_id = ?,
                role_id = ?

            WHERE membership_id = ?
              AND term_id = ?
        """, (
            selected_department_id,
            role_id,
            membership_id,
            active_term_id,
        ))

        conn.commit()
        conn.close()

        return redirect(
            url_for(
                "members.member_detail",
                membership_id=membership_id,
            )
        )

    # ========================================================
    # DEPARTMENTS
    # ========================================================

    if current_target_is_hr_head:

        cursor.execute("""
            SELECT
                department_id,
                name

            FROM departments

            WHERE department_id = ?
        """, (HR_DEPARTMENT_ID,))

    else:

        cursor.execute("""
            SELECT
                department_id,
                name

            FROM departments

            ORDER BY name
        """)

    departments = cursor.fetchall()

    # ========================================================
    # EDITABLE ROLES
    # ========================================================

    if (
        member["role_name"] in EXECUTIVE_ROLES
        or current_target_is_hr_head
    ):

        cursor.execute("""
            SELECT
                role_id,
                name

            FROM roles

            WHERE role_id = ?
        """, (
            member["role_id"],
        ))

    else:

        cursor.execute("""
            SELECT
                role_id,
                name

            FROM roles

            WHERE name NOT IN (
                'ALUMNI',
                'PRESIDENT',
                'VICE_PRESIDENT',
                'SECRETARY_GENERAL'
            )

            ORDER BY name
        """)

    roles = cursor.fetchall()

    conn.close()

    return render_template(
        "edit_member.html",
        member=member,
        departments=departments,
        roles=roles,
    )


# ============================================================
# ACTIVATE / DEACTIVATE MEMBER
# ============================================================

@members_bp.route(
    "/members/<int:membership_id>/toggle-active",
    methods=["POST"],
)
@login_required
def toggle_member_active(membership_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    if active_term_id is None:
        conn.close()
        return "No active mandate configured.", 503

    current_member = get_current_member_permissions(conn)

    if current_member is None:
        conn.close()
        return "Current membership not found", 404

    current_role = current_member["role_name"]
    current_department_id = current_member["department_id"]

    can_manage_member = (
        current_department_id == HR_DEPARTMENT_ID
        and current_role in (
            "HEAD",
            "SUB_HEAD",
        )
    )

    if not can_manage_member:

        conn.close()

        return "Access denied", 403

    # ========================================================
    # TARGET USER
    # Only ACTIVE mandate can be changed here.
    # ========================================================

    cursor.execute("""
        SELECT
            users.user_id,
            users.is_active,
            users.is_platform_admin,

            memberships.department_id,
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

        WHERE memberships.membership_id = ?
          AND memberships.term_id = ?
    """, (
        membership_id,
        active_term_id,
    ))

    target_user = cursor.fetchone()

    if target_user is None:

        conn.close()

        return "Member not found", 404

    target_is_hr_head = (
        target_user["role_name"] == "HEAD"
        and target_user["department_id"] == HR_DEPARTMENT_ID
    )

    if target_user["role_name"] in EXECUTIVE_ROLES:

        conn.close()

        return (
            "Executive accounts are managed through "
            "mandate transition.",
            403,
        )

    if target_is_hr_head:

        conn.close()

        return (
            "The HR Head account is managed through "
            "mandate transition.",
            403,
        )

    if target_user["is_platform_admin"]:

        conn.close()

        return (
            "Platform admin accounts cannot be activated or "
            "deactivated from the Members module.",
            403,
        )

    # ========================================================
    # TOGGLE
    # ========================================================

    if target_user["is_active"] == 1:

        new_status = 0

    else:

        new_status = 1

    cursor.execute("""
        UPDATE users

        SET is_active = ?

        WHERE user_id = ?
    """, (
        new_status,
        target_user["user_id"],
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "members.member_detail",
            membership_id=membership_id,
        )
    )


# ============================================================
# ADD PERSON
# ============================================================

@members_bp.route(
    "/members/add",
    methods=["GET", "POST"],
)
@login_required
def add_person():

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    if active_term_id is None:
        conn.close()
        return "No active mandate configured.", 503

    current_member = get_current_member_permissions(conn)

    if current_member is None:

        conn.close()

        return "Current membership not found", 404

    current_department_id = current_member[
        "department_id"
    ]

    current_role = current_member[
        "role_name"
    ]

    # ========================================================
    # PERMISSION
    # ========================================================

    can_add_person = (
        current_department_id == HR_DEPARTMENT_ID
        and current_role in (
            "HEAD",
            "SUB_HEAD",
        )
    )

    if not can_add_person:

        conn.close()

        return "Access denied", 403

    # ========================================================
    # DEPARTMENTS
    # ========================================================

    cursor.execute("""
        SELECT
            department_id,
            name

        FROM departments

        ORDER BY name
    """)

    departments = cursor.fetchall()

    # ========================================================
    # PAST TERMS
    # DRAFT mandates are not historical mandates.
    # ========================================================

    cursor.execute("""
        SELECT
            term_id,
            name

        FROM terms

        WHERE status = 'ARCHIVED'

        ORDER BY start_date DESC
    """)

    past_terms = cursor.fetchall()

    # ========================================================
    # HISTORICAL ROLES
    # ========================================================

    cursor.execute("""
        SELECT
            role_id,
            name

        FROM roles

        WHERE name != 'ALUMNI'

        ORDER BY role_id
    """)

    roles = cursor.fetchall()

    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        person_type = request.form.get(
            "person_type",
            "",
        ).strip().lower()

        # ====================================================
        # PERSONAL INFORMATION
        # ====================================================

        first_name = request.form.get(
            "first_name",
            "",
        ).strip()

        last_name = request.form.get(
            "last_name",
            "",
        ).strip()

        date_of_birth = (
            request.form.get(
                "date_of_birth"
            )
            or None
        )

        phone = (
            request.form.get(
                "phone",
                "",
            ).strip()
            or None
        )

        email = (
            request.form.get(
                "email",
                "",
            ).strip()
            or None
        )

        university = (
            request.form.get(
                "university",
                "",
            ).strip()
            or None
        )

        faculty = (
            request.form.get(
                "faculty",
                "",
            ).strip()
            or None
        )

        profession = (
            request.form.get(
                "profession",
                "",
            ).strip()
            or None
        )

        bio = (
            request.form.get(
                "bio",
                "",
            ).strip()
            or None
        )

        linkedin = (
            request.form.get(
                "linkedin",
                "",
            ).strip()
            or None
        )

        facebook = (
            request.form.get(
                "facebook",
                "",
            ).strip()
            or None
        )

        discord = (
            request.form.get(
                "discord",
                "",
            ).strip()
            or None
        )

        github = (
            request.form.get(
                "github",
                "",
            ).strip()
            or None
        )

        # ====================================================
        # BASIC VALIDATION
        # ====================================================

        if not first_name or not last_name:

            conn.close()

            return (
                "First name and last name are required",
                400,
            )

        if person_type not in (
            "member",
            "coach",
            "alumni",
        ):

            conn.close()

            return "Invalid person type", 400



        # ====================================================
        # ACCOUNT
        # MEMBER = OPTIONAL
        # ALUMNI = REQUIRED
        # ====================================================

        username = None
        password = None
        create_account = False


        # ----------------------------------------------------
        # MEMBER ACCOUNT
        # Optional for historical/current membership records.
        # ----------------------------------------------------

        if person_type == "member":

            create_account = (
                request.form.get(
                    "create_account"
                )
                == "1"
            )


            if create_account:

                username = request.form.get(
                    "username",
                    "",
                ).strip()

                password = request.form.get(
                    "password",
                    "",
                )


                if (
                    not username
                    or not password
                ):

                    conn.close()

                    return (
                        "Username and password are required "
                        "when creating a CMS account.",
                        400,
                    )


                cursor.execute("""
                    SELECT
                        user_id

                    FROM users

                    WHERE LOWER(username) = LOWER(?)
                """, (
                    username,
                ))


                if (
                    cursor.fetchone()
                    is not None
                ):

                    conn.close()

                    return (
                        "Username already exists",
                        400,
                    )


        # ----------------------------------------------------
        # ALUMNI ACCOUNT
        # Alumni accounts remain mandatory.
        # ----------------------------------------------------

        elif person_type == "alumni":

            create_account = True


            username = request.form.get(
                "username",
                "",
            ).strip()

            password = request.form.get(
                "password",
                "",
            )


            if (
                not username
                or not password
            ):

                conn.close()

                return (
                    "Username and password are required "
                    "for an alumni.",
                    400,
                )


            cursor.execute("""
                SELECT
                    user_id

                FROM users

                WHERE LOWER(username) = LOWER(?)
            """, (
                username,
            ))


            if (
                cursor.fetchone()
                is not None
            ):

                conn.close()

                return (
                    "Username already exists",
                    400,
                )

        # ====================================================
        # MEMBER INFORMATION
        # ====================================================

        department_id = None
        member_role_id = None

        if person_type == "member":

            department_id = request.form.get(
                "department_id"
            )

            if not department_id:

                conn.close()

                return (
                    "Department is required for a member",
                    400,
                )

            try:

                department_id = int(department_id)

            except (TypeError, ValueError):

                conn.close()

                return "Invalid department", 400

            # -----------------------------------------------
            # VERIFY DEPARTMENT
            # -----------------------------------------------

            cursor.execute("""
                SELECT
                    department_id

                FROM departments

                WHERE department_id = ?
            """, (department_id,))

            if cursor.fetchone() is None:

                conn.close()

                return "Department not found", 404

            # -----------------------------------------------
            # MEMBER ROLE
            # -----------------------------------------------

            cursor.execute("""
                SELECT
                    role_id

                FROM roles

                WHERE name = 'MEMBER'
            """)

            member_role = cursor.fetchone()

            if member_role is None:

                conn.close()

                return "MEMBER role not found", 500

            member_role_id = member_role[
                "role_id"
            ]

        # ====================================================
        # ALUMNI INFORMATION
        # ====================================================

        alumni_term_id = None
        alumni_department_id = None
        alumni_role_id = None

        if person_type == "alumni":

            alumni_term_id = request.form.get(
                "alumni_term_id"
            )

            alumni_department_id = (
                request.form.get(
                    "alumni_department_id"
                )
                or None
            )

            alumni_role_id = request.form.get(
                "alumni_role_id"
            )

            if (
                not alumni_term_id
                or not alumni_role_id
            ):

                conn.close()

                return (
                    "Mandate and role are required "
                    "for an alumni",
                    400,
                )

            # -----------------------------------------------
            # ALUMNI CANNOT BELONG TO CURRENT TERM
            # -----------------------------------------------

            if str(alumni_term_id) == str(
                active_term_id
            ):

                conn.close()

                return (
                    "An alumni cannot have a membership "
                    "in the current term",
                    400,
                )

            # -----------------------------------------------
            # VERIFY ARCHIVED TERM
            # -----------------------------------------------

            cursor.execute("""
                SELECT
                    term_id

                FROM terms

                WHERE term_id = ?
                  AND status = 'ARCHIVED'
            """, (
                alumni_term_id,
            ))

            if cursor.fetchone() is None:

                conn.close()

                return "Mandate not found", 404

            # -----------------------------------------------
            # VERIFY HISTORICAL ROLE
            # -----------------------------------------------

            cursor.execute("""
                SELECT
                    role_id,
                    name

                FROM roles

                WHERE role_id = ?
                  AND name != 'ALUMNI'
            """, (alumni_role_id,))

            historical_role = cursor.fetchone()

            if historical_role is None:

                conn.close()

                return "Role not found", 404

            historical_role_name = historical_role[
                "name"
            ]

            # -----------------------------------------------
            # VERIFY HISTORICAL DEPARTMENT
            # -----------------------------------------------

            if historical_role_name in EXECUTIVE_ROLES:

                alumni_department_id = None

            else:

                if not alumni_department_id:

                    conn.close()

                    return (
                        "Department is required "
                        "for this historical role",
                        400,
                    )

                try:

                    alumni_department_id = int(
                        alumni_department_id
                    )

                except (TypeError, ValueError):

                    conn.close()

                    return "Invalid department", 400

                cursor.execute("""
                    SELECT
                        department_id

                    FROM departments

                    WHERE department_id = ?
                """, (alumni_department_id,))

                if cursor.fetchone() is None:

                    conn.close()

                    return "Department not found", 404

        # ====================================================
        # CREATE PERSON
        # ====================================================

        cursor.execute("""
            INSERT INTO people (
                first_name,
                last_name,
                date_of_birth,
                phone,
                email,
                university,
                faculty,
                profession,
                bio,
                linkedin,
                facebook,
                discord,
                github
            )

            VALUES (
                ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            )
        """, (
            first_name,
            last_name,
            date_of_birth,
            phone,
            email,
            university,
            faculty,
            profession,
            bio,
            linkedin,
            facebook,
            discord,
            github,
        ))

        person_id = cursor.lastrowid

        # ====================================================
        # MEMBER
        # ====================================================

        
        if person_type == "member":

            # ------------------------------------------------
            # OPTIONAL CMS ACCOUNT
            # ------------------------------------------------

            if create_account:

                password_hash = (
                    generate_password_hash(
                        password
                    )
                )


                cursor.execute("""
                    INSERT INTO users (
                        person_id,
                        username,
                        password_hash,
                        is_active
                    )

                    VALUES (?, ?, ?, 1)
                """, (
                    person_id,
                    username,
                    password_hash,
                ))


            # ------------------------------------------------
            # MEMBERSHIP
            # Always created for a MEMBER.
            # ------------------------------------------------

            cursor.execute("""
                INSERT INTO memberships (
                    person_id,
                    term_id,
                    role_id,
                    department_id
                )

                VALUES (?, ?, ?, ?)
            """, (
                person_id,
                active_term_id,
                member_role_id,
                department_id,
            ))

        # ====================================================
        # ALUMNI
        # ====================================================

        elif person_type == "alumni":

            password_hash = generate_password_hash(
                password
            )

            cursor.execute("""
                INSERT INTO users (
                    person_id,
                    username,
                    password_hash,
                    is_active
                )

                VALUES (?, ?, ?, 1)
            """, (
                person_id,
                username,
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
                person_id,
                alumni_term_id,
                alumni_role_id,
                alumni_department_id,
            ))

        # ====================================================
        # COACH
        # ====================================================

        elif person_type == "coach":

            # Coach exists only in PEOPLE.
            # No account and no membership.
            pass

        # ====================================================
        # SAVE
        # ====================================================

        conn.commit()
        conn.close()

        return redirect(
            url_for(
                "members.members"
            )
        )

    # ========================================================
    # GET
    # ========================================================

    conn.close()

    return render_template(
        "add_person.html",
        departments=departments,
        past_terms=past_terms,
        roles=roles,
    )