from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
)

from database import get_db_connection
from permissions import login_required
from context import (
    get_current_user,
    get_active_term_id,
)


projects_bp = Blueprint(
    "projects",
    __name__,
)


# ========================================
# CONSTANTS
# ========================================

DPA_DEPARTMENT_ID = 2

DPA_ROLES = (
    "MEMBER",
    "HEAD",
    "SUB_HEAD",
)

DPA_MANAGEMENT_ROLES = (
    "HEAD",
    "SUB_HEAD",
)


# ========================================
# HELPERS
# ========================================

def is_dpa_management(user):

    return (
        user is not None
        and not user["is_alumni"]
        and user["department_id"]
        == DPA_DEPARTMENT_ID
        and user["role_name"]
        in DPA_MANAGEMENT_ROLES
    )


def is_head_dpa(user):

    return (
        user is not None
        and not user["is_alumni"]
        and user["department_id"]
        == DPA_DEPARTMENT_ID
        and user["role_name"]
        == "HEAD"
    )


def is_dpa_member(user):

    return (
        user is not None
        and not user["is_alumni"]
        and user["department_id"]
        == DPA_DEPARTMENT_ID
        and user["role_name"]
        in DPA_ROLES
    )


def get_project_term_state(
    cursor,
    project_id,
    active_term_id,
):

    cursor.execute("""
        SELECT

            EXISTS (
                SELECT 1

                FROM project_terms

                WHERE project_id = ?
                  AND term_id = ?
            ) AS is_active_term_project,

            EXISTS (
                SELECT 1

                FROM project_terms

                JOIN terms
                    ON project_terms.term_id =
                       terms.term_id

                WHERE project_terms.project_id = ?
                  AND terms.status = 'ARCHIVED'
            ) AS has_archived_term
    """, (
        project_id,
        active_term_id,
        project_id,
    ))

    return cursor.fetchone()


def get_project_for_action(
    cursor,
    project_id,
    active_term_id,
):

    cursor.execute("""
        SELECT

            projects.project_id,

            projects.idea_owner_membership_id,

            projects.name,

            projects.description,

            projects.project_link,

            projects.is_public,

            projects.status,

            owner_membership.person_id
                AS owner_person_id


        FROM projects


        JOIN memberships
            AS owner_membership

            ON projects.idea_owner_membership_id =
               owner_membership.membership_id


        JOIN project_terms

            ON projects.project_id =
               project_terms.project_id


        WHERE projects.project_id = ?

          AND project_terms.term_id = ?


        LIMIT 1
    """, (
        project_id,
        active_term_id,
    ))

    return cursor.fetchone()


# ========================================
# PROJECTS LIST
# ========================================

@projects_bp.route("/projects")
@login_required
def projects():

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()

    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    active_term_id = (
        get_active_term_id()
    )


    can_create_project = (

        is_head_dpa(
            current_user
        )

        and active_term_id is not None
    )


    # ========================================
    # ALUMNI
    # COMPLETED PROJECTS ONLY
    # ========================================

    if current_user["is_alumni"]:

        cursor.execute("""
            SELECT

                projects.project_id,

                projects.name,

                projects.description,

                projects.status,

                projects.created_at,

                people.first_name
                    AS owner_first_name,

                people.last_name
                    AS owner_last_name,

                GROUP_CONCAT(
                    DISTINCT terms.name
                ) AS term_names


            FROM projects


            JOIN memberships

                ON projects.idea_owner_membership_id =
                   memberships.membership_id


            JOIN people

                ON memberships.person_id =
                   people.person_id


            JOIN project_terms

                ON projects.project_id =
                   project_terms.project_id


            JOIN terms

                ON project_terms.term_id =
                   terms.term_id


            WHERE projects.status = 'completed'

              AND terms.status IN (
                    'ACTIVE',
                    'ARCHIVED'
              )


            GROUP BY

                projects.project_id


            ORDER BY

                projects.created_at DESC
        """)


    # ========================================
    # CURRENT MEMBERS
    # ACTIVE + ARCHIVED PROJECTS
    # ========================================

    else:

        cursor.execute("""
            SELECT

                projects.project_id,

                projects.name,

                projects.description,

                projects.status,

                projects.created_at,

                people.first_name
                    AS owner_first_name,

                people.last_name
                    AS owner_last_name,

                GROUP_CONCAT(
                    DISTINCT terms.name
                ) AS term_names


            FROM projects


            JOIN memberships

                ON projects.idea_owner_membership_id =
                   memberships.membership_id


            JOIN people

                ON memberships.person_id =
                   people.person_id


            JOIN project_terms

                ON projects.project_id =
                   project_terms.project_id


            JOIN terms

                ON project_terms.term_id =
                   terms.term_id


            WHERE terms.status IN (
                'ACTIVE',
                'ARCHIVED'
            )


            GROUP BY

                projects.project_id


            ORDER BY

                projects.created_at DESC
        """)


    all_projects = cursor.fetchall()

    conn.close()


    return render_template(

        "projects.html",

        projects=all_projects,

        can_create_project=(
            can_create_project
        ),

        is_alumni=(
            current_user["is_alumni"]
        ),
    )


