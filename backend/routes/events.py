import os
import shutil
import uuid

from datetime import date, timedelta

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from werkzeug.utils import secure_filename

from context import (
    get_active_term_id,
    get_current_user,
)

from database import get_db_connection
from permissions import login_required


events_bp = Blueprint(
    "events",
    __name__,
)


# ============================================================
# CONSTANTS
# ============================================================

HR_DEPARTMENT_ID = 1
DCM_DEPARTMENT_ID = 4


HR_EVENT_ROLES = (
    "MEMBER",
    "SUB_HEAD",
    "HEAD",
)


DCM_MEDIA_ROLES = (
    "HEAD",
    "SUB_HEAD",
)


IMAGE_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "gif",
    "webp",
}


VIDEO_EXTENSIONS = {
    "mp4",
    "mov",
    "avi",
    "mkv",
    "webm",
}


DOCUMENT_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "odt",
}


# ============================================================
# HELPERS
# ============================================================

def is_hr_event_member(user):

    return (
        user is not None
        and not user["is_alumni"]
        and user["department_id"]
        == HR_DEPARTMENT_ID
        and user["role_name"]
        in HR_EVENT_ROLES
    )


def is_department_head(user):

    return (
        user is not None
        and not user["is_alumni"]
        and user["department_id"] is not None
        and user["role_name"] == "HEAD"
    )



def is_dcm_media_manager(user):

    return (
        user is not None
        and not user["is_alumni"]
        and user["department_id"]
        == DCM_DEPARTMENT_ID
        and user["role_name"]
        in DCM_MEDIA_ROLES
    )


def is_dcm_media_publisher(user):

    return (
        user is not None
        and not user["is_alumni"]
        and user["department_id"]
        == DCM_DEPARTMENT_ID
        and user["role_name"]
        == "HEAD"
    )


def event_edit_deadline(end_date):

    return (
        date.fromisoformat(
            end_date
        )
        + timedelta(days=10)
    )


# ============================================================
# EVENTS LIST
# ============================================================

@events_bp.route("/events")
@login_required
def events():

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()

    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    # ========================================================
    # CREATE PERMISSION
    # RH MEMBERS ONLY
    # ========================================================

    active_term_id = get_active_term_id()
    
    can_create_event = (
        is_department_head(
            current_user
        )
        and active_term_id is not None
    )


    # ========================================================
    # GET EVENTS
    #
    # ACTIVE + ARCHIVED are visible.
    # DRAFT events are never displayed here.
    # ========================================================

    cursor.execute("""
        SELECT

            events.event_id,

            events.title,

            events.description,

            events.event_date,

            events.end_date,

            events.start_time,

            events.end_time,

            events.location,

            terms.name
                AS term_name,

            terms.status
                AS term_status,

            people.first_name
                AS leader_first_name,

            people.last_name
                AS leader_last_name


        FROM events


        JOIN terms

            ON events.term_id =
               terms.term_id


        JOIN memberships

            ON events.event_leader_membership_id =
               memberships.membership_id


        JOIN people

            ON memberships.person_id =
               people.person_id


        WHERE terms.status IN (
            'ACTIVE',
            'ARCHIVED'
        )


        ORDER BY

            events.event_date ASC
    """)


    all_events = cursor.fetchall()

    conn.close()


    # ========================================================
    # UPCOMING / PAST
    # ========================================================

    today = date.today().isoformat()

    upcoming_events = []

    past_events = []


    for event in all_events:

        if event["end_date"] >= today:

            upcoming_events.append(
                event
            )

        else:

            past_events.append(
                event
            )


    # Past events:
    # newest first.

    past_events.reverse()


    return render_template(

        "events.html",

        upcoming_events=(
            upcoming_events
        ),

        past_events=(
            past_events
        ),

        can_create_event=(
            can_create_event
        ),

        is_alumni=(
            current_user["is_alumni"]
        ),
    )


# ============================================================
# NEW EVENT
# ============================================================

