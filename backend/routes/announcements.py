from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
)

from context import get_active_term_id
from database import get_db_connection
from permissions import login_required
from routes.notifications import create_notification


announcements_bp = Blueprint(
    "announcements",
    __name__,
)


# ========================================
# CONSTANTS
# ========================================

HR_DEPARTMENT_ID = 1

PERSONALIZED_CREATOR_ROLES = (
    "HEAD",
    "SUB_HEAD",
)


# ========================================
# CURRENT MEMBER
# ========================================

def get_current_announcement_member(conn):

    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    # ========================================
    # CURRENT ACTIVE MEMBER
    # ========================================

    if active_term_id is not None:

        cursor.execute("""
            SELECT
                memberships.membership_id,
                memberships.term_id,
                memberships.person_id,
                memberships.department_id,
                roles.name AS role_name,

                CASE
                    WHEN roles.name = 'ALUMNI'
                    THEN 1
                    ELSE 0
                END AS is_alumni

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
        """, (
            session["user_id"],
            active_term_id,
        ))

        member = cursor.fetchone()

        if member is not None:
            return member

    # ========================================
    # ALUMNI / HISTORICAL USER
    # LATEST ARCHIVED MEMBERSHIP
    # ========================================

    cursor.execute("""
        SELECT
            memberships.membership_id,
            memberships.term_id,
            memberships.person_id,
            memberships.department_id,
            roles.name AS role_name,
            1 AS is_alumni

        FROM users

        JOIN memberships
            ON users.person_id =
               memberships.person_id

        JOIN roles
            ON memberships.role_id =
               roles.role_id

        JOIN terms
            ON memberships.term_id =
               terms.term_id

        WHERE users.user_id = ?
          AND terms.status = 'ARCHIVED'

        ORDER BY
            terms.end_date DESC

        LIMIT 1
    """, (
        session["user_id"],
    ))

    return cursor.fetchone()


# ========================================
# PERMISSION HELPERS
# ========================================

def is_hr_management(member):

    return (
        member is not None
        and not member["is_alumni"]
        and member["department_id"]
        == HR_DEPARTMENT_ID
        and member["role_name"]
        in PERSONALIZED_CREATOR_ROLES
    )


def can_delete_guest_message(member):

    return (
        member is not None
        and not member["is_alumni"]
        and (
            member["role_name"]
            in (
                "PRESIDENT",
                "VICE_PRESIDENT",
            )
            or (
                member["role_name"] == "HEAD"
                and member["department_id"]
                == HR_DEPARTMENT_ID
            )
        )
    )


def get_active_announcement(
    cursor,
    announcement_id,
    active_term_id,
):

    cursor.execute("""
        SELECT
            announcements.announcement_id,
            announcements.created_by_membership_id,
            announcements.title,
            announcements.message,
            announcements.visibility,
            announcements.status,
            announcements.created_at,
            announcements.updated_at,

            announcement_recipients.recipient_membership_id

        FROM announcements

        JOIN memberships AS creator_membership
            ON announcements.created_by_membership_id =
               creator_membership.membership_id

        LEFT JOIN announcement_recipients
            ON announcements.announcement_id =
               announcement_recipients.announcement_id

        WHERE announcements.announcement_id = ?
          AND creator_membership.term_id = ?

        LIMIT 1
    """, (
        announcement_id,
        active_term_id,
    ))

    return cursor.fetchone()