# ========================================
# NEW PROJECT
# HEAD / SUB_HEAD DPA ONLY
# ========================================

@projects_bp.route(
    "/projects/new",
    methods=[
        "GET",
        "POST",
    ],
)
@login_required
def new_project():

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    active_term_id = (
        get_active_term_id()
    )


    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    if not is_dpa_management(
        current_user
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )


    # ========================================
    # CURRENT MEMBERS
    # FOR IDEA OWNER SELECTION
    # ========================================

    cursor.execute("""
        SELECT

            memberships.membership_id,

            people.first_name,

            people.last_name,

            departments.name
                AS department_name,

            roles.name
                AS role_name


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


        WHERE memberships.term_id = ?

          AND users.is_active = 1


        ORDER BY

            people.first_name ASC,

            people.last_name ASC
    """, (
        active_term_id,
    ))


    idea_owners = cursor.fetchall()


    # ========================================
    # CREATE PROJECT
    # ========================================

    if request.method == "POST":


        name = request.form.get(
            "name",
            "",
        ).strip()


        description = (

            request.form.get(
                "description",
                "",
            ).strip()

            or None
        )


        project_link = (

            request.form.get(
                "project_link",
                "",
            ).strip()

            or None
        )


        idea_owner_membership_id = (

            request.form.get(
                "idea_owner_membership_id"
            )
        )


        # ====================================
        # VALIDATION
        # ====================================

        if not name:

            conn.close()

            return (
                "Project name is required",
                400,
            )


        if not idea_owner_membership_id:

            conn.close()

            return (
                "Idea owner is required",
                400,
            )


        # ====================================
        # VERIFY IDEA OWNER
        # ACTIVE TERM ONLY
        # ====================================

        cursor.execute("""
            SELECT

                memberships.membership_id


            FROM memberships


            JOIN users

                ON memberships.person_id =
                   users.person_id


            WHERE memberships.membership_id = ?

              AND memberships.term_id = ?

              AND users.is_active = 1
        """, (
            idea_owner_membership_id,
            active_term_id,
        ))


        idea_owner = (
            cursor.fetchone()
        )


        if idea_owner is None:

            conn.close()

            return (
                "Invalid idea owner",
                400,
            )


        # ====================================
        # INSERT PROJECT
        # ====================================

        cursor.execute("""
            INSERT INTO projects (

                idea_owner_membership_id,

                name,

                description,

                project_link,

                status
            )

            VALUES (
                ?,
                ?,
                ?,
                ?,
                ?
            )
        """, (

            idea_owner_membership_id,

            name,

            description,

            project_link,

            "active",
        ))


        project_id = (
            cursor.lastrowid
        )


        # ====================================
        # LINK ACTIVE TERM
        # ====================================

        cursor.execute("""
            INSERT INTO project_terms (

                project_id,

                term_id
            )

            VALUES (?, ?)
        """, (
            project_id,
            active_term_id,
        ))


        conn.commit()

        conn.close()


        return redirect(

            url_for(
                "projects.projects"
            )
        )


    conn.close()


    return render_template(

        "new_project.html",

        idea_owners=(
            idea_owners
        ),
    )


# ========================================
# PROJECT DETAIL
# CURRENT MEMBERS ONLY
# ========================================