@events_bp.route(
    "/events/new",
    methods=[
        "GET",
        "POST",
    ],
)
@login_required
def new_event():

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    # ========================================================
    # ACTIVE TERM
    # ========================================================

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
    # PERMISSION
    # RH MEMBERS ONLY
    # ========================================================

    if not is_department_head(
        current_user
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )


    # ========================================================
    # AVAILABLE EVENT LEADERS
    # ACTIVE MEMBERS ONLY
    #
    # LEFT JOIN departments is important because
    # President / VP / Secretary General may have
    # department_id = NULL.
    # ========================================================

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


    event_leaders = (
        cursor.fetchall()
    )


    # ========================================================
    # CREATE EVENT
    # ========================================================

    if request.method == "POST":


        title = request.form.get(
            "title",
            "",
        ).strip()


        description = (
            request.form.get(
                "description",
                "",
            ).strip()
            or None
        )


        event_leader_membership_id = (
            request.form.get(
                "event_leader_membership_id"
            )
        )


        event_date = (
            request.form.get(
                "event_date"
            )
        )


        end_date = (
            request.form.get(
                "end_date"
            )
        )


        start_time = (
            request.form.get(
                "start_time"
            )
            or None
        )


        end_time = (
            request.form.get(
                "end_time"
            )
            or None
        )


        location = (
            request.form.get(
                "location",
                "",
            ).strip()
            or None
        )


        # ====================================================
        # VALIDATION
        # ====================================================

        if not title:

            conn.close()

            return (
                "Title is required",
                400,
            )


        if not event_leader_membership_id:

            conn.close()

            return (
                "Event leader is required",
                400,
            )


        if not event_date:

            conn.close()

            return (
                "Start date is required",
                400,
            )


        if not end_date:

            conn.close()

            return (
                "End date is required",
                400,
            )


        if end_date < event_date:

            conn.close()

            return (
                "End date cannot be before "
                "start date",
                400,
            )


        if (
            event_date == end_date
            and start_time
            and end_time
            and end_time < start_time
        ):

            conn.close()

            return (
                "End time cannot be before "
                "start time",
                400,
            )


        # ====================================================
        # VERIFY EVENT LEADER
        # ACTIVE TERM ONLY
        # ====================================================

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
            event_leader_membership_id,
            active_term_id,
        ))


        leader = cursor.fetchone()


        if leader is None:

            conn.close()

            return (
                "Invalid event leader",
                400,
            )


        # ====================================================
        # INSERT EVENT
        # ====================================================

        cursor.execute("""
            INSERT INTO events (

                term_id,

                event_leader_membership_id,

                title,

                description,

                event_date,

                end_date,

                start_time,

                end_time,

                location
            )

            VALUES (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                ?
            )
        """, (

            active_term_id,

            event_leader_membership_id,

            title,

            description,

            event_date,

            end_date,

            start_time,

            end_time,

            location,
        ))


        conn.commit()

        conn.close()


        return redirect(

            url_for(
                "events.events"
            )
        )


    # ========================================================
    # GET
    # ========================================================

    conn.close()


    return render_template(

        "new_event.html",

        event_leaders=(
            event_leaders
        ),
    )


# ============================================================
# EVENT DETAIL
# ============================================================