def get_available_recipients(
    cursor,
    current_member,
    active_term_id,
):

    if (
        current_member is None
        or current_member["is_alumni"]
        or current_member["role_name"]
        not in PERSONALIZED_CREATOR_ROLES
    ):
        return []

    current_membership_id = (
        current_member["membership_id"]
    )

    current_department_id = (
        current_member["department_id"]
    )

    # ========================================
    # HR HEAD / SUB_HEAD
    # ALL CURRENT MEMBERS
    # ========================================

    if is_hr_management(
        current_member
    ):

        cursor.execute("""
            SELECT
                memberships.membership_id,
                people.first_name,
                people.last_name,
                roles.name AS role_name,
                departments.name AS department_name

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

            LEFT JOIN departments
                ON memberships.department_id =
                   departments.department_id

            WHERE memberships.term_id = ?
              AND users.is_active = 1
              AND roles.name != 'ALUMNI'
              AND memberships.membership_id != ?

            ORDER BY
                people.last_name,
                people.first_name
        """, (
            active_term_id,
            current_membership_id,
        ))

    # ========================================
    # OTHER HEAD / SUB_HEAD
    # OWN DEPARTMENT ONLY
    # ========================================

    else:

        cursor.execute("""
            SELECT
                memberships.membership_id,
                people.first_name,
                people.last_name,
                roles.name AS role_name,
                departments.name AS department_name

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

            LEFT JOIN departments
                ON memberships.department_id =
                   departments.department_id

            WHERE memberships.term_id = ?
              AND memberships.department_id = ?
              AND users.is_active = 1
              AND roles.name != 'ALUMNI'
              AND memberships.membership_id != ?

            ORDER BY
                people.last_name,
                people.first_name
        """, (
            active_term_id,
            current_department_id,
            current_membership_id,
        ))

    return cursor.fetchall()


def verify_announcement_recipient(
    cursor,
    recipient_membership_id,
    current_member,
    active_term_id,
):

    cursor.execute("""
        SELECT
            memberships.membership_id,
            memberships.department_id,
            roles.name AS role_name,
            users.user_id

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
          AND roles.name != 'ALUMNI'

        LIMIT 1
    """, (
        recipient_membership_id,
        active_term_id,
    ))

    recipient = cursor.fetchone()

    if recipient is None:

        return (
            None,
            "Invalid recipient",
        )

    try:

        recipient_membership_id = int(
            recipient_membership_id
        )

    except (
        TypeError,
        ValueError,
    ):

        return (
            None,
            "Invalid recipient",
        )

    if (
        recipient_membership_id
        == current_member[
            "membership_id"
        ]
    ):

        return (
            None,
            "You cannot select yourself",
        )

    if (
        not is_hr_management(
            current_member
        )
        and recipient["department_id"]
        != current_member[
            "department_id"
        ]
    ):

        return (
            None,
            "Access denied",
        )

    return (
        recipient,
        None,
    )


# ========================================
# ANNOUNCEMENTS LIST
# ========================================