@projects_bp.route(
    "/projects/<int:project_id>"
)
@login_required
def project_detail(project_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    # Alumni can see completed projects
    # in the list only.

    if current_user["is_alumni"]:

        conn.close()

        return (
            "Access denied",
            403,
        )


    active_term_id = (
        get_active_term_id()
    )


    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    # ========================================
    # GET PROJECT
    # ACTIVE + ARCHIVED ONLY
    # ========================================

    cursor.execute("""
        SELECT

            projects.project_id,

            projects.idea_owner_membership_id,

            projects.name,

            projects.description,

            projects.project_link,

            projects.is_public,

            projects.status,

            projects.created_at,

            owner_membership.person_id
                AS owner_person_id,

            people.first_name
                AS owner_first_name,

            people.last_name
                AS owner_last_name,

            departments.name
                AS owner_department_name,

            roles.name
                AS owner_role_name,

            GROUP_CONCAT(
                DISTINCT terms.name
            ) AS term_names,

            MAX(
                CASE

                    WHEN terms.status = 'ACTIVE'
                    THEN 1

                    ELSE 0

                END
            ) AS is_active_term_project


        FROM projects


        JOIN memberships
            AS owner_membership

            ON projects.idea_owner_membership_id =
               owner_membership.membership_id


        JOIN people

            ON owner_membership.person_id =
               people.person_id


        LEFT JOIN departments

            ON owner_membership.department_id =
               departments.department_id


        JOIN roles

            ON owner_membership.role_id =
               roles.role_id


        JOIN project_terms

            ON projects.project_id =
               project_terms.project_id


        JOIN terms

            ON project_terms.term_id =
               terms.term_id


        WHERE projects.project_id = ?

          AND terms.status IN (
                'ACTIVE',
                'ARCHIVED'
          )


        GROUP BY

            projects.project_id
    """, (
        project_id,
    ))


    project = cursor.fetchone()


    if project is None:

        conn.close()

        return (
            "Project not found",
            404,
        )


    is_active_term_project = bool(

        project[
            "is_active_term_project"
        ]
    )


    # ========================================
    # USER STATUS
    # ========================================

    # We compare PERSON IDs instead of
    # MEMBERSHIP IDs.
    #
    # This means the original idea owner
    # remains the idea owner even if a new
    # mandate creates a new membership_id.

    is_idea_owner = (

        current_user["person_id"]

        ==

        project["owner_person_id"]
    )


    dpa_management = (

        is_dpa_management(
            current_user
        )
    )


    head_dpa = (

        is_head_dpa(
            current_user
        )
    )


    dpa_member = (

        is_dpa_member(
            current_user
        )
    )


    # ========================================
    # PERMISSIONS
    # ARCHIVED-ONLY PROJECTS = READ ONLY
    # ========================================

    can_edit_project = (

        is_active_term_project

        and (

            is_idea_owner

            or dpa_management
        )
    )


    can_delete_project = (

        is_active_term_project

        and dpa_management
    )


    can_manage_team = (

        is_active_term_project

        and project["status"]
        == "active"

        and (

            is_idea_owner

            or dpa_management
        )
    )


    can_participate = (

        is_active_term_project

        and project["status"]
        == "active"

        and (

            dpa_member

            or is_idea_owner
        )
    )


    # ========================================
    # GET VOLUNTEERS
    # ========================================

    cursor.execute("""
        SELECT

            project_volunteers.project_volunteer_id,

            project_volunteers.membership_id,

            project_volunteers.volunteered_at,

            people.first_name,

            people.last_name,

            roles.name
                AS role_name


        FROM project_volunteers


        JOIN memberships

            ON project_volunteers.membership_id =
               memberships.membership_id


        JOIN people

            ON memberships.person_id =
               people.person_id


        JOIN roles

            ON memberships.role_id =
               roles.role_id


        WHERE project_volunteers.project_id = ?


        ORDER BY

            project_volunteers.volunteered_at ASC
    """, (
        project_id,
    ))


    volunteers = cursor.fetchall()


    # ========================================
    # GET FINAL PROJECT TEAM
    # ========================================

    cursor.execute("""
        SELECT

            project_members.project_member_id,

            project_members.membership_id,

            project_members.joined_at,

            people.first_name,

            people.last_name,

            departments.name
                AS department_name,

            roles.name
                AS role_name


        FROM project_members


        JOIN memberships

            ON project_members.membership_id =
               memberships.membership_id


        JOIN people

            ON memberships.person_id =
               people.person_id


        LEFT JOIN departments

            ON memberships.department_id =
               departments.department_id


        JOIN roles

            ON memberships.role_id =
               roles.role_id


        WHERE project_members.project_id = ?


        ORDER BY

            people.first_name ASC,

            people.last_name ASC
    """, (
        project_id,
    ))


    project_members = (
        cursor.fetchall()
    )


    final_member_ids = [

        member["membership_id"]

        for member
        in project_members
    ]


    # ========================================
    # CURRENT USER PARTICIPATION
    # ========================================

    cursor.execute("""
        SELECT

            project_volunteer_id


        FROM project_volunteers


        WHERE project_id = ?

          AND membership_id = ?
    """, (

        project_id,

        current_user[
            "membership_id"
        ],
    ))


    current_volunteer = (
        cursor.fetchone()
    )


    has_volunteered = (

        current_volunteer
        is not None
    )


    # ========================================
    # CURRENT USER IN FINAL TEAM
    # ========================================

    cursor.execute("""
        SELECT

            project_member_id


        FROM project_members


        WHERE project_id = ?

          AND membership_id = ?
    """, (

        project_id,

        current_user[
            "membership_id"
        ],
    ))


    current_project_member = (
        cursor.fetchone()
    )


    is_project_member = (

        current_project_member
        is not None
    )


    conn.close()


    return render_template(

        "project_detail.html",

        project=project,

        volunteers=volunteers,

        project_members=(
            project_members
        ),

        final_member_ids=(
            final_member_ids
        ),

        can_edit_project=(
            can_edit_project
        ),

        can_delete_project=(
            can_delete_project
        ),

        can_manage_team=(
            can_manage_team
        ),

        can_participate=(
            can_participate
        ),

        has_volunteered=(
            has_volunteered
        ),

        is_project_member=(
            is_project_member
        ),

        is_idea_owner=(
            is_idea_owner
        ),

        is_head_dpa=(
            head_dpa
        ),
    )


# ========================================
# PARTICIPATE IN PROJECT
# ACTIVE PROJECT / ACTIVE TERM ONLY
# ========================================

@projects_bp.route(
    "/projects/<int:project_id>/participate",
    methods=["POST"],
)
@login_required
def participate_project(project_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    if current_user["is_alumni"]:

        conn.close()

        return (
            "Access denied",
            403,
        )


    active_term_id = (
        get_active_term_id()
    )


    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    project = get_project_for_action(

        cursor,

        project_id,

        active_term_id,
    )


    if project is None:

        conn.close()

        return (
            "Project not found",
            404,
        )


    if project["status"] != "active":

        conn.close()

        return (
            "Participation is only "
            "available for active projects",
            403,
        )


    is_idea_owner = (

        current_user["person_id"]

        ==

        project["owner_person_id"]
    )


    dpa_member = (

        is_dpa_member(
            current_user
        )
    )


    if not (

        dpa_member

        or is_idea_owner
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )


    # ========================================
    # ALREADY IN FINAL TEAM
    # ========================================

    cursor.execute("""
        SELECT

            project_member_id


        FROM project_members


        WHERE project_id = ?

          AND membership_id = ?
    """, (

        project_id,

        current_user[
            "membership_id"
        ],
    ))


    if cursor.fetchone() is not None:

        conn.close()

        return (
            "You are already part of "
            "the project team",
            400,
        )


    # ========================================
    # ADD VOLUNTEER
    # ========================================

    cursor.execute("""
        INSERT OR IGNORE
        INTO project_volunteers (

            project_id,

            membership_id
        )

        VALUES (?, ?)
    """, (

        project_id,

        current_user[
            "membership_id"
        ],
    ))


    conn.commit()

    conn.close()


    return redirect(

        url_for(

            "projects.project_detail",

            project_id=project_id,
        )
    )


# ========================================
# CANCEL PROJECT PARTICIPATION
# ACTIVE PROJECT / ACTIVE TERM ONLY
# ========================================

@projects_bp.route(
    "/projects/<int:project_id>/participation/cancel",
    methods=["POST"],
)
@login_required
def cancel_project_participation(
    project_id
):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    if current_user["is_alumni"]:

        conn.close()

        return (
            "Access denied",
            403,
        )


    active_term_id = (
        get_active_term_id()
    )


    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    project = get_project_for_action(

        cursor,

        project_id,

        active_term_id,
    )


    if project is None:

        conn.close()

        return (
            "Project not found",
            404,
        )


    if project["status"] != "active":

        conn.close()

        return (
            "Participation cannot be "
            "changed for this project",
            403,
        )


    is_idea_owner = (

        current_user["person_id"]

        ==

        project["owner_person_id"]
    )


    dpa_member = (

        is_dpa_member(
            current_user
        )
    )


    if not (

        dpa_member

        or is_idea_owner
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )


    # ========================================
    # FINAL TEAM CHECK
    # ========================================

    cursor.execute("""
        SELECT

            project_member_id


        FROM project_members


        WHERE project_id = ?

          AND membership_id = ?
    """, (

        project_id,

        current_user[
            "membership_id"
        ],
    ))


    final_member = (
        cursor.fetchone()
    )


    if final_member is not None:

        conn.close()

        return (
            "Final project members cannot "
            "cancel participation",
            400,
        )


    # ========================================
    # DELETE VOLUNTEER
    # ========================================

    cursor.execute("""
        DELETE FROM project_volunteers

        WHERE project_id = ?

          AND membership_id = ?
    """, (

        project_id,

        current_user[
            "membership_id"
        ],
    ))


    conn.commit()

    conn.close()


    return redirect(

        url_for(

            "projects.project_detail",

            project_id=project_id,
        )
    )


# ========================================
# SELECT FINAL PROJECT TEAM
# ACTIVE PROJECT / ACTIVE TERM ONLY
# ========================================

@projects_bp.route(
    "/projects/<int:project_id>/team/select",
    methods=["POST"],
)
@login_required
def select_project_team(project_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    if current_user["is_alumni"]:

        conn.close()

        return (
            "Access denied",
            403,
        )


    active_term_id = (
        get_active_term_id()
    )


    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    project = get_project_for_action(

        cursor,

        project_id,

        active_term_id,
    )


    if project is None:

        conn.close()

        return (
            "Project not found",
            404,
        )


    if project["status"] != "active":

        conn.close()

        return (
            "The team can only be modified "
            "for an active project",
            403,
        )


    is_idea_owner = (

        current_user["person_id"]

        ==

        project["owner_person_id"]
    )


    dpa_management = (

        is_dpa_management(
            current_user
        )
    )


    if not (

        is_idea_owner

        or dpa_management
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )


    # ========================================
    # SELECTED MEMBERS
    # ========================================

    selected_members = (

        request.form.getlist(
            "selected_members"
        )
    )


    if not selected_members:

        conn.close()

        return (
            "Select at least one "
            "project member",
            400,
        )


    try:

        selected_members = [

            int(membership_id)

            for membership_id
            in selected_members
        ]


    except ValueError:

        conn.close()

        return (
            "Invalid member selection",
            400,
        )


    # Remove duplicates.

    selected_members = list(

        dict.fromkeys(
            selected_members
        )
    )


    # ========================================
    # VALID CURRENT VOLUNTEERS
    # ========================================

    cursor.execute("""
        SELECT

            project_volunteers.membership_id


        FROM project_volunteers


        JOIN memberships

            ON project_volunteers.membership_id =
               memberships.membership_id


        JOIN users

            ON memberships.person_id =
               users.person_id


        WHERE project_volunteers.project_id = ?

          AND memberships.term_id = ?

          AND users.is_active = 1
    """, (
        project_id,
        active_term_id,
    ))


    volunteer_rows = (
        cursor.fetchall()
    )


    valid_volunteer_ids = {

        row["membership_id"]

        for row in volunteer_rows
    }


    # ========================================
    # SECURITY CHECK
    # ========================================

    for membership_id in selected_members:

        if (
            membership_id
            not in valid_volunteer_ids
        ):

            conn.close()

            return (
                "Invalid project member selection",
                400,
            )


    # ========================================
    # REPLACE FINAL TEAM
    # ========================================

    cursor.execute("""
        DELETE FROM project_members

        WHERE project_id = ?
    """, (
        project_id,
    ))


    for membership_id in selected_members:

        cursor.execute("""
            INSERT INTO project_members (

                project_id,

                membership_id,

                joined_at
            )

            VALUES (
                ?,
                ?,
                CURRENT_TIMESTAMP
            )
        """, (
            project_id,
            membership_id,
        ))


    conn.commit()

    conn.close()


    return redirect(

        url_for(

            "projects.project_detail",

            project_id=project_id,
        )
    )


# ========================================
# TOGGLE PROJECT PUBLICATION
# HEAD DPA ONLY
# ACTIVE TERM ONLY
# ========================================

@projects_bp.route(
    "/projects/<int:project_id>/publication/toggle",
    methods=["POST"],
)
@login_required
def toggle_project_publication(
    project_id
):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    if not is_head_dpa(
        current_user
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )


    active_term_id = (
        get_active_term_id()
    )


    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    project = get_project_for_action(

        cursor,

        project_id,

        active_term_id,
    )


    if project is None:

        conn.close()

        return (
            "Project not found",
            404,
        )


    # ========================================
    # TOGGLE PUBLIC VISIBILITY
    # ========================================

    new_public_status = (

        0

        if project["is_public"]

        else 1
    )


    cursor.execute("""
        UPDATE projects

        SET is_public = ?

        WHERE project_id = ?
    """, (
        new_public_status,
        project_id,
    ))


    conn.commit()

    conn.close()


    return redirect(

        url_for(

            "projects.project_detail",

            project_id=project_id,
        )
    )


# ========================================
# EDIT PROJECT
# ACTIVE TERM ONLY
# ========================================

@projects_bp.route(
    "/projects/<int:project_id>/edit",
    methods=[
        "GET",
        "POST",
    ],
)
@login_required
def edit_project(project_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    if current_user["is_alumni"]:

        conn.close()

        return (
            "Access denied",
            403,
        )


    active_term_id = (
        get_active_term_id()
    )


    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    # ========================================
    # GET ACTIVE PROJECT
    # ========================================

    project = get_project_for_action(

        cursor,

        project_id,

        active_term_id,
    )


    if project is None:

        conn.close()

        return (
            "Project not found",
            404,
        )


    # ========================================
    # PERMISSION
    # ========================================

    is_idea_owner = (

        current_user["person_id"]

        ==

        project["owner_person_id"]
    )


    dpa_management = (

        is_dpa_management(
            current_user
        )
    )


    if not (

        is_idea_owner

        or dpa_management
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )


    # ========================================
    # UPDATE PROJECT
    # ========================================

    if request.method == "POST":


        name = request.form.get(
            "name",
            "",
        ).strip()


        description = (

            request.form.get(
                "description",
                "",
            ).strip()

            or None
        )


        project_link = (

            request.form.get(
                "project_link",
                "",
            ).strip()

            or None
        )


        status = request.form.get(
            "status",
            "",
        ).strip()


        if not name:

            conn.close()

            return (
                "Project name is required",
                400,
            )


        allowed_statuses = {

            "active",

            "completed",

            "paused",

            "cancelled",
        }


        if status not in allowed_statuses:

            conn.close()

            return (
                "Invalid project status",
                400,
            )


        cursor.execute("""
            UPDATE projects

            SET
                name = ?,

                description = ?,

                project_link = ?,

                status = ?

            WHERE project_id = ?

              AND project_id IN (

                    SELECT project_id

                    FROM project_terms

                    WHERE term_id = ?
              )
        """, (

            name,

            description,

            project_link,

            status,

            project_id,

            active_term_id,
        ))


        conn.commit()

        conn.close()


        return redirect(

            url_for(

                "projects.project_detail",

                project_id=project_id,
            )
        )


    conn.close()


    return render_template(

        "edit_project.html",

        project=project,
    )


# ========================================
# DELETE PROJECT
# HEAD / SUB_HEAD DPA ONLY
# ACTIVE TERM ONLY
# ========================================

@projects_bp.route(
    "/projects/<int:project_id>/delete",
    methods=["POST"],
)
@login_required
def delete_project(project_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    if not is_dpa_management(
        current_user
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )


    active_term_id = (
        get_active_term_id()
    )


    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    project = get_project_for_action(

        cursor,

        project_id,

        active_term_id,
    )


    if project is None:

        conn.close()

        return (
            "Project not found",
            404,
        )


    # ========================================
    # PROTECT DIGITAL ARCHIVE
    # ========================================

    state = get_project_term_state(

        cursor,

        project_id,

        active_term_id,
    )


    if (
        state is not None
        and state[
            "has_archived_term"
        ]
    ):

        conn.close()

        return (
            "This project belongs to an "
            "archived mandate and cannot "
            "be deleted.",
            403,
        )


    # ========================================
    # DELETE VOLUNTEERS
    # ========================================

    cursor.execute("""
        DELETE FROM project_volunteers

        WHERE project_id = ?
    """, (
        project_id,
    ))


    # ========================================
    # DELETE FINAL TEAM
    # ========================================

    cursor.execute("""
        DELETE FROM project_members

        WHERE project_id = ?
    """, (
        project_id,
    ))


    # ========================================
    # DELETE PROJECT TERMS
    # ========================================

    cursor.execute("""
        DELETE FROM project_terms

        WHERE project_id = ?

          AND term_id = ?
    """, (
        project_id,
        active_term_id,
    ))


    # ========================================
    # DELETE PROJECT
    # ========================================

    cursor.execute("""
        DELETE FROM projects

        WHERE project_id = ?
    """, (
        project_id,
    ))


    conn.commit()

    conn.close()


    return redirect(

        url_for(
            "projects.projects"
        )
    )