@events_bp.route(
    "/events/<int:event_id>"
)
@login_required
def event_detail(event_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    # ========================================================
    # ALUMNI
    #
    # Can see Events list,
    # but not Event details.
    # ========================================================

    if current_user["is_alumni"]:

        conn.close()

        return (
            "Access denied",
            403,
        )


    # ========================================================
    # GET EVENT
    #
    # ACTIVE + ARCHIVED can be viewed.
    # DRAFT is not visible.
    # ========================================================

    cursor.execute("""
        SELECT

            events.event_id,

            events.term_id,

            events.event_leader_membership_id,

            events.title,

            events.description,

            events.event_date,

            events.end_date,

            events.start_time,

            events.end_time,

            events.location,

            terms.name
                AS term_name,

            terms.status
                AS term_status,

            people.first_name
                AS leader_first_name,

            people.last_name
                AS leader_last_name,

            departments.name
                AS leader_department_name,

            roles.name
                AS leader_role_name


        FROM events


        JOIN terms

            ON events.term_id =
               terms.term_id


        JOIN memberships

            ON events.event_leader_membership_id =
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


        WHERE events.event_id = ?

          AND terms.status IN (
              'ACTIVE',
              'ARCHIVED'
          )
    """, (
        event_id,
    ))


    event = cursor.fetchone()


    if event is None:

        conn.close()

        return (
            "Event not found",
            404,
        )


    # ========================================================
    # EVENT END DATE + DEADLINE
    # ========================================================

    final_event_date = (
        date.fromisoformat(
            event["end_date"]
        )
    )


    edit_deadline = (

        final_event_date

        + timedelta(
            days=10
        )
    )


    # ========================================================
    # ACTIVE / ARCHIVED
    # ========================================================

    is_active_event = (

        event["term_status"]

        == "ACTIVE"
    )


    # ========================================================
    # EVENT LEADER
    # ========================================================

    is_event_leader = (

        current_user[
            "membership_id"
        ]

        ==

        event[
            "event_leader_membership_id"
        ]
    )


    # ========================================================
    # HR MEMBER
    # ========================================================

    is_hr_member = (
        is_hr_event_member(
            current_user
        )
    )


    # ========================================================
    # EVENT LEADER EDIT PERMISSION
    # ACTIVE EVENT ONLY
    # Until 10 days after END DATE
    # ========================================================

    can_edit_event = (

        is_active_event

        and is_event_leader

        and date.today()
        <= edit_deadline
    )


    # ========================================================
    # ORGANIZATIONS MANAGEMENT
    # EVENT LEADER ONLY
    # ACTIVE EVENT ONLY
    # ========================================================

    can_manage_organizations = (

        is_active_event

        and is_event_leader

        and date.today()
        <= edit_deadline
    )


    # ========================================================
    # DELETE EVENT
    # HEAD RH ONLY
    # ACTIVE EVENT ONLY
    # ========================================================

    can_delete_event = (

        is_active_event

        and current_user[
            "department_id"
        ]
        == HR_DEPARTMENT_ID

        and current_user[
            "role_name"
        ]
        == "HEAD"
    )


    # ========================================================
    # ATTENDANCE SHEET
    # RH ONLY
    # ACTIVE EVENT ONLY
    # ========================================================

    can_manage_attendance = (

        is_active_event

        and is_hr_member
    )


    # ========================================================
    # EVENT MEDIA MANAGEMENT
    # HEAD / SUB_HEAD DCM
    # ACTIVE EVENT ONLY
    # ========================================================

    can_manage_media = (

        is_active_event

        and is_dcm_media_manager(
            current_user
        )
    )


    # ========================================================
    # EVENT MEDIA PUBLICATION
    # HEAD DCM ONLY
    # ACTIVE EVENT ONLY
    # ========================================================

    can_publish_media = (

        is_active_event

        and is_dcm_media_publisher(
            current_user
        )
    )


    # ========================================================
    # EVENT DOCUMENTS UPLOAD
    # Event Leader OR RH
    # ACTIVE EVENT ONLY
    # ========================================================

    can_upload_documents = (

        is_active_event

        and date.today()
        <= edit_deadline

        and (

            is_event_leader

            or is_hr_member
        )
    )


    # ========================================================
    # DELETE EVENT DOCUMENTS
    # RH ONLY
    # ACTIVE EVENT ONLY
    # ========================================================

    can_delete_documents = (

        is_active_event

        and is_hr_member
    )


    # ========================================================
    # ORGANIZATIONS LINKED TO EVENT
    # ========================================================

    cursor.execute("""
        SELECT

            organizations.organization_id,

            organizations.name,

            organizations.organization_type


        FROM event_organizations


        JOIN organizations

            ON event_organizations.organization_id =
               organizations.organization_id


        WHERE event_organizations.event_id = ?


        ORDER BY

            organizations.name ASC
    """, (
        event_id,
    ))


    event_organizations = (
        cursor.fetchall()
    )


    # ========================================================
    # ALL AVAILABLE ORGANIZATIONS
    # ========================================================

    available_organizations = []


    if can_manage_organizations:

        cursor.execute("""
            SELECT

                organization_id,

                name,

                organization_type


            FROM organizations


            ORDER BY

                name ASC
        """)


        available_organizations = (
            cursor.fetchall()
        )


    # ========================================================
    # SELECTED ORGANIZATION IDS
    # ========================================================

    selected_organization_ids = [

        organization[
            "organization_id"
        ]

        for organization
        in event_organizations
    ]


    # ========================================================
    # GET EVENT MEDIA
    # ========================================================

    cursor.execute("""
        SELECT

            event_media_id,

            media_type,

            file_path,

            caption,

            is_public


        FROM event_media


        WHERE event_id = ?


        ORDER BY

            event_media_id DESC
    """, (
        event_id,
    ))


    event_media = (
        cursor.fetchall()
    )


    # ========================================================
    # GET EVENT DOCUMENTS
    # ========================================================

    cursor.execute("""
        SELECT

            event_documents.event_document_id,

            event_documents.event_id,

            event_documents.created_by_membership_id,

            event_documents.document_name,

            event_documents.file_path,

            event_documents.created_at,

            people.first_name
                AS creator_first_name,

            people.last_name
                AS creator_last_name


        FROM event_documents


        JOIN memberships

            ON event_documents.created_by_membership_id =
               memberships.membership_id


        JOIN people

            ON memberships.person_id =
               people.person_id


        WHERE event_documents.event_id = ?


        ORDER BY

            event_documents.created_at DESC
    """, (
        event_id,
    ))


    event_documents = (
        cursor.fetchall()
    )


    conn.close()


    # ========================================================
    # TEMPLATE
    # ========================================================

    return render_template(

        "event_detail.html",

        event=event,

        event_media=(
            event_media
        ),

        event_documents=(
            event_documents
        ),

        event_organizations=(
            event_organizations
        ),

        available_organizations=(
            available_organizations
        ),

        selected_organization_ids=(
            selected_organization_ids
        ),

        can_edit_event=(
            can_edit_event
        ),

        can_delete_event=(
            can_delete_event
        ),

        can_manage_attendance=(
            can_manage_attendance
        ),

        can_manage_media=(
            can_manage_media
        ),

        can_publish_media=(
            can_publish_media
        ),

        can_upload_documents=(
            can_upload_documents
        ),

        can_delete_documents=(
            can_delete_documents
        ),

        can_manage_organizations=(
            can_manage_organizations
        ),

        edit_deadline=(
            edit_deadline
        ),
    )


# ============================================================
# UPDATE EVENT ORGANIZATIONS
# EVENT LEADER ONLY
# ACTIVE MANDATE ONLY
# ============================================================

@events_bp.route(
    "/events/<int:event_id>/organizations",
    methods=["POST"],
)
@login_required
def update_event_organizations(
    event_id
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


    # ========================================================
    # GET ACTIVE EVENT
    # ========================================================

    cursor.execute("""
        SELECT

            event_id,

            event_leader_membership_id,

            end_date


        FROM events


        WHERE event_id = ?

          AND term_id = ?
    """, (
        event_id,
        active_term_id,
    ))


    event = cursor.fetchone()


    if event is None:

        conn.close()

        return (
            "Event not found",
            404,
        )


    # ========================================================
    # EVENT LEADER ONLY
    # ========================================================

    if (

        current_user[
            "membership_id"
        ]

        !=

        event[
            "event_leader_membership_id"
        ]
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )


    # ========================================================
    # EDIT DEADLINE
    # ========================================================

    edit_deadline = (
        event_edit_deadline(
            event["end_date"]
        )
    )


    if date.today() > edit_deadline:

        conn.close()

        return (
            "The organization editing "
            "period has expired",
            403,
        )


    # ========================================================
    # SELECTED ORGANIZATIONS
    # ========================================================

    selected_organizations = (

        request.form.getlist(
            "organizations"
        )
    )


    selected_organizations = list(

        dict.fromkeys(
            selected_organizations
        )
    )


    # ========================================================
    # VERIFY ORGANIZATIONS
    # ========================================================

    valid_organization_ids = []


    for organization_id in (
        selected_organizations
    ):

        cursor.execute("""
            SELECT

                organization_id


            FROM organizations


            WHERE organization_id = ?
        """, (
            organization_id,
        ))


        organization = (
            cursor.fetchone()
        )


        if organization is None:

            conn.close()

            return (
                "Invalid organization",
                400,
            )


        valid_organization_ids.append(
            organization_id
        )


    # ========================================================
    # REMOVE OLD LINKS
    # ========================================================

    cursor.execute("""
        DELETE FROM event_organizations

        WHERE event_id = ?
    """, (
        event_id,
    ))


    # ========================================================
    # INSERT NEW LINKS
    # ========================================================

    for organization_id in (
        valid_organization_ids
    ):

        cursor.execute("""
            INSERT INTO event_organizations (

                event_id,

                organization_id
            )

            VALUES (?, ?)
        """, (
            event_id,
            organization_id,
        ))


    conn.commit()

    conn.close()


    return redirect(

        url_for(

            "events.event_detail",

            event_id=event_id,
        )
    )


# ============================================================
# EDIT EVENT
# ACTIVE MANDATE ONLY
# ============================================================

@events_bp.route(
    "/events/<int:event_id>/edit",
    methods=[
        "GET",
        "POST",
    ],
)
@login_required
def edit_event(event_id):

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


    # ========================================================
    # GET ACTIVE EVENT
    # ========================================================

    cursor.execute("""
        SELECT

            event_id,

            term_id,

            event_leader_membership_id,

            title,

            description,

            event_date,

            end_date,

            start_time,

            end_time,

            location


        FROM events


        WHERE event_id = ?

          AND term_id = ?
    """, (
        event_id,
        active_term_id,
    ))


    event = cursor.fetchone()


    if event is None:

        conn.close()

        return (
            "Event not found",
            404,
        )


    # ========================================================
    # EDIT PERMISSION
    # ========================================================

    edit_deadline = (
        event_edit_deadline(
            event["end_date"]
        )
    )


    can_edit_event = (

        current_user[
            "membership_id"
        ]

        ==

        event[
            "event_leader_membership_id"
        ]

        and date.today()
        <= edit_deadline
    )


    if not can_edit_event:

        conn.close()

        return (
            "Access denied",
            403,
        )


    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":


        title = request.form.get(
            "title",
            "",
        ).strip()


        description = (
            request.form.get(
                "description",
                "",
            ).strip()
            or None
        )


        event_date = (
            request.form.get(
                "event_date"
            )
        )


        end_date = (
            request.form.get(
                "end_date"
            )
        )


        start_time = (
            request.form.get(
                "start_time"
            )
            or None
        )


        end_time = (
            request.form.get(
                "end_time"
            )
            or None
        )


        location = (
            request.form.get(
                "location",
                "",
            ).strip()
            or None
        )


        # ====================================================
        # VALIDATION
        # ====================================================

        if not title:

            conn.close()

            return (
                "Title is required",
                400,
            )


        if not event_date:

            conn.close()

            return (
                "Start date is required",
                400,
            )


        if not end_date:

            conn.close()

            return (
                "End date is required",
                400,
            )


        if end_date < event_date:

            conn.close()

            return (
                "End date cannot be before "
                "start date",
                400,
            )


        if (
            event_date == end_date
            and start_time
            and end_time
            and end_time < start_time
        ):

            conn.close()

            return (
                "End time cannot be before "
                "start time",
                400,
            )


        # ====================================================
        # UPDATE
        # ====================================================

        cursor.execute("""
            UPDATE events


            SET

                title = ?,

                description = ?,

                event_date = ?,

                end_date = ?,

                start_time = ?,

                end_time = ?,

                location = ?


            WHERE event_id = ?

              AND term_id = ?
        """, (

            title,

            description,

            event_date,

            end_date,

            start_time,

            end_time,

            location,

            event_id,

            active_term_id,
        ))


        conn.commit()

        conn.close()


        return redirect(

            url_for(

                "events.event_detail",

                event_id=event_id,
            )
        )


    conn.close()


    return render_template(

        "edit_event.html",

        event=event,

        edit_deadline=(
            edit_deadline
        ),
    )


# ============================================================
# DELETE EVENT
# HEAD RH ONLY
# ACTIVE MANDATE ONLY
# ============================================================

@events_bp.route(
    "/events/<int:event_id>/delete",
    methods=["POST"],
)
@login_required
def delete_event(event_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    # ========================================================
    # PERMISSION
    # ========================================================

    can_delete_event = (

        not current_user[
            "is_alumni"
        ]

        and current_user[
            "department_id"
        ]
        == HR_DEPARTMENT_ID

        and current_user[
            "role_name"
        ]
        == "HEAD"
    )


    if not can_delete_event:

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


    # ========================================================
    # VERIFY ACTIVE EVENT
    # ========================================================

    cursor.execute("""
        SELECT

            event_id


        FROM events


        WHERE event_id = ?

          AND term_id = ?
    """, (
        event_id,
        active_term_id,
    ))


    event = cursor.fetchone()


    if event is None:

        conn.close()

        return (
            "Event not found",
            404,
        )


    # ========================================================
    # DELETE EVENT ORGANIZATION LINKS
    # ========================================================

    cursor.execute("""
        DELETE FROM event_organizations

        WHERE event_id = ?
    """, (
        event_id,
    ))


    # ========================================================
    # DELETE DATABASE MEDIA
    # ========================================================

    cursor.execute("""
        DELETE FROM event_media

        WHERE event_id = ?
    """, (
        event_id,
    ))


    # ========================================================
    # DELETE DATABASE DOCUMENTS
    # ========================================================

    cursor.execute("""
        DELETE FROM event_documents

        WHERE event_id = ?
    """, (
        event_id,
    ))


    # ========================================================
    # DELETE EVENT
    # ========================================================

    cursor.execute("""
        DELETE FROM events

        WHERE event_id = ?

          AND term_id = ?
    """, (
        event_id,
        active_term_id,
    ))


    conn.commit()

    conn.close()


    # ========================================================
    # DELETE PHYSICAL MEDIA FOLDER
    # ========================================================

    media_folder = os.path.abspath(

        os.path.join(

            os.path.dirname(
                __file__
            ),

            "..",

            "uploads",

            "events",

            "media",

            str(event_id),
        )
    )


    if os.path.exists(
        media_folder
    ):

        shutil.rmtree(
            media_folder
        )


    # ========================================================
    # DELETE PHYSICAL DOCUMENTS FOLDER
    # ========================================================

    documents_folder = os.path.abspath(

        os.path.join(

            os.path.dirname(
                __file__
            ),

            "..",

            "uploads",

            "events",

            "documents",

            str(event_id),
        )
    )


    if os.path.exists(
        documents_folder
    ):

        shutil.rmtree(
            documents_folder
        )


    return redirect(

        url_for(
            "events.events"
        )
    )


# ============================================================
# EVENT ATTENDANCE SHEET
# RH ONLY
# ACTIVE MANDATE ONLY
# ============================================================

@events_bp.route(
    "/events/<int:event_id>/attendance-sheet"
)
@login_required
def event_attendance_sheet(
    event_id
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


    # ========================================================
    # PERMISSION
    # ========================================================

    if not is_hr_event_member(
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


    # ========================================================
    # VERIFY EVENT
    # ========================================================

    cursor.execute("""
        SELECT

            event_id,

            title,

            event_date,

            end_date


        FROM events


        WHERE event_id = ?

          AND term_id = ?
    """, (
        event_id,
        active_term_id,
    ))


    event = cursor.fetchone()

    conn.close()


    if event is None:

        return (
            "Event not found",
            404,
        )


    # ========================================================
    # FILE PATH
    # ========================================================

    file_path = os.path.join(

        os.path.dirname(
            __file__
        ),

        "..",

        "resources",

        "event_attendance_template.xlsx",
    )


    file_path = os.path.abspath(
        file_path
    )


    # ========================================================
    # DOWNLOAD NAME
    # ========================================================

    safe_title = "".join(

        character

        if (
            character.isalnum()

            or character
            in (
                " ",
                "-",
                "_",
            )
        )

        else "_"

        for character
        in event["title"]
    ).strip()


    download_name = (

        f"{safe_title}"
        f"_attendance.xlsx"
    )


    return send_file(

        file_path,

        as_attachment=True,

        download_name=(
            download_name
        ),
    )


# ============================================================
# UPLOAD EVENT MEDIA
# HEAD / SUB_HEAD DCM ONLY
# ACTIVE MANDATE ONLY
# ============================================================

@events_bp.route(
    "/events/<int:event_id>/media/upload",
    methods=["POST"],
)
@login_required
def upload_event_media(
    event_id
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


    # ========================================================
    # PERMISSION
    # ========================================================

    if not is_dcm_media_manager(
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


    # ========================================================
    # VERIFY ACTIVE EVENT
    # ========================================================

    cursor.execute("""
        SELECT

            event_id


        FROM events


        WHERE event_id = ?

          AND term_id = ?
    """, (
        event_id,
        active_term_id,
    ))


    if cursor.fetchone() is None:

        conn.close()

        return (
            "Event not found",
            404,
        )


    # ========================================================
    # FILE
    # ========================================================

    media_file = request.files.get(
        "media_file"
    )


    caption = (
        request.form.get(
            "caption",
            "",
        ).strip()
        or None
    )


    if (
        media_file is None
        or media_file.filename == ""
    ):

        conn.close()

        return (
            "Media file is required",
            400,
        )


    filename = secure_filename(
        media_file.filename
    )


    extension = (

        filename.rsplit(
            ".",
            1,
        )[-1].lower()

        if "." in filename

        else ""
    )


    if extension in (
        IMAGE_EXTENSIONS
    ):

        media_type = "image"


    elif extension in (
        VIDEO_EXTENSIONS
    ):

        media_type = "video"


    else:

        conn.close()

        return (
            "Unsupported media type",
            400,
        )


    # ========================================================
    # SAVE FILE
    # ========================================================

    unique_filename = (

        f"{uuid.uuid4().hex}"
        f"_{filename}"
    )


    upload_folder = os.path.abspath(

        os.path.join(

            os.path.dirname(
                __file__
            ),

            "..",

            "uploads",

            "events",

            "media",

            str(event_id),
        )
    )


    os.makedirs(

        upload_folder,

        exist_ok=True,
    )


    full_path = os.path.join(

        upload_folder,

        unique_filename,
    )


    media_file.save(
        full_path
    )


    relative_path = os.path.join(

        "uploads",

        "events",

        "media",

        str(event_id),

        unique_filename,
    )


    # ========================================================
    # DATABASE
    # ========================================================

    cursor.execute("""
        INSERT INTO event_media (

            event_id,

            media_type,

            file_path,

            caption
        )

        VALUES (
            ?,
            ?,
            ?,
            ?
        )
    """, (

        event_id,

        media_type,

        relative_path,

        caption,
    ))


    conn.commit()

    conn.close()


    return redirect(

        url_for(

            "events.event_detail",

            event_id=event_id,
        )
    )


# ============================================================
# TOGGLE EVENT MEDIA PUBLICATION
# HEAD DCM ONLY
# IMAGES ONLY
# ACTIVE MANDATE ONLY
# ============================================================

@events_bp.route(
    "/events/media/<int:event_media_id>/publication/toggle",
    methods=["POST"],
)
@login_required
def toggle_event_media_publication(
    event_media_id
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


    # ========================================================
    # PERMISSION
    # ========================================================

    if not is_dcm_media_publisher(
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


    # ========================================================
    # GET MEDIA
    # ACTIVE EVENT ONLY
    # ========================================================

    cursor.execute("""
        SELECT

            event_media.event_media_id,

            event_media.event_id,

            event_media.media_type,

            event_media.is_public


        FROM event_media


        JOIN events

            ON event_media.event_id =
               events.event_id


        WHERE event_media.event_media_id = ?

          AND events.term_id = ?
    """, (
        event_media_id,
        active_term_id,
    ))


    media = cursor.fetchone()


    if media is None:

        conn.close()

        return (
            "Media not found",
            404,
        )


    # ========================================================
    # IMAGES ONLY
    # ========================================================

    if (
        media["media_type"]
        != "image"
    ):

        conn.close()

        return (
            "Only images can be published "
            "on the public website.",
            400,
        )


    # ========================================================
    # TOGGLE
    # ========================================================

    new_status = (

        0

        if media[
            "is_public"
        ]

        else 1
    )


    cursor.execute("""
        UPDATE event_media

        SET is_public = ?

        WHERE event_media_id = ?
    """, (
        new_status,
        event_media_id,
    ))


    conn.commit()

    conn.close()


    return redirect(

        url_for(

            "events.event_detail",

            event_id=(
                media["event_id"]
            ),
        )
    )


# ============================================================
# VIEW EVENT MEDIA
# CURRENT MEMBERS ONLY
# ACTIVE + ARCHIVED EVENTS
# ============================================================

@events_bp.route(
    "/events/media/<int:event_media_id>"
)
@login_required
def view_event_media(
    event_media_id
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


    cursor.execute("""
        SELECT

            event_media.event_media_id,

            event_media.file_path


        FROM event_media


        JOIN events

            ON event_media.event_id =
               events.event_id


        JOIN terms

            ON events.term_id =
               terms.term_id


        WHERE event_media.event_media_id = ?

          AND terms.status IN (
              'ACTIVE',
              'ARCHIVED'
          )
    """, (
        event_media_id,
    ))


    media = cursor.fetchone()

    conn.close()


    if media is None:

        return (
            "Media not found",
            404,
        )


    file_path = os.path.abspath(

        os.path.join(

            os.path.dirname(
                __file__
            ),

            "..",

            media["file_path"],
        )
    )


    if not os.path.exists(
        file_path
    ):

        return (
            "Media file not found",
            404,
        )


    return send_file(
        file_path
    )


# ============================================================
# UPLOAD EVENT DOCUMENT
#
# EVENT LEADER OR HR
# ACTIVE MANDATE ONLY
# ============================================================

@events_bp.route(
    "/events/<int:event_id>/documents/upload",
    methods=["POST"],
)
@login_required
def upload_event_document(
    event_id
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


    # ========================================================
    # GET ACTIVE EVENT
    # ========================================================

    cursor.execute("""
        SELECT

            event_id,

            event_leader_membership_id,

            end_date


        FROM events


        WHERE event_id = ?

          AND term_id = ?
    """, (
        event_id,
        active_term_id,
    ))


    event = cursor.fetchone()


    if event is None:

        conn.close()

        return (
            "Event not found",
            404,
        )


    # ========================================================
    # PERMISSIONS
    # ========================================================

    upload_deadline = (
        event_edit_deadline(
            event["end_date"]
        )
    )


    is_event_leader = (

        current_user[
            "membership_id"
        ]

        ==

        event[
            "event_leader_membership_id"
        ]
    )


    is_hr_member = (

        is_hr_event_member(
            current_user
        )
    )


    can_upload_document = (

        date.today()
        <= upload_deadline

        and (

            is_event_leader

            or is_hr_member
        )
    )


    if not can_upload_document:

        conn.close()

        return (
            "Access denied",
            403,
        )


    # ========================================================
    # FORM DATA
    # ========================================================

    document_name = (
        request.form.get(
            "document_name",
            "",
        ).strip()
    )


    document_file = (
        request.files.get(
            "document_file"
        )
    )


    if not document_name:

        conn.close()

        return (
            "Document name is required",
            400,
        )


    if (
        document_file is None
        or document_file.filename == ""
    ):

        conn.close()

        return (
            "Document file is required",
            400,
        )


    # ========================================================
    # FILE EXTENSION
    # ========================================================

    filename = secure_filename(
        document_file.filename
    )


    extension = (

        filename.rsplit(
            ".",
            1,
        )[-1].lower()

        if "." in filename

        else ""
    )


    if extension not in (
        DOCUMENT_EXTENSIONS
    ):

        conn.close()

        return (
            "Unsupported document type",
            400,
        )


    # ========================================================
    # SAVE DOCUMENT
    # ========================================================

    unique_filename = (

        f"{uuid.uuid4().hex}"
        f"_{filename}"
    )


    upload_folder = os.path.abspath(

        os.path.join(

            os.path.dirname(
                __file__
            ),

            "..",

            "uploads",

            "events",

            "documents",

            str(event_id),
        )
    )


    os.makedirs(

        upload_folder,

        exist_ok=True,
    )


    full_path = os.path.join(

        upload_folder,

        unique_filename,
    )


    document_file.save(
        full_path
    )


    relative_path = os.path.join(

        "uploads",

        "events",

        "documents",

        str(event_id),

        unique_filename,
    )


    # ========================================================
    # DATABASE
    # ========================================================

    cursor.execute("""
        INSERT INTO event_documents (

            event_id,

            created_by_membership_id,

            document_name,

            file_path
        )

        VALUES (
            ?,
            ?,
            ?,
            ?
        )
    """, (

        event_id,

        current_user[
            "membership_id"
        ],

        document_name,

        relative_path,
    ))


    conn.commit()

    conn.close()


    return redirect(

        url_for(

            "events.event_detail",

            event_id=event_id,
        )
    )


# ============================================================
# DOWNLOAD EVENT DOCUMENT
# CURRENT MEMBERS ONLY
# ACTIVE + ARCHIVED EVENTS
# ============================================================

@events_bp.route(
    "/events/documents/<int:event_document_id>/download"
)
@login_required
def download_event_document(
    event_document_id
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


    # ========================================================
    # GET DOCUMENT
    # ========================================================

    cursor.execute("""
        SELECT

            event_documents.event_document_id,

            event_documents.event_id,

            event_documents.document_name,

            event_documents.file_path


        FROM event_documents


        JOIN events

            ON event_documents.event_id =
               events.event_id


        JOIN terms

            ON events.term_id =
               terms.term_id


        WHERE event_documents.event_document_id = ?

          AND terms.status IN (
              'ACTIVE',
              'ARCHIVED'
          )
    """, (
        event_document_id,
    ))


    document = cursor.fetchone()

    conn.close()


    if document is None:

        return (
            "Document not found",
            404,
        )


    # ========================================================
    # FILE PATH
    # ========================================================

    file_path = os.path.abspath(

        os.path.join(

            os.path.dirname(
                __file__
            ),

            "..",

            document[
                "file_path"
            ],
        )
    )


    if not os.path.exists(
        file_path
    ):

        return (
            "Document file not found",
            404,
        )


    # ========================================================
    # DOWNLOAD NAME
    # ========================================================

    original_extension = (
        os.path.splitext(
            file_path
        )[1]
    )


    download_name = (

        f"{document['document_name']}"

        f"{original_extension}"
    )


    # ========================================================
    # DOWNLOAD
    # ========================================================

    return send_file(

        file_path,

        as_attachment=True,

        download_name=(
            download_name
        ),
    )


# ============================================================
# DELETE EVENT DOCUMENT
# RH ONLY
# ACTIVE MANDATE ONLY
# ============================================================

@events_bp.route(
    "/events/documents/<int:event_document_id>/delete",
    methods=["POST"],
)
@login_required
def delete_event_document(
    event_document_id
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


    # ========================================================
    # PERMISSION
    # ========================================================

    if not is_hr_event_member(
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


    # ========================================================
    # GET DOCUMENT
    # ACTIVE EVENT ONLY
    # ========================================================

    cursor.execute("""
        SELECT

            event_documents.event_document_id,

            event_documents.event_id,

            event_documents.file_path


        FROM event_documents


        JOIN events

            ON event_documents.event_id =
               events.event_id


        WHERE event_documents.event_document_id = ?

          AND events.term_id = ?
    """, (
        event_document_id,
        active_term_id,
    ))


    document = cursor.fetchone()


    if document is None:

        conn.close()

        return (
            "Document not found",
            404,
        )


    event_id = (
        document["event_id"]
    )


    # ========================================================
    # DELETE PHYSICAL FILE
    # ========================================================

    file_path = os.path.abspath(

        os.path.join(

            os.path.dirname(
                __file__
            ),

            "..",

            document[
                "file_path"
            ],
        )
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

    cursor.execute("""
        DELETE FROM event_documents

        WHERE event_document_id = ?
    """, (
        event_document_id,
    ))


    conn.commit()

    conn.close()


    return redirect(

        url_for(

            "events.event_detail",

            event_id=event_id,
        )
    )


# ============================================================
# DELETE EVENT MEDIA
# HEAD / SUB_HEAD DCM ONLY
# ACTIVE MANDATE ONLY
# ============================================================

@events_bp.route(
    "/events/media/<int:event_media_id>/delete",
    methods=["POST"],
)
@login_required
def delete_event_media(
    event_media_id
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


    # ========================================================
    # PERMISSION
    # ========================================================

    if not is_dcm_media_manager(
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


    # ========================================================
    # GET MEDIA
    # ACTIVE EVENT ONLY
    # ========================================================

    cursor.execute("""
        SELECT

            event_media.event_media_id,

            event_media.event_id,

            event_media.file_path


        FROM event_media


        JOIN events

            ON event_media.event_id =
               events.event_id


        WHERE event_media.event_media_id = ?

          AND events.term_id = ?
    """, (
        event_media_id,
        active_term_id,
    ))


    media = cursor.fetchone()


    if media is None:

        conn.close()

        return (
            "Media not found",
            404,
        )


    event_id = (
        media["event_id"]
    )


    # ========================================================
    # DELETE PHYSICAL FILE
    # ========================================================

    file_path = os.path.abspath(

        os.path.join(

            os.path.dirname(
                __file__
            ),

            "..",

            media[
                "file_path"
            ],
        )
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

    cursor.execute("""
        DELETE FROM event_media

        WHERE event_media_id = ?
    """, (
        event_media_id,
    ))


    conn.commit()

    conn.close()


    return redirect(

        url_for(

            "events.event_detail",

            event_id=event_id,
        )
    )