@announcements_bp.route(
    "/announcements"
)
@login_required
def announcements():

    conn = get_db_connection()
    cursor = conn.cursor()

    current_member = (
        get_current_announcement_member(
            conn
        )
    )

    if current_member is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    current_person_id = (
        current_member[
            "person_id"
        ]
    )

    delete_guest_permission = (
        can_delete_guest_message(
            current_member
        )
    )

    # ========================================
    # FILTERS
    # ========================================

    search_query = request.args.get(
        "q",
        "",
    ).strip()

    visibility_filter = request.args.get(
        "visibility",
        "all",
    )

    status_filter = request.args.get(
        "status",
        "all",
    )

    read_filter = request.args.get(
        "read",
        "all",
    )

    if visibility_filter not in (
        "all",
        "public",
        "personalized",
    ):

        visibility_filter = "all"

    if status_filter not in (
        "all",
        "active",
        "resolved",
    ):

        status_filter = "all"

    if read_filter not in (
        "all",
        "read",
        "unread",
    ):

        read_filter = "all"

    # ========================================
    # BASE QUERY
    # ACTIVE + ARCHIVED ONLY
    # ========================================

    query = """
        SELECT
            announcements.announcement_id,
            announcements.title,
            announcements.message,
            announcements.visibility,
            announcements.status,
            announcements.created_at,
            announcements.updated_at,

            announcements.created_by_membership_id
                AS creator_membership_id,

            creator_membership.person_id
                AS creator_person_id,

            creator_term.name
                AS creator_term_name,

            creator_term.status
                AS creator_term_status,

            creator_people.first_name
                AS creator_first_name,

            creator_people.last_name
                AS creator_last_name,

            announcement_recipients.recipient_membership_id,

            recipient_membership.person_id
                AS recipient_person_id,

            announcement_recipients.is_read,
            announcement_recipients.read_at,

            recipient_people.first_name
                AS recipient_first_name,

            recipient_people.last_name
                AS recipient_last_name

        FROM announcements

        JOIN memberships AS creator_membership
            ON announcements.created_by_membership_id =
               creator_membership.membership_id

        JOIN terms AS creator_term
            ON creator_membership.term_id =
               creator_term.term_id

        JOIN people AS creator_people
            ON creator_membership.person_id =
               creator_people.person_id

        LEFT JOIN announcement_recipients
            ON announcements.announcement_id =
               announcement_recipients.announcement_id

        LEFT JOIN memberships AS recipient_membership
            ON announcement_recipients.recipient_membership_id =
               recipient_membership.membership_id

        LEFT JOIN people AS recipient_people
            ON recipient_membership.person_id =
               recipient_people.person_id

        WHERE creator_term.status IN (
            'ACTIVE',
            'ARCHIVED'
        )

          AND (
                announcements.visibility = 'public'

                OR creator_membership.person_id = ?

                OR recipient_membership.person_id = ?
          )
    """

    params = [
        current_person_id,
        current_person_id,
    ]

    # ========================================
    # SEARCH
    # ========================================

    if search_query:

        search_pattern = (
            "%"
            + search_query.lower()
            + "%"
        )

        query += """
            AND (
                LOWER(
                    announcements.title
                ) LIKE ?

                OR LOWER(
                    announcements.message
                ) LIKE ?

                OR LOWER(
                    creator_people.first_name
                    || ' '
                    || creator_people.last_name
                ) LIKE ?

                OR LOWER(
                    COALESCE(
                        recipient_people.first_name,
                        ''
                    )
                    || ' '
                    ||
                    COALESCE(
                        recipient_people.last_name,
                        ''
                    )
                ) LIKE ?
            )
        """

        params.extend([
            search_pattern,
            search_pattern,
            search_pattern,
            search_pattern,
        ])

    # ========================================
    # VISIBILITY FILTER
    # ========================================

    if visibility_filter != "all":

        query += """
            AND announcements.visibility = ?
        """

        params.append(
            visibility_filter
        )

    # ========================================
    # STATUS FILTER
    # ========================================

    if status_filter != "all":

        query += """
            AND announcements.status = ?
        """

        params.append(
            status_filter
        )

    # ========================================
    # READ FILTER
    # ========================================

    if read_filter == "read":

        query += """
            AND announcements.visibility = 'personalized'
            AND announcement_recipients.is_read = 1
        """

    elif read_filter == "unread":

        query += """
            AND announcements.visibility = 'personalized'
            AND announcement_recipients.is_read = 0
        """

    # ========================================
    # ORDER
    # ========================================

    query += """
        ORDER BY
            announcements.created_at DESC
    """

    cursor.execute(
        query,
        params,
    )

    announcements_list = (
        cursor.fetchall()
    )

    # ========================================
    # GUEST MESSAGES
    # ========================================

    cursor.execute("""
        SELECT
            contact_message_id,
            sender_type,
            sender_email,
            message,
            is_read,
            created_at

        FROM contact_messages

        ORDER BY
            created_at DESC
    """)

    guest_messages = (
        cursor.fetchall()
    )

    conn.close()

    return render_template(
        "announcements.html",

        announcements=(
            announcements_list
        ),

        guest_messages=(
            guest_messages
        ),

        can_delete_guest_message=(
            delete_guest_permission
        ),

        search_query=(
            search_query
        ),

        visibility_filter=(
            visibility_filter
        ),

        status_filter=(
            status_filter
        ),

        read_filter=(
            read_filter
        ),
    )


# ========================================
# NEW ANNOUNCEMENT
# ACTIVE MANDATE ONLY
# ========================================

@announcements_bp.route(
    "/announcements/new",
    methods=[
        "GET",
        "POST",
    ],
)
@login_required
def new_announcement():

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

    current_member = (
        get_current_announcement_member(
            conn
        )
    )

    if current_member is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    if (
        current_member[
            "is_alumni"
        ]
        or current_member[
            "term_id"
        ]
        != active_term_id
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    current_membership_id = (
        current_member[
            "membership_id"
        ]
    )

    current_role = (
        current_member[
            "role_name"
        ]
    )

    can_create_personalized = (
        current_role
        in PERSONALIZED_CREATOR_ROLES
    )

    recipients = (
        get_available_recipients(
            cursor,
            current_member,
            active_term_id,
        )
    )

    # ========================================
    # CREATE
    # ========================================

    if request.method == "POST":

        title = request.form.get(
            "title",
            "",
        ).strip()

        message = request.form.get(
            "message",
            "",
        ).strip()

        visibility = request.form.get(
            "visibility",
            "public",
        ).strip()

        if not title or not message:

            conn.close()

            return (
                "Title and message are required",
                400,
            )

        if visibility not in (
            "public",
            "personalized",
        ):

            conn.close()

            return (
                "Invalid visibility",
                400,
            )

        if (
            visibility
            == "personalized"
            and not can_create_personalized
        ):

            conn.close()

            return (
                "Access denied",
                403,
            )

        # ====================================
        # PUBLIC
        # ====================================

        if visibility == "public":

            cursor.execute("""
                INSERT INTO announcements (
                    created_by_membership_id,
                    title,
                    message,
                    visibility,
                    status
                )

                VALUES (
                    ?,
                    ?,
                    ?,
                    'public',
                    'active'
                )
            """, (
                current_membership_id,
                title,
                message,
            ))

            announcement_id = (
                cursor.lastrowid
            )

            # Notify current active members only.

            cursor.execute("""
                SELECT DISTINCT
                    users.user_id

                FROM users

                JOIN memberships
                    ON users.person_id =
                       memberships.person_id

                JOIN roles
                    ON memberships.role_id =
                       roles.role_id

                WHERE users.is_active = 1

                  AND memberships.term_id = ?

                  AND roles.name != 'ALUMNI'

                  AND users.user_id != ?
            """, (
                active_term_id,
                session[
                    "user_id"
                ],
            ))

            users_to_notify = (
                cursor.fetchall()
            )

            for user in users_to_notify:

                create_notification(
                    recipient_user_id=(
                        user[
                            "user_id"
                        ]
                    ),
                    notification_type=(
                        "announcement"
                    ),
                    title=(
                        "New announcement"
                    ),
                    message=title,
                    target_url=(
                        f"/announcements/"
                        f"{announcement_id}"
                    ),
                    conn=conn,
                )

        # ====================================
        # PERSONALIZED
        # ====================================

        else:

            recipient_membership_id = (
                request.form.get(
                    "recipient_membership_id"
                )
            )

            if not recipient_membership_id:

                conn.close()

                return (
                    "Please select a recipient",
                    400,
                )

            recipient, error = (
                verify_announcement_recipient(
                    cursor,
                    recipient_membership_id,
                    current_member,
                    active_term_id,
                )
            )

            if recipient is None:

                conn.close()

                status_code = (
                    403
                    if error
                    == "Access denied"
                    else 400
                )

                return (
                    error,
                    status_code,
                )

            cursor.execute("""
                INSERT INTO announcements (
                    created_by_membership_id,
                    title,
                    message,
                    visibility,
                    status
                )

                VALUES (
                    ?,
                    ?,
                    ?,
                    'personalized',
                    'active'
                )
            """, (
                current_membership_id,
                title,
                message,
            ))

            announcement_id = (
                cursor.lastrowid
            )

            cursor.execute("""
                INSERT INTO announcement_recipients (
                    announcement_id,
                    recipient_membership_id
                )

                VALUES (?, ?)
            """, (
                announcement_id,
                recipient_membership_id,
            ))

            create_notification(
                recipient_user_id=(
                    recipient[
                        "user_id"
                    ]
                ),
                notification_type=(
                    "announcement"
                ),
                title=(
                    "New announcement"
                ),
                message=title,
                target_url=(
                    f"/announcements/"
                    f"{announcement_id}"
                ),
                conn=conn,
            )

        conn.commit()
        conn.close()

        return redirect(
            url_for(
                "announcements.announcements"
            )
        )

    conn.close()

    return render_template(
        "new_announcement.html",

        recipients=recipients,

        can_create_personalized=(
            can_create_personalized
        ),

        current_role=(
            current_role
        ),
    )


# ========================================
# ANNOUNCEMENT DETAIL
# ACTIVE + ARCHIVED
# ========================================

@announcements_bp.route(
    "/announcements/<int:announcement_id>"
)
@login_required
def announcement_detail(
    announcement_id
):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_member = (
        get_current_announcement_member(
            conn
        )
    )

    if current_member is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    current_person_id = (
        current_member[
            "person_id"
        ]
    )

    cursor.execute("""
        SELECT
            announcements.announcement_id,
            announcements.title,
            announcements.message,
            announcements.visibility,
            announcements.status,
            announcements.created_at,
            announcements.updated_at,

            announcements.created_by_membership_id,

            creator_membership.person_id
                AS creator_person_id,

            creator_term.name
                AS creator_term_name,

            creator_term.status
                AS creator_term_status,

            creator_people.first_name
                AS creator_first_name,

            creator_people.last_name
                AS creator_last_name,

            announcement_recipients.recipient_membership_id,

            recipient_membership.person_id
                AS recipient_person_id,

            recipient_people.first_name
                AS recipient_first_name,

            recipient_people.last_name
                AS recipient_last_name,

            announcement_recipients.is_read,

            announcement_recipients.read_at

        FROM announcements

        JOIN memberships AS creator_membership
            ON announcements.created_by_membership_id =
               creator_membership.membership_id

        JOIN terms AS creator_term
            ON creator_membership.term_id =
               creator_term.term_id

        JOIN people AS creator_people
            ON creator_membership.person_id =
               creator_people.person_id

        LEFT JOIN announcement_recipients
            ON announcements.announcement_id =
               announcement_recipients.announcement_id

        LEFT JOIN memberships AS recipient_membership
            ON announcement_recipients.recipient_membership_id =
               recipient_membership.membership_id

        LEFT JOIN people AS recipient_people
            ON recipient_membership.person_id =
               recipient_people.person_id

        WHERE announcements.announcement_id = ?

          AND creator_term.status IN (
              'ACTIVE',
              'ARCHIVED'
          )

        LIMIT 1
    """, (
        announcement_id,
    ))

    announcement = (
        cursor.fetchone()
    )

    if announcement is None:

        conn.close()

        return (
            "Announcement not found",
            404,
        )

    # ========================================
    # PERMISSION
    # ========================================

    is_creator = (
        announcement[
            "creator_person_id"
        ]
        == current_person_id
    )

    is_recipient = (
        announcement[
            "recipient_person_id"
        ]
        == current_person_id
    )

    if (
        announcement[
            "visibility"
        ]
        == "personalized"
        and not is_creator
        and not is_recipient
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    # ========================================
    # MARK PERSONALIZED MESSAGE AS READ
    # ========================================

    if (
        announcement[
            "visibility"
        ]
        == "personalized"
        and is_recipient
        and announcement[
            "is_read"
        ]
        == 0
    ):

        cursor.execute("""
            UPDATE announcement_recipients

            SET
                is_read = 1,
                read_at = CURRENT_TIMESTAMP

            WHERE announcement_id = ?
              AND recipient_membership_id = ?
        """, (
            announcement_id,
            announcement[
                "recipient_membership_id"
            ],
        ))

        conn.commit()
        conn.close()

        return redirect(
            url_for(
                "announcements.announcement_detail",
                announcement_id=(
                    announcement_id
                ),
            )
        )

    conn.close()

    return render_template(
        "announcement_detail.html",

        announcement=(
            announcement
        ),

        current_membership_id=(
            current_member[
                "membership_id"
            ]
        ),
    )


# ========================================
# UPDATE ANNOUNCEMENT STATUS
# ACTIVE MANDATE ONLY
# ========================================

@announcements_bp.route(
    "/announcements/<int:announcement_id>/status",
    methods=["POST"],
)
@login_required
def update_announcement_status(
    announcement_id
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

    current_member = (
        get_current_announcement_member(
            conn
        )
    )

    if (
        current_member is None
        or current_member[
            "is_alumni"
        ]
        or current_member[
            "term_id"
        ]
        != active_term_id
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    announcement = (
        get_active_announcement(
            cursor,
            announcement_id,
            active_term_id,
        )
    )

    if announcement is None:

        conn.close()

        return (
            "Announcement not found",
            404,
        )

    if (
        announcement[
            "created_by_membership_id"
        ]
        != current_member[
            "membership_id"
        ]
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    new_status = request.form.get(
        "status"
    )

    if new_status not in (
        "active",
        "resolved",
    ):

        conn.close()

        return (
            "Invalid status",
            400,
        )

    cursor.execute("""
        UPDATE announcements

        SET
            status = ?,
            updated_at = CURRENT_TIMESTAMP

        WHERE announcement_id = ?

          AND created_by_membership_id = ?
    """, (
        new_status,
        announcement_id,
        current_member[
            "membership_id"
        ],
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "announcements.announcement_detail",
            announcement_id=(
                announcement_id
            ),
        )
    )


# ========================================
# EDIT ANNOUNCEMENT
# ACTIVE MANDATE ONLY
# ========================================

@announcements_bp.route(
    "/announcements/<int:announcement_id>/edit",
    methods=[
        "GET",
        "POST",
    ],
)
@login_required
def edit_announcement(
    announcement_id
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

    current_member = (
        get_current_announcement_member(
            conn
        )
    )

    if (
        current_member is None
        or current_member[
            "is_alumni"
        ]
        or current_member[
            "term_id"
        ]
        != active_term_id
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    current_membership_id = (
        current_member[
            "membership_id"
        ]
    )

    current_role = (
        current_member[
            "role_name"
        ]
    )

    can_create_personalized = (
        current_role
        in PERSONALIZED_CREATOR_ROLES
    )

    # ========================================
    # GET ACTIVE ANNOUNCEMENT
    # ========================================

    announcement = (
        get_active_announcement(
            cursor,
            announcement_id,
            active_term_id,
        )
    )

    if announcement is None:

        conn.close()

        return (
            "Announcement not found",
            404,
        )

    if (
        announcement[
            "created_by_membership_id"
        ]
        != current_membership_id
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    recipients = (
        get_available_recipients(
            cursor,
            current_member,
            active_term_id,
        )
    )

    # ========================================
    # UPDATE
    # ========================================

    if request.method == "POST":

        title = request.form.get(
            "title",
            "",
        ).strip()

        message = request.form.get(
            "message",
            "",
        ).strip()

        visibility = request.form.get(
            "visibility",
            "public",
        ).strip()

        if not title or not message:

            conn.close()

            return (
                "Title and message are required",
                400,
            )

        if visibility not in (
            "public",
            "personalized",
        ):

            conn.close()

            return (
                "Invalid visibility",
                400,
            )

        if (
            visibility
            == "personalized"
            and not can_create_personalized
        ):

            conn.close()

            return (
                "Access denied",
                403,
            )

        # ====================================
        # PUBLIC
        # ====================================

        if visibility == "public":

            cursor.execute("""
                DELETE FROM announcement_recipients

                WHERE announcement_id = ?
            """, (
                announcement_id,
            ))

        # ====================================
        # PERSONALIZED
        # ====================================

        else:

            recipient_membership_id = (
                request.form.get(
                    "recipient_membership_id"
                )
            )

            if not recipient_membership_id:

                conn.close()

                return (
                    "Please select a recipient",
                    400,
                )

            recipient, error = (
                verify_announcement_recipient(
                    cursor,
                    recipient_membership_id,
                    current_member,
                    active_term_id,
                )
            )

            if recipient is None:

                conn.close()

                status_code = (
                    403
                    if error
                    == "Access denied"
                    else 400
                )

                return (
                    error,
                    status_code,
                )

            cursor.execute("""
                SELECT
                    recipient_membership_id

                FROM announcement_recipients

                WHERE announcement_id = ?
            """, (
                announcement_id,
            ))

            old_recipient = (
                cursor.fetchone()
            )

            # Public -> Personalized

            if old_recipient is None:

                cursor.execute("""
                    INSERT INTO announcement_recipients (
                        announcement_id,
                        recipient_membership_id,
                        is_read,
                        read_at
                    )

                    VALUES (
                        ?,
                        ?,
                        0,
                        NULL
                    )
                """, (
                    announcement_id,
                    recipient_membership_id,
                ))

            # Personalized -> different recipient

            elif (
                old_recipient[
                    "recipient_membership_id"
                ]
                != int(
                    recipient_membership_id
                )
            ):

                cursor.execute("""
                    UPDATE announcement_recipients

                    SET
                        recipient_membership_id = ?,
                        is_read = 0,
                        read_at = NULL

                    WHERE announcement_id = ?
                """, (
                    recipient_membership_id,
                    announcement_id,
                ))

        # ====================================
        # UPDATE MAIN ANNOUNCEMENT
        # ====================================

        cursor.execute("""
            UPDATE announcements

            SET
                title = ?,
                message = ?,
                visibility = ?,
                updated_at = CURRENT_TIMESTAMP

            WHERE announcement_id = ?

              AND created_by_membership_id = ?
        """, (
            title,
            message,
            visibility,
            announcement_id,
            current_membership_id,
        ))

        conn.commit()
        conn.close()

        return redirect(
            url_for(
                "announcements.announcement_detail",
                announcement_id=(
                    announcement_id
                ),
            )
        )

    conn.close()

    return render_template(
        "edit_announcement.html",

        announcement=(
            announcement
        ),

        recipients=(
            recipients
        ),

        can_create_personalized=(
            can_create_personalized
        ),
    )


# ========================================
# DELETE ANNOUNCEMENT
# ACTIVE MANDATE ONLY
# ========================================

@announcements_bp.route(
    "/announcements/<int:announcement_id>/delete",
    methods=["POST"],
)
@login_required
def delete_announcement(
    announcement_id
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

    current_member = (
        get_current_announcement_member(
            conn
        )
    )

    if (
        current_member is None
        or current_member[
            "is_alumni"
        ]
        or current_member[
            "term_id"
        ]
        != active_term_id
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    announcement = (
        get_active_announcement(
            cursor,
            announcement_id,
            active_term_id,
        )
    )

    if announcement is None:

        conn.close()

        return (
            "Announcement not found",
            404,
        )

    if (
        announcement[
            "created_by_membership_id"
        ]
        != current_member[
            "membership_id"
        ]
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    cursor.execute("""
        DELETE FROM announcement_recipients

        WHERE announcement_id = ?
    """, (
        announcement_id,
    ))

    cursor.execute("""
        DELETE FROM announcements

        WHERE announcement_id = ?

          AND created_by_membership_id = ?
    """, (
        announcement_id,
        current_member[
            "membership_id"
        ],
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "announcements.announcements"
        )
    )


# ========================================
# MARK GUEST MESSAGE AS READ
# CURRENT MEMBERS ONLY
# ========================================

@announcements_bp.route(
    "/announcements/guest-messages/<int:contact_message_id>/read",
    methods=["POST"],
)
@login_required
def mark_guest_message_read(
    contact_message_id
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

    current_member = (
        get_current_announcement_member(
            conn
        )
    )

    if (
        current_member is None
        or current_member[
            "is_alumni"
        ]
        or current_member[
            "term_id"
        ]
        != active_term_id
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    cursor.execute("""
        SELECT
            contact_message_id,
            is_read

        FROM contact_messages

        WHERE contact_message_id = ?
    """, (
        contact_message_id,
    ))

    guest_message = (
        cursor.fetchone()
    )

    if guest_message is None:

        conn.close()

        return (
            "Guest message not found",
            404,
        )

    cursor.execute("""
        UPDATE contact_messages

        SET is_read = 1

        WHERE contact_message_id = ?
    """, (
        contact_message_id,
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "announcements.announcements"
        )
        + "#guest-messages"
    )


# ========================================
# DELETE GUEST MESSAGE
# PRESIDENT / VP / HR HEAD ONLY
# ========================================

@announcements_bp.route(
    "/announcements/guest-messages/<int:contact_message_id>/delete",
    methods=["POST"],
)
@login_required
def delete_guest_message(
    contact_message_id
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

    current_member = (
        get_current_announcement_member(
            conn
        )
    )

    if (
        current_member is None
        or current_member[
            "is_alumni"
        ]
        or current_member[
            "term_id"
        ]
        != active_term_id
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    if not can_delete_guest_message(
        current_member
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    cursor.execute("""
        SELECT
            contact_message_id

        FROM contact_messages

        WHERE contact_message_id = ?
    """, (
        contact_message_id,
    ))

    guest_message = (
        cursor.fetchone()
    )

    if guest_message is None:

        conn.close()

        return (
            "Guest message not found",
            404,
        )

    cursor.execute("""
        DELETE FROM contact_messages

        WHERE contact_message_id = ?
    """, (
        contact_message_id,
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "announcements.announcements"
        )
        + "#guest-messages"
    )