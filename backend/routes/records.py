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

from werkzeug.utils import (
    secure_filename,
)

from context import (
    get_current_user,
)

from database import (
    get_db_connection,
)

from permissions import (
    login_required,
)


records_bp = Blueprint(
    "records",
    __name__,
)


ATTENDANCE_STATUSES = {
    "present",
    "absent",
    "late",
    "excused",
}


NOTE_TYPES = {
    "REMARK",
    "WARNING",
    "SANCTION",
    "POSITIVE",
}


SCHEDULE_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
}


CERTIFICATE_EXTENSIONS = {
    ".pdf",
}


# ============================================================
# PROTECT MODULE
# ============================================================

@records_bp.before_request
@login_required
def protect_records_module():

    pass


# ============================================================
# PERMISSIONS
# ============================================================

def is_platform_admin(user):

    return (
        user is not None
        and bool(
            user[
                "is_platform_admin"
            ]
        )
    )


def is_current_member(user):

    return (
        user is not None
        and not user[
            "is_alumni"
        ]
        and user[
            "membership_id"
        ]
        is not None
    )


def is_leadership(user):

    return (
        is_current_member(
            user
        )
        and user[
            "role_name"
        ]
        in {
            "PRESIDENT",
            "VICE_PRESIDENT",
            "SECRETARY_GENERAL",
            "HEAD",
            "SUB_HEAD",
        }
    )


def is_presidency_or_sg(user):

    return (
        is_current_member(
            user
        )
        and user[
            "role_name"
        ]
        in {
            "PRESIDENT",
            "VICE_PRESIDENT",
            "SECRETARY_GENERAL",
        }
    )


def is_hr_management(user):

    return (
        is_current_member(
            user
        )
        and user[
            "department_name"
        ]
        == "Human Resources"
        and user[
            "role_name"
        ]
        in {
            "HEAD",
            "SUB_HEAD",
        }
    )


def is_research_management(user):

    return (
        is_current_member(
            user
        )
        and user[
            "department_name"
        ]
        == "Research"
        and user[
            "role_name"
        ]
        in {
            "HEAD",
            "SUB_HEAD",
        }
    )


def can_view_records(user):

    return (
        is_current_member(
            user
        )
        or is_platform_admin(
            user
        )
    )


def can_manage_meetings(user):

    return (
        is_leadership(
            user
        )
        or is_platform_admin(
            user
        )
    )


def can_manage_attendance(user):

    return (
        is_leadership(
            user
        )
        or is_platform_admin(
            user
        )
    )


def can_manage_schedule(user):

    return (
        is_presidency_or_sg(
            user
        )
        or is_platform_admin(
            user
        )
    )


def can_manage_member_notes(user):

    return (
        is_hr_management(
            user
        )
        or is_presidency_or_sg(
            user
        )
        or is_platform_admin(
            user
        )
    )


def can_manage_certificates(user):

    return (
        is_leadership(
            user
        )
        or is_platform_admin(
            user
        )
    )


def can_manage_references(user):

    return (
        is_research_management(
            user
        )
        or is_presidency_or_sg(
            user
        )
        or is_platform_admin(
            user
        )
    )


def require_records_access(user):

    if not can_view_records(
        user
    ):

        return (
            "Access denied",
            403,
        )


    return None


# ============================================================
# GENERIC HELPERS
# ============================================================

def active_term(cursor):

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


    return (
        cursor.fetchone()
    )


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
        (
            term_id,
        ),
    )


    return (
        cursor.fetchone()
    )


def parse_date(
    value,
    label,
    required=False,
):

    value = (
        value
        or ""
    ).strip()


    if not value:

        if required:

            raise ValueError(
                f"{label} is required."
            )


        return None


    try:

        datetime.strptime(
            value,
            "%Y-%m-%d",
        )


    except ValueError as error:

        raise ValueError(
            f"Invalid {label}."
        ) from error


    return value


def normalize_optional(value):

    value = (
        value
        or ""
    ).strip()


    return (
        value
        or None
    )


def save_upload(
    file_storage,
    folder_name,
    allowed_extensions,
):

    if (
        file_storage is None
        or not file_storage.filename
    ):

        return (
            None,
            None,
        )


    original_filename = (
        secure_filename(
            file_storage.filename
        )
    )


    if not original_filename:

        raise ValueError(
            "Invalid filename."
        )


    extension = (
        os.path.splitext(
            original_filename
        )[1].lower()
    )


    if (
        extension
        not in allowed_extensions
    ):

        allowed = ", ".join(
            sorted(
                allowed_extensions
            )
        )


        raise ValueError(
            "Invalid file type. "
            f"Allowed: {allowed}"
        )


    stored_filename = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )


    folder = os.path.join(
        current_app.root_path,
        "uploads",
        "records",
        folder_name,
    )


    os.makedirs(
        folder,
        exist_ok=True,
    )


    file_storage.save(
        os.path.join(
            folder,
            stored_filename,
        )
    )


    return (
        stored_filename,
        original_filename,
    )


def delete_upload(
    folder_name,
    stored_filename,
):

    if not stored_filename:

        return


    safe_name = (
        os.path.basename(
            stored_filename
        )
    )


    folder = os.path.realpath(
        os.path.join(
            current_app.root_path,
            "uploads",
            "records",
            folder_name,
        )
    )


    path = os.path.realpath(
        os.path.join(
            folder,
            safe_name,
        )
    )


    try:

        if (
            os.path.commonpath(
                [
                    folder,
                    path,
                ]
            )
            != folder
        ):

            return


    except ValueError:

        return


    if os.path.isfile(
        path
    ):

        try:

            os.remove(
                path
            )

        except OSError:

            pass


def current_term_members(
    cursor,
    term_id,
):

    cursor.execute(
        """
        SELECT
            memberships.membership_id,
            memberships.person_id,

            people.first_name,
            people.last_name,

            roles.name
                AS role_name,

            departments.name
                AS department_name

        FROM memberships

        JOIN people

            ON people.person_id =
               memberships.person_id

        JOIN roles

            ON roles.role_id =
               memberships.role_id

        LEFT JOIN departments

            ON departments.department_id =
               memberships.department_id

        WHERE
            memberships.term_id = ?

          AND roles.name !=
              'ALUMNI'

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

                ELSE 6

            END,

            departments.name,

            people.first_name,

            people.last_name
        """,
        (
            term_id,
        ),
    )


    return (
        cursor.fetchall()
    )


def parse_attendance_form(
    members,
):

    result = []


    for member in members:

        membership_id = (
            member[
                "membership_id"
            ]
        )


        value = (
            request.form.get(
                f"status_{membership_id}",
                "",
            )
            .strip()
            .lower()
        )


        if not value:

            continue


        if (
            value
            not in ATTENDANCE_STATUSES
        ):

            raise ValueError(
                "Invalid attendance status."
            )


        result.append(
            (
                membership_id,
                value,
            )
        )


    return result


# ============================================================
# RECORDS HOME
# ============================================================

@records_bp.route(
    "/records"
)
def records_home():

    user = (
        get_current_user()
    )


    denied = (
        require_records_access(
            user
        )
    )


    if denied:

        return denied


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    term = (
        active_term(
            cursor
        )
    )


    counts = {

        "meetings":
            0,

        "events":
            0,

        "trainings":
            0,

        "certificates":
            0,

        "notes":
            0,

        "references":
            0,
    }


    if term:

        term_id = (
            term[
                "term_id"
            ]
        )


        counts[
            "meetings"
        ] = cursor.execute(
            """
            SELECT COUNT(*)

            FROM meetings

            WHERE term_id = ?
            """,
            (
                term_id,
            ),
        ).fetchone()[0]


        counts[
            "events"
        ] = cursor.execute(
            """
            SELECT COUNT(*)

            FROM events

            WHERE term_id = ?
            """,
            (
                term_id,
            ),
        ).fetchone()[0]


        counts[
            "trainings"
        ] = cursor.execute(
            """
            SELECT COUNT(*)

            FROM training_terms

            WHERE term_id = ?
            """,
            (
                term_id,
            ),
        ).fetchone()[0]


        counts[
            "certificates"
        ] = cursor.execute(
            """
            SELECT COUNT(*)

            FROM certificates

            WHERE term_id = ?
            """,
            (
                term_id,
            ),
        ).fetchone()[0]


        counts[
            "notes"
        ] = cursor.execute(
            """
            SELECT COUNT(*)

            FROM member_notes

            JOIN memberships

                ON memberships.membership_id =
                   member_notes.membership_id

            WHERE
                memberships.term_id = ?
            """,
            (
                term_id,
            ),
        ).fetchone()[0]


    counts[
        "references"
    ] = cursor.execute(
        """
        SELECT COUNT(*)

        FROM source_references
        """
    ).fetchone()[0]


    conn.close()


    return render_template(
        "records/index.html",

        term=term,

        counts=counts,

        can_manage_meetings=(
            can_manage_meetings(
                user
            )
        ),

        can_manage_attendance=(
            can_manage_attendance(
                user
            )
        ),

        can_manage_schedule=(
            can_manage_schedule(
                user
            )
        ),

        can_manage_member_notes=(
            can_manage_member_notes(
                user
            )
        ),

        can_manage_certificates=(
            can_manage_certificates(
                user
            )
        ),

        can_manage_references=(
            can_manage_references(
                user
            )
        ),
    )


# ============================================================
# MEETINGS
# ============================================================

@records_bp.route(
    "/records/meetings",
    methods=[
        "GET",
        "POST",
    ],
)
def meetings():

    user = (
        get_current_user()
    )


    denied = (
        require_records_access(
            user
        )
    )


    if denied:

        return denied


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    active = (
        active_term(
            cursor
        )
    )


    if active is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    error = None


    # ========================================================
    # CREATE
    # ========================================================

    if request.method == "POST":

        if not can_manage_meetings(
            user
        ):

            conn.close()

            return (
                "Access denied",
                403,
            )


        if not user[
            "membership_id"
        ]:

            conn.close()

            return (
                "A current membership is required "
                "to organize a meeting.",
                400,
            )


        try:

            title = (
                request.form.get(
                    "title",
                    "",
                ).strip()
            )


            if not title:

                raise ValueError(
                    "Meeting title is required."
                )


            meeting_date = (
                parse_date(
                    request.form.get(
                        "meeting_date"
                    ),
                    "meeting date",
                    True,
                )
            )


            start_time = (
                normalize_optional(
                    request.form.get(
                        "start_time"
                    )
                )
            )


            end_time = (
                normalize_optional(
                    request.form.get(
                        "end_time"
                    )
                )
            )


            if (
                start_time
                and end_time
                and end_time
                <= start_time
            ):

                raise ValueError(
                    "Meeting end time must "
                    "be after start time."
                )


            cursor.execute(
                """
                INSERT INTO meetings (

                    organizer_membership_id,

                    title,

                    description,

                    meeting_date,

                    start_time,

                    end_time,

                    location,

                    application_id,

                    term_id
                )

                VALUES (
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    ?,
                    NULL,
                    ?
                )
                """,
                (
                    user[
                        "membership_id"
                    ],

                    title,

                    normalize_optional(
                        request.form.get(
                            "description"
                        )
                    ),

                    meeting_date,

                    start_time,

                    end_time,

                    normalize_optional(
                        request.form.get(
                            "location"
                        )
                    ),

                    active[
                        "term_id"
                    ],
                ),
            )


            meeting_id = (
                cursor.lastrowid
            )


            conn.commit()

            conn.close()


            return redirect(
                url_for(
                    "records.meeting_detail",

                    meeting_id=(
                        meeting_id
                    ),
                )
            )


        except (
            ValueError,
            sqlite3.IntegrityError,
        ) as caught_error:

            conn.rollback()

            error = str(
                caught_error
            )


    # ========================================================
    # SELECT TERM
    # ========================================================

    selected_term_id = (

        request.args.get(
            "term_id",
            type=int,
        )
        or active[
            "term_id"
        ]
    )


    term = get_term(
        cursor,
        selected_term_id,
    )


    if term is None:

        term = active

        selected_term_id = (
            active[
                "term_id"
            ]
        )


    cursor.execute(
        """
        SELECT
            meetings.*,

            terms.name
                AS term_name,

            terms.status
                AS term_status,

            people.first_name
                AS organizer_first_name,

            people.last_name
                AS organizer_last_name,

            COUNT(
                meeting_attendance.meeting_attendance_id
            )
                AS attendance_count

        FROM meetings


        JOIN terms

            ON terms.term_id =
               meetings.term_id


        JOIN memberships

            ON memberships.membership_id =
               meetings.organizer_membership_id


        JOIN people

            ON people.person_id =
               memberships.person_id


        LEFT JOIN meeting_attendance

            ON meeting_attendance.meeting_id =
               meetings.meeting_id


        WHERE
            meetings.term_id = ?


        GROUP BY
            meetings.meeting_id


        ORDER BY
            meetings.meeting_date DESC,
            meetings.start_time DESC
        """,
        (
            selected_term_id,
        ),
    )


    meeting_rows = (
        cursor.fetchall()
    )


    cursor.execute(
        """
        SELECT
            term_id,
            name,
            status

        FROM terms

        WHERE status IN (
            'ACTIVE',
            'ARCHIVED'
        )

        ORDER BY
            start_date DESC
        """
    )


    terms = (
        cursor.fetchall()
    )


    conn.close()


    return render_template(
        "records/meetings.html",

        meetings=(
            meeting_rows
        ),

        term=term,

        terms=terms,

        active_term=active,

        error=error,

        can_manage=(
            can_manage_meetings(
                user
            )
        ),
    )


@records_bp.route(
    "/records/meetings/<int:meeting_id>",
    methods=[
        "GET",
        "POST",
    ],
)
def meeting_detail(
    meeting_id,
):

    user = (
        get_current_user()
    )


    denied = (
        require_records_access(
            user
        )
    )


    if denied:

        return denied


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    cursor.execute(
        """
        SELECT
            meetings.*,

            terms.name
                AS term_name,

            terms.status
                AS term_status,

            people.first_name
                AS organizer_first_name,

            people.last_name
                AS organizer_last_name

        FROM meetings


        JOIN terms

            ON terms.term_id =
               meetings.term_id


        JOIN memberships

            ON memberships.membership_id =
               meetings.organizer_membership_id


        JOIN people

            ON people.person_id =
               memberships.person_id


        WHERE
            meetings.meeting_id = ?
        """,
        (
            meeting_id,
        ),
    )


    meeting = (
        cursor.fetchone()
    )


    if meeting is None:

        conn.close()

        return (
            "Meeting not found",
            404,
        )


    error = None


    # ========================================================
    # UPDATE
    # ========================================================

    if request.method == "POST":

        if (
            not can_manage_meetings(
                user
            )
            or meeting[
                "term_status"
            ]
            != "ACTIVE"
        ):

            conn.close()

            return (
                "Access denied",
                403,
            )


        try:

            title = (
                request.form.get(
                    "title",
                    "",
                ).strip()
            )


            if not title:

                raise ValueError(
                    "Meeting title is required."
                )


            meeting_date = (
                parse_date(
                    request.form.get(
                        "meeting_date"
                    ),
                    "meeting date",
                    True,
                )
            )


            start_time = (
                normalize_optional(
                    request.form.get(
                        "start_time"
                    )
                )
            )


            end_time = (
                normalize_optional(
                    request.form.get(
                        "end_time"
                    )
                )
            )


            if (
                start_time
                and end_time
                and end_time
                <= start_time
            ):

                raise ValueError(
                    "Meeting end time must "
                    "be after start time."
                )


            cursor.execute(
                """
                UPDATE meetings

                SET
                    title = ?,

                    description = ?,

                    meeting_date = ?,

                    start_time = ?,

                    end_time = ?,

                    location = ?

                WHERE meeting_id = ?
                """,
                (
                    title,

                    normalize_optional(
                        request.form.get(
                            "description"
                        )
                    ),

                    meeting_date,

                    start_time,

                    end_time,

                    normalize_optional(
                        request.form.get(
                            "location"
                        )
                    ),

                    meeting_id,
                ),
            )


            conn.commit()


            return redirect(
                url_for(
                    "records.meeting_detail",

                    meeting_id=(
                        meeting_id
                    ),
                )
            )


        except (
            ValueError,
            sqlite3.IntegrityError,
        ) as caught_error:

            conn.rollback()

            error = str(
                caught_error
            )


    members = (
        current_term_members(
            cursor,
            meeting[
                "term_id"
            ],
        )
    )


    attendance_rows = (
        cursor.execute(
            """
            SELECT
                membership_id,
                attendance_status

            FROM meeting_attendance

            WHERE meeting_id = ?
            """,
            (
                meeting_id,
            ),
        ).fetchall()
    )


    attendance = {

        row[
            "membership_id"
        ]:
            row[
                "attendance_status"
            ]

        for row
        in attendance_rows

    }


    conn.close()


    return render_template(
        "records/meeting_detail.html",

        meeting=meeting,

        members=members,

        attendance=attendance,

        error=error,

        can_manage=(
            can_manage_meetings(
                user
            )
        ),

        can_manage_attendance=(
            can_manage_attendance(
                user
            )
        ),
    )


@records_bp.route(
    "/records/meetings/<int:meeting_id>/attendance",
    methods=[
        "POST",
    ],
)
def save_meeting_attendance(
    meeting_id,
):

    user = (
        get_current_user()
    )


    if not can_manage_attendance(
        user
    ):

        return (
            "Access denied",
            403,
        )


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    meeting = cursor.execute(
        """
        SELECT
            meetings.meeting_id,
            meetings.term_id,

            terms.status
                AS term_status

        FROM meetings

        JOIN terms

            ON terms.term_id =
               meetings.term_id

        WHERE
            meetings.meeting_id = ?
        """,
        (
            meeting_id,
        ),
    ).fetchone()


    if meeting is None:

        conn.close()

        return (
            "Meeting not found",
            404,
        )


    if (
        meeting[
            "term_status"
        ]
        != "ACTIVE"
    ):

        conn.close()

        return (
            "Archived attendance "
            "is read-only.",
            403,
        )


    members = (
        current_term_members(
            cursor,
            meeting[
                "term_id"
            ],
        )
    )


    try:

        entries = (
            parse_attendance_form(
                members
            )
        )


        cursor.execute(
            """
            DELETE FROM meeting_attendance

            WHERE meeting_id = ?
            """,
            (
                meeting_id,
            ),
        )


        cursor.executemany(
            """
            INSERT INTO meeting_attendance (
                meeting_id,
                membership_id,
                attendance_status
            )

            VALUES (?, ?, ?)
            """,

            [

                (
                    meeting_id,
                    membership_id,
                    status,
                )

                for (
                    membership_id,
                    status,
                )
                in entries

            ],
        )


        conn.commit()


    except (
        ValueError,
        sqlite3.IntegrityError,
    ) as error:

        conn.rollback()

        conn.close()


        return (
            str(error),
            400,
        )


    conn.close()


    return redirect(
        url_for(
            "records.meeting_detail",

            meeting_id=(
                meeting_id
            ),
        )
    )


@records_bp.route(
    "/records/meetings/<int:meeting_id>/delete",
    methods=[
        "POST",
    ],
)
def delete_meeting(
    meeting_id,
):

    user = (
        get_current_user()
    )


    if not can_manage_meetings(
        user
    ):

        return (
            "Access denied",
            403,
        )


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    meeting = cursor.execute(
        """
        SELECT
            meetings.meeting_id,

            terms.status
                AS term_status

        FROM meetings

        JOIN terms

            ON terms.term_id =
               meetings.term_id

        WHERE
            meetings.meeting_id = ?
        """,
        (
            meeting_id,
        ),
    ).fetchone()


    if meeting is None:

        conn.close()

        return (
            "Meeting not found",
            404,
        )


    if (
        meeting[
            "term_status"
        ]
        != "ACTIVE"
    ):

        conn.close()

        return (
            "Archived meeting "
            "is read-only.",
            403,
        )


    try:

        cursor.execute(
            """
            DELETE FROM meeting_attendance

            WHERE meeting_id = ?
            """,
            (
                meeting_id,
            ),
        )


        cursor.execute(
            """
            DELETE FROM meetings

            WHERE meeting_id = ?
            """,
            (
                meeting_id,
            ),
        )


        conn.commit()


    except sqlite3.IntegrityError as error:

        conn.rollback()

        conn.close()


        return (
            (
                "Meeting cannot "
                f"be deleted: {error}"
            ),
            400,
        )


    conn.close()


    return redirect(
        url_for(
            "records.meetings"
        )
    )


# ============================================================
# ATTENDANCE HUB
# ============================================================

@records_bp.route(
    "/records/attendance"
)
def attendance_hub():

    user = (
        get_current_user()
    )


    if not can_manage_attendance(
        user
    ):

        return (
            "Access denied",
            403,
        )


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    term = (
        active_term(
            cursor
        )
    )


    if term is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    term_id = (
        term[
            "term_id"
        ]
    )


    events = cursor.execute(
        """
        SELECT
            events.event_id
                AS item_id,

            events.title,

            events.event_date
                AS item_date,

            COUNT(
                event_attendance.event_attendance_id
            )
                AS attendance_count

        FROM events

        LEFT JOIN event_attendance

            ON event_attendance.event_id =
               events.event_id

        WHERE
            events.term_id = ?

        GROUP BY
            events.event_id

        ORDER BY
            events.event_date DESC
        """,
        (
            term_id,
        ),
    ).fetchall()


    trainings = cursor.execute(
        """
        SELECT
            trainings.training_id
                AS item_id,

            trainings.title,

            trainings.training_date
                AS item_date,

            COUNT(
                training_attendance.training_attendance_id
            )
                AS attendance_count

        FROM trainings

        JOIN training_terms

            ON training_terms.training_id =
               trainings.training_id

        LEFT JOIN training_attendance

            ON training_attendance.training_id =
               trainings.training_id

        WHERE
            training_terms.term_id = ?

        GROUP BY
            trainings.training_id

        ORDER BY
            trainings.training_date DESC,
            trainings.training_id DESC
        """,
        (
            term_id,
        ),
    ).fetchall()


    meetings_rows = cursor.execute(
        """
        SELECT
            meetings.meeting_id
                AS item_id,

            meetings.title,

            meetings.meeting_date
                AS item_date,

            COUNT(
                meeting_attendance.meeting_attendance_id
            )
                AS attendance_count

        FROM meetings

        LEFT JOIN meeting_attendance

            ON meeting_attendance.meeting_id =
               meetings.meeting_id

        WHERE
            meetings.term_id = ?

        GROUP BY
            meetings.meeting_id

        ORDER BY
            meetings.meeting_date DESC
        """,
        (
            term_id,
        ),
    ).fetchall()


    conn.close()


    return render_template(
        "records/attendance.html",

        term=term,

        events=events,

        trainings=trainings,

        meetings=(
            meetings_rows
        ),
    )


def attendance_resource(
    cursor,
    kind,
    item_id,
    active_term_id,
):

    if kind == "event":

        item = cursor.execute(
            """
            SELECT
                event_id
                    AS item_id,

                title,

                event_date
                    AS item_date,

                term_id

            FROM events

            WHERE
                event_id = ?

              AND term_id = ?
            """,
            (
                item_id,
                active_term_id,
            ),
        ).fetchone()


        return (
            item,
            "event_attendance",
            "event_id",
        )


    if kind == "training":

        item = cursor.execute(
            """
            SELECT
                trainings.training_id
                    AS item_id,

                trainings.title,

                trainings.training_date
                    AS item_date,

                training_terms.term_id

            FROM trainings

            JOIN training_terms

                ON training_terms.training_id =
                   trainings.training_id

            WHERE
                trainings.training_id = ?

              AND training_terms.term_id = ?
            """,
            (
                item_id,
                active_term_id,
            ),
        ).fetchone()


        return (
            item,
            "training_attendance",
            "training_id",
        )


    return (
        None,
        None,
        None,
    )


@records_bp.route(
    "/records/attendance/<string:kind>/<int:item_id>",
    methods=[
        "GET",
        "POST",
    ],
)
def attendance_detail(
    kind,
    item_id,
):

    user = (
        get_current_user()
    )


    if not can_manage_attendance(
        user
    ):

        return (
            "Access denied",
            403,
        )


    if kind not in {
        "event",
        "training",
    }:

        return (
            "Invalid attendance type",
            404,
        )


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    term = (
        active_term(
            cursor
        )
    )


    if term is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    (
        item,
        table_name,
        foreign_key,
    ) = attendance_resource(

        cursor,

        kind,

        item_id,

        term[
            "term_id"
        ],
    )


    if item is None:

        conn.close()

        return (
            "Attendance resource not found",
            404,
        )


    members = (
        current_term_members(
            cursor,
            term[
                "term_id"
            ],
        )
    )


    error = None


    if request.method == "POST":

        try:

            entries = (
                parse_attendance_form(
                    members
                )
            )


            cursor.execute(
                f"""
                DELETE FROM {table_name}

                WHERE {foreign_key} = ?
                """,
                (
                    item_id,
                ),
            )


            cursor.executemany(
                f"""
                INSERT INTO {table_name} (
                    {foreign_key},
                    membership_id,
                    attendance_status
                )

                VALUES (?, ?, ?)
                """,

                [

                    (
                        item_id,
                        membership_id,
                        status,
                    )

                    for (
                        membership_id,
                        status,
                    )
                    in entries

                ],
            )


            conn.commit()


            return redirect(
                url_for(
                    "records.attendance_detail",

                    kind=kind,

                    item_id=(
                        item_id
                    ),
                )
            )


        except (
            ValueError,
            sqlite3.IntegrityError,
        ) as caught_error:

            conn.rollback()

            error = str(
                caught_error
            )


    rows = cursor.execute(
        f"""
        SELECT
            membership_id,
            attendance_status

        FROM {table_name}

        WHERE {foreign_key} = ?
        """,
        (
            item_id,
        ),
    ).fetchall()


    attendance = {

        row[
            "membership_id"
        ]:
            row[
                "attendance_status"
            ]

        for row
        in rows

    }


    conn.close()


    return render_template(
        "records/attendance_detail.html",

        kind=kind,

        item=item,

        term=term,

        members=members,

        attendance=attendance,

        error=error,
    )


# ============================================================
# ANNUAL SCHEDULE
# ============================================================

@records_bp.route(
    "/records/schedule",
    methods=[
        "GET",
        "POST",
    ],
)
def annual_schedule():

    user = (
        get_current_user()
    )


    denied = (
        require_records_access(
            user
        )
    )


    if denied:

        return denied


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    term = (
        active_term(
            cursor
        )
    )


    if term is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    error = None

    new_file = None

    old_file_to_delete = None


    if request.method == "POST":

        if not can_manage_schedule(
            user
        ):

            conn.close()

            return (
                "Access denied",
                403,
            )


        if not user[
            "membership_id"
        ]:

            conn.close()

            return (
                (
                    "A current membership "
                    "is required to publish "
                    "the annual schedule."
                ),
                400,
            )


        try:

            title = (
                request.form.get(
                    "title",
                    "",
                ).strip()
            )


            if not title:

                raise ValueError(
                    "Schedule title is required."
                )


            existing = cursor.execute(
                """
                SELECT *

                FROM annual_schedule

                WHERE term_id = ?
                """,
                (
                    term[
                        "term_id"
                    ],
                ),
            ).fetchone()


            (
                new_file,
                new_original,
            ) = save_upload(

                request.files.get(
                    "schedule_file"
                ),

                "schedules",

                SCHEDULE_EXTENSIONS,
            )


            final_file = (

                new_file

                or (

                    existing[
                        "file_path"
                    ]

                    if existing

                    else None
                )
            )


            final_original = (

                new_original

                or (

                    existing[
                        "original_filename"
                    ]

                    if existing

                    else None
                )
            )


            if existing:

                cursor.execute(
                    """
                    UPDATE annual_schedule

                    SET
                        title = ?,

                        description = ?,

                        file_path = ?,

                        original_filename = ?

                    WHERE
                        annual_schedule_id = ?
                    """,
                    (
                        title,

                        normalize_optional(
                            request.form.get(
                                "description"
                            )
                        ),

                        final_file,

                        final_original,

                        existing[
                            "annual_schedule_id"
                        ],
                    ),
                )


                if (
                    new_file
                    and existing[
                        "file_path"
                    ]
                    and existing[
                        "file_path"
                    ]
                    != new_file
                ):

                    old_file_to_delete = (
                        existing[
                            "file_path"
                        ]
                    )


            else:

                cursor.execute(
                    """
                    INSERT INTO annual_schedule (

                        term_id,

                        created_by_membership_id,

                        title,

                        description,

                        file_path,

                        original_filename
                    )

                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        term[
                            "term_id"
                        ],

                        user[
                            "membership_id"
                        ],

                        title,

                        normalize_optional(
                            request.form.get(
                                "description"
                            )
                        ),

                        final_file,

                        final_original,
                    ),
                )


            conn.commit()


            if old_file_to_delete:

                delete_upload(
                    "schedules",
                    old_file_to_delete,
                )


            return redirect(
                url_for(
                    "records.annual_schedule"
                )
            )


        except (
            ValueError,
            sqlite3.IntegrityError,
            OSError,
        ) as caught_error:

            conn.rollback()


            if new_file:

                delete_upload(
                    "schedules",
                    new_file,
                )


            error = str(
                caught_error
            )


    schedules = cursor.execute(
        """
        SELECT
            annual_schedule.*,

            terms.name
                AS term_name,

            terms.status
                AS term_status,

            people.first_name,

            people.last_name

        FROM annual_schedule


        JOIN terms

            ON terms.term_id =
               annual_schedule.term_id


        JOIN memberships

            ON memberships.membership_id =
               annual_schedule.created_by_membership_id


        JOIN people

            ON people.person_id =
               memberships.person_id


        ORDER BY
            terms.start_date DESC
        """
    ).fetchall()


    current_schedule = next(

        (

            row

            for row in schedules

            if row[
                "term_id"
            ]
            == term[
                "term_id"
            ]

        ),

        None,
    )


    conn.close()


    return render_template(
        "records/schedule.html",

        term=term,

        schedules=schedules,

        current_schedule=(
            current_schedule
        ),

        error=error,

        can_manage=(
            can_manage_schedule(
                user
            )
        ),
    )


@records_bp.route(
    "/records/schedule/<int:schedule_id>/file"
)
def annual_schedule_file(
    schedule_id,
):

    user = (
        get_current_user()
    )


    denied = (
        require_records_access(
            user
        )
    )


    if denied:

        return denied


    conn = (
        get_db_connection()
    )


    row = conn.execute(
        """
        SELECT
            file_path,
            original_filename

        FROM annual_schedule

        WHERE
            annual_schedule_id = ?
        """,
        (
            schedule_id,
        ),
    ).fetchone()


    conn.close()


    if (
        row is None
        or not row[
            "file_path"
        ]
    ):

        return (
            "Schedule file not found",
            404,
        )


    folder = os.path.join(
        current_app.root_path,
        "uploads",
        "records",
        "schedules",
    )


    return send_from_directory(
        folder,

        os.path.basename(
            row[
                "file_path"
            ]
        ),

        as_attachment=True,

        download_name=(

            row[
                "original_filename"
            ]

            or os.path.basename(
                row[
                    "file_path"
                ]
            )
        ),
    )


@records_bp.route(
    "/records/schedule/<int:schedule_id>/delete",
    methods=[
        "POST",
    ],
)
def delete_annual_schedule(
    schedule_id,
):

    user = (
        get_current_user()
    )


    if not can_manage_schedule(
        user
    ):

        return (
            "Access denied",
            403,
        )


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    row = cursor.execute(
        """
        SELECT
            annual_schedule.*,

            terms.status
                AS term_status

        FROM annual_schedule

        JOIN terms

            ON terms.term_id =
               annual_schedule.term_id

        WHERE
            annual_schedule_id = ?
        """,
        (
            schedule_id,
        ),
    ).fetchone()


    if row is None:

        conn.close()

        return (
            "Schedule not found",
            404,
        )


    if (
        row[
            "term_status"
        ]
        != "ACTIVE"
    ):

        conn.close()

        return (
            "Archived schedule "
            "is read-only.",
            403,
        )


    cursor.execute(
        """
        DELETE FROM annual_schedule

        WHERE annual_schedule_id = ?
        """,
        (
            schedule_id,
        ),
    )


    conn.commit()

    conn.close()


    delete_upload(
        "schedules",
        row[
            "file_path"
        ],
    )


    return redirect(
        url_for(
            "records.annual_schedule"
        )
    )


# ============================================================
# MEMBER NOTES
# ============================================================

@records_bp.route(
    "/records/member-notes",
    methods=[
        "GET",
        "POST",
    ],
)
def member_notes():

    user = (
        get_current_user()
    )


    if not can_manage_member_notes(
        user
    ):

        return (
            "Access denied",
            403,
        )


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    term = (
        active_term(
            cursor
        )
    )


    if term is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    error = None


    if request.method == "POST":

        if not user[
            "membership_id"
        ]:

            conn.close()

            return (
                (
                    "A current membership "
                    "is required to add "
                    "a member note."
                ),
                400,
            )


        try:

            membership_id = int(
                request.form.get(
                    "membership_id",
                    "",
                )
            )


            note_type = (
                request.form.get(
                    "note_type",
                    "REMARK",
                )
                .strip()
                .upper()
            )


            note = (
                request.form.get(
                    "note",
                    "",
                ).strip()
            )


            if (
                note_type
                not in NOTE_TYPES
            ):

                raise ValueError(
                    "Invalid note type."
                )


            if not note:

                raise ValueError(
                    "Note text is required."
                )


            target = cursor.execute(
                """
                SELECT
                    membership_id

                FROM memberships

                WHERE
                    membership_id = ?

                  AND term_id = ?
                """,
                (
                    membership_id,

                    term[
                        "term_id"
                    ],
                ),
            ).fetchone()


            if target is None:

                raise ValueError(
                    (
                        "Selected member "
                        "is not part of "
                        "the active mandate."
                    )
                )


            cursor.execute(
                """
                INSERT INTO member_notes (
                    membership_id,
                    given_by_membership_id,
                    note,
                    note_type
                )

                VALUES (?, ?, ?, ?)
                """,
                (
                    membership_id,

                    user[
                        "membership_id"
                    ],

                    note,

                    note_type,
                ),
            )


            conn.commit()


            return redirect(
                url_for(
                    "records.member_notes"
                )
            )


        except (
            ValueError,
            sqlite3.IntegrityError,
        ) as caught_error:

            conn.rollback()

            error = str(
                caught_error
            )


    members = (
        current_term_members(
            cursor,
            term[
                "term_id"
            ],
        )
    )


    selected_membership_id = (
        request.args.get(
            "membership_id",
            type=int,
        )
    )


    params = [
        term[
            "term_id"
        ]
    ]


    extra = ""


    if selected_membership_id:

        extra = (
            "AND member_notes."
            "membership_id = ?"
        )

        params.append(
            selected_membership_id
        )


    notes = cursor.execute(
        f"""
        SELECT
            member_notes.*,

            target_person.first_name
                AS target_first_name,

            target_person.last_name
                AS target_last_name,

            giver_person.first_name
                AS giver_first_name,

            giver_person.last_name
                AS giver_last_name

        FROM member_notes


        JOIN memberships
            AS target_membership

            ON target_membership.membership_id =
               member_notes.membership_id


        JOIN people
            AS target_person

            ON target_person.person_id =
               target_membership.person_id


        JOIN memberships
            AS giver_membership

            ON giver_membership.membership_id =
               member_notes.given_by_membership_id


        JOIN people
            AS giver_person

            ON giver_person.person_id =
               giver_membership.person_id


        WHERE
            target_membership.term_id = ?

            {extra}


        ORDER BY
            member_notes.created_at DESC,
            member_notes.member_note_id DESC
        """,
        params,
    ).fetchall()


    conn.close()


    return render_template(
        "records/member_notes.html",

        term=term,

        members=members,

        notes=notes,

        selected_membership_id=(
            selected_membership_id
        ),

        error=error,

        note_types=(
            sorted(
                NOTE_TYPES
            )
        ),
    )


@records_bp.route(
    "/records/member-notes/<int:note_id>/delete",
    methods=[
        "POST",
    ],
)
def delete_member_note(
    note_id,
):

    user = (
        get_current_user()
    )


    if not can_manage_member_notes(
        user
    ):

        return (
            "Access denied",
            403,
        )


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    row = cursor.execute(
        """
        SELECT
            member_notes.member_note_id,

            terms.status
                AS term_status

        FROM member_notes

        JOIN memberships

            ON memberships.membership_id =
               member_notes.membership_id

        JOIN terms

            ON terms.term_id =
               memberships.term_id

        WHERE
            member_notes.member_note_id = ?
        """,
        (
            note_id,
        ),
    ).fetchone()


    if row is None:

        conn.close()

        return (
            "Member note not found",
            404,
        )


    if (
        row[
            "term_status"
        ]
        != "ACTIVE"
    ):

        conn.close()

        return (
            "Archived member note "
            "is read-only.",
            403,
        )


    cursor.execute(
        """
        DELETE FROM member_notes

        WHERE member_note_id = ?
        """,
        (
            note_id,
        ),
    )


    conn.commit()

    conn.close()


    return redirect(
        url_for(
            "records.member_notes"
        )
    )


# ============================================================
# CERTIFICATES
# ============================================================

@records_bp.route(
    "/records/certificates",
    methods=[
        "GET",
        "POST",
    ],
)
def certificates():

    user = (
        get_current_user()
    )


    denied = (
        require_records_access(
            user
        )
    )


    if denied:

        return denied


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    active = (
        active_term(
            cursor
        )
    )


    if active is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    error = None

    new_file = None


    if request.method == "POST":

        if not can_manage_certificates(
            user
        ):

            conn.close()

            return (
                "Access denied",
                403,
            )


        try:

            name = (
                request.form.get(
                    "name",
                    "",
                ).strip()
            )


            if not name:

                raise ValueError(
                    "Certificate name is required."
                )


            issued_date = (
                parse_date(
                    request.form.get(
                        "issued_date"
                    ),
                    "issued date",
                    False,
                )
            )


            recipient_ids = []


            for raw in request.form.getlist(
                "recipient_ids"
            ):

                try:

                    recipient_ids.append(
                        int(raw)
                    )

                except ValueError as error_parse:

                    raise ValueError(
                        "Invalid certificate recipient."
                    ) from error_parse


            recipient_ids = sorted(
                set(
                    recipient_ids
                )
            )


            if not recipient_ids:

                raise ValueError(
                    (
                        "Select at least "
                        "one certificate recipient."
                    )
                )


            placeholders = ",".join(
                "?"
                for _ in recipient_ids
            )


            valid_people = cursor.execute(
                f"""
                SELECT person_id

                FROM people

                WHERE
                    person_id IN (
                        {placeholders}
                    )
                """,
                recipient_ids,
            ).fetchall()


            if (
                len(
                    valid_people
                )
                != len(
                    recipient_ids
                )
            ):

                raise ValueError(
                    (
                        "One or more "
                        "certificate recipients "
                        "do not exist."
                    )
                )


            (
                new_file,
                original_filename,
            ) = save_upload(

                request.files.get(
                    "certificate_file"
                ),

                "certificates",

                CERTIFICATE_EXTENSIONS,
            )


            cursor.execute(
                """
                INSERT INTO certificates (

                    name,

                    description,

                    certificate_type,

                    issued_date,

                    file_path,

                    term_id,

                    created_by_membership_id,

                    original_filename
                )

                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,

                    normalize_optional(
                        request.form.get(
                            "description"
                        )
                    ),

                    normalize_optional(
                        request.form.get(
                            "certificate_type"
                        )
                    ),

                    issued_date,

                    new_file,

                    active[
                        "term_id"
                    ],

                    user[
                        "membership_id"
                    ],

                    original_filename,
                ),
            )


            certificate_id = (
                cursor.lastrowid
            )


            cursor.executemany(
                """
                INSERT INTO certificate_recipients (
                    certificate_id,
                    person_id
                )

                VALUES (?, ?)
                """,

                [

                    (
                        certificate_id,
                        person_id,
                    )

                    for person_id
                    in recipient_ids

                ],
            )


            conn.commit()

            conn.close()


            return redirect(
                url_for(
                    "records.certificate_detail",

                    certificate_id=(
                        certificate_id
                    ),
                )
            )


        except (
            ValueError,
            sqlite3.IntegrityError,
            OSError,
        ) as caught_error:

            conn.rollback()


            if new_file:

                delete_upload(
                    "certificates",
                    new_file,
                )


            error = str(
                caught_error
            )


    selected_term_id = (

        request.args.get(
            "term_id",
            type=int,
        )
        or active[
            "term_id"
        ]
    )


    selected_term = (

        get_term(
            cursor,
            selected_term_id,
        )
        or active
    )


    selected_term_id = (
        selected_term[
            "term_id"
        ]
    )


    rows = cursor.execute(
        """
        SELECT
            certificates.*,

            terms.name
                AS term_name,

            terms.status
                AS term_status,

            COUNT(
                certificate_recipients.certificate_recipient_id
            )
                AS recipient_count

        FROM certificates


        JOIN terms

            ON terms.term_id =
               certificates.term_id


        LEFT JOIN certificate_recipients

            ON certificate_recipients.certificate_id =
               certificates.certificate_id


        WHERE
            certificates.term_id = ?


        GROUP BY
            certificates.certificate_id


        ORDER BY
            certificates.issued_date DESC,
            certificates.certificate_id DESC
        """,
        (
            selected_term_id,
        ),
    ).fetchall()


    terms = cursor.execute(
        """
        SELECT
            term_id,
            name,
            status

        FROM terms

        WHERE status IN (
            'ACTIVE',
            'ARCHIVED'
        )

        ORDER BY
            start_date DESC
        """
    ).fetchall()


    people = cursor.execute(
        """
        SELECT
            person_id,
            first_name,
            last_name,
            email

        FROM people

        ORDER BY
            first_name,
            last_name
        """
    ).fetchall()


    conn.close()


    return render_template(
        "records/certificates.html",

        certificates=rows,

        term=selected_term,

        active_term=active,

        terms=terms,

        people=people,

        error=error,

        can_manage=(
            can_manage_certificates(
                user
            )
        ),
    )


@records_bp.route(
    "/records/certificates/<int:certificate_id>",
    methods=[
        "GET",
        "POST",
    ],
)
def certificate_detail(
    certificate_id,
):

    user = (
        get_current_user()
    )


    denied = (
        require_records_access(
            user
        )
    )


    if denied:

        return denied


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    certificate = cursor.execute(
        """
        SELECT
            certificates.*,

            terms.name
                AS term_name,

            terms.status
                AS term_status

        FROM certificates

        JOIN terms

            ON terms.term_id =
               certificates.term_id

        WHERE
            certificate_id = ?
        """,
        (
            certificate_id,
        ),
    ).fetchone()


    if certificate is None:

        conn.close()

        return (
            "Certificate not found",
            404,
        )


    error = None

    new_file = None

    old_file_to_delete = None


    if request.method == "POST":

        if (
            not can_manage_certificates(
                user
            )
            or certificate[
                "term_status"
            ]
            != "ACTIVE"
        ):

            conn.close()

            return (
                "Access denied",
                403,
            )


        try:

            name = (
                request.form.get(
                    "name",
                    "",
                ).strip()
            )


            if not name:

                raise ValueError(
                    "Certificate name is required."
                )


            recipient_ids = sorted(
                {

                    int(raw)

                    for raw
                    in request.form.getlist(
                        "recipient_ids"
                    )

                }
            )


            if not recipient_ids:

                raise ValueError(
                    (
                        "Select at least one "
                        "certificate recipient."
                    )
                )


            placeholders = ",".join(
                "?"
                for _ in recipient_ids
            )


            valid_count = cursor.execute(
                f"""
                SELECT COUNT(*)

                FROM people

                WHERE person_id
                    IN (
                        {placeholders}
                    )
                """,
                recipient_ids,
            ).fetchone()[0]


            if (
                valid_count
                != len(
                    recipient_ids
                )
            ):

                raise ValueError(
                    (
                        "One or more "
                        "certificate recipients "
                        "do not exist."
                    )
                )


            (
                new_file,
                new_original,
            ) = save_upload(

                request.files.get(
                    "certificate_file"
                ),

                "certificates",

                CERTIFICATE_EXTENSIONS,
            )


            final_file = (

                new_file

                or certificate[
                    "file_path"
                ]
            )


            final_original = (

                new_original

                or certificate[
                    "original_filename"
                ]
            )


            cursor.execute(
                """
                UPDATE certificates

                SET
                    name = ?,

                    description = ?,

                    certificate_type = ?,

                    issued_date = ?,

                    file_path = ?,

                    original_filename = ?

                WHERE
                    certificate_id = ?
                """,
                (
                    name,

                    normalize_optional(
                        request.form.get(
                            "description"
                        )
                    ),

                    normalize_optional(
                        request.form.get(
                            "certificate_type"
                        )
                    ),

                    parse_date(
                        request.form.get(
                            "issued_date"
                        ),
                        "issued date",
                        False,
                    ),

                    final_file,

                    final_original,

                    certificate_id,
                ),
            )


            cursor.execute(
                """
                DELETE FROM certificate_recipients

                WHERE certificate_id = ?
                """,
                (
                    certificate_id,
                ),
            )


            cursor.executemany(
                """
                INSERT INTO certificate_recipients (
                    certificate_id,
                    person_id
                )

                VALUES (?, ?)
                """,

                [

                    (
                        certificate_id,
                        person_id,
                    )

                    for person_id
                    in recipient_ids

                ],
            )


            conn.commit()


            if (
                new_file
                and certificate[
                    "file_path"
                ]
                and certificate[
                    "file_path"
                ]
                != new_file
            ):

                old_file_to_delete = (
                    certificate[
                        "file_path"
                    ]
                )


            if old_file_to_delete:

                delete_upload(
                    "certificates",
                    old_file_to_delete,
                )


            return redirect(
                url_for(
                    "records.certificate_detail",

                    certificate_id=(
                        certificate_id
                    ),
                )
            )


        except (
            ValueError,
            sqlite3.IntegrityError,
            OSError,
        ) as caught_error:

            conn.rollback()


            if new_file:

                delete_upload(
                    "certificates",
                    new_file,
                )


            error = str(
                caught_error
            )


    recipients = cursor.execute(
        """
        SELECT
            certificate_recipients.person_id,

            certificate_recipients.recipient_name_snapshot,

            people.first_name,

            people.last_name,

            people.email

        FROM certificate_recipients

        JOIN people

            ON people.person_id =
               certificate_recipients.person_id

        WHERE
            certificate_recipients.certificate_id = ?

        ORDER BY
            people.first_name,
            people.last_name
        """,
        (
            certificate_id,
        ),
    ).fetchall()


    recipient_ids = {

        row[
            "person_id"
        ]

        for row
        in recipients

    }


    people = cursor.execute(
        """
        SELECT
            person_id,
            first_name,
            last_name,
            email

        FROM people

        ORDER BY
            first_name,
            last_name
        """
    ).fetchall()


    conn.close()


    return render_template(
        "records/certificate_detail.html",

        certificate=certificate,

        recipients=recipients,

        recipient_ids=(
            recipient_ids
        ),

        people=people,

        error=error,

        can_manage=(
            can_manage_certificates(
                user
            )
        ),
    )


@records_bp.route(
    "/records/certificates/<int:certificate_id>/file"
)
def certificate_file(
    certificate_id,
):

    user = (
        get_current_user()
    )


    denied = (
        require_records_access(
            user
        )
    )


    if denied:

        return denied


    conn = (
        get_db_connection()
    )


    row = conn.execute(
        """
        SELECT
            file_path,
            original_filename

        FROM certificates

        WHERE certificate_id = ?
        """,
        (
            certificate_id,
        ),
    ).fetchone()


    conn.close()


    if (
        row is None
        or not row[
            "file_path"
        ]
    ):

        return (
            "Certificate file not found",
            404,
        )


    folder = os.path.join(
        current_app.root_path,
        "uploads",
        "records",
        "certificates",
    )


    return send_from_directory(
        folder,

        os.path.basename(
            row[
                "file_path"
            ]
        ),

        as_attachment=True,

        download_name=(

            row[
                "original_filename"
            ]

            or os.path.basename(
                row[
                    "file_path"
                ]
            )
        ),
    )


@records_bp.route(
    "/records/certificates/<int:certificate_id>/delete",
    methods=[
        "POST",
    ],
)
def delete_certificate(
    certificate_id,
):

    user = (
        get_current_user()
    )


    if not can_manage_certificates(
        user
    ):

        return (
            "Access denied",
            403,
        )


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    row = cursor.execute(
        """
        SELECT
            certificates.*,

            terms.status
                AS term_status

        FROM certificates

        JOIN terms

            ON terms.term_id =
               certificates.term_id

        WHERE
            certificate_id = ?
        """,
        (
            certificate_id,
        ),
    ).fetchone()


    if row is None:

        conn.close()

        return (
            "Certificate not found",
            404,
        )


    if (
        row[
            "term_status"
        ]
        != "ACTIVE"
    ):

        conn.close()

        return (
            "Archived certificate "
            "is read-only.",
            403,
        )


    cursor.execute(
        """
        DELETE FROM certificate_recipients

        WHERE certificate_id = ?
        """,
        (
            certificate_id,
        ),
    )


    cursor.execute(
        """
        DELETE FROM certificates

        WHERE certificate_id = ?
        """,
        (
            certificate_id,
        ),
    )


    conn.commit()

    conn.close()


    delete_upload(
        "certificates",
        row[
            "file_path"
        ],
    )


    return redirect(
        url_for(
            "records.certificates"
        )
    )


# ============================================================
# RESEARCH REFERENCES
# ============================================================

@records_bp.route(
    "/records/references"
)
def references():

    user = (
        get_current_user()
    )


    denied = (
        require_records_access(
            user
        )
    )


    if denied:

        return denied


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    term = (
        active_term(
            cursor
        )
    )


    if term is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    sources = cursor.execute(
        """
        SELECT
            source_references.*,

            COUNT(
                article_source_references.article_source_reference_id
            )
                AS link_count

        FROM source_references

        LEFT JOIN article_source_references

            ON article_source_references.source_reference_id =
               source_references.source_reference_id

        GROUP BY
            source_references.source_reference_id

        ORDER BY
            source_references.title
        """
    ).fetchall()


    articles = cursor.execute(
        """
        SELECT
            scientific_articles.scientific_article_id,

            scientific_articles.title,

            GROUP_CONCAT(
                article_source_references.source_reference_id
            )
                AS linked_source_ids

        FROM scientific_articles

        JOIN article_terms

            ON article_terms.scientific_article_id =
               scientific_articles.scientific_article_id

        LEFT JOIN article_source_references

            ON article_source_references.scientific_article_id =
               scientific_articles.scientific_article_id

        WHERE
            article_terms.term_id = ?

        GROUP BY
            scientific_articles.scientific_article_id

        ORDER BY
            scientific_articles.title
        """,
        (
            term[
                "term_id"
            ],
        ),
    ).fetchall()


    linked = cursor.execute(
        """
        SELECT
            scientific_articles.scientific_article_id,

            scientific_articles.title
                AS article_title,

            source_references.source_reference_id,

            COALESCE(
                article_source_references.source_title_snapshot,
                source_references.title
            )
                AS source_title

        FROM article_source_references


        JOIN scientific_articles

            ON scientific_articles.scientific_article_id =
               article_source_references.scientific_article_id


        JOIN article_terms

            ON article_terms.scientific_article_id =
               scientific_articles.scientific_article_id


        JOIN source_references

            ON source_references.source_reference_id =
               article_source_references.source_reference_id


        WHERE
            article_terms.term_id = ?


        ORDER BY
            scientific_articles.title,
            source_title
        """,
        (
            term[
                "term_id"
            ],
        ),
    ).fetchall()


    conn.close()


    return render_template(
        "records/references.html",

        term=term,

        sources=sources,

        articles=articles,

        linked=linked,

        can_manage=(
            can_manage_references(
                user
            )
        ),
    )


@records_bp.route(
    "/records/references/new",
    methods=[
        "POST",
    ],
)
def create_reference():

    user = (
        get_current_user()
    )


    if not can_manage_references(
        user
    ):

        return (
            "Access denied",
            403,
        )


    title = (
        request.form.get(
            "title",
            "",
        ).strip()
    )


    if not title:

        return (
            "Reference title is required.",
            400,
        )


    year_raw = (
        request.form.get(
            "publication_year",
            "",
        ).strip()
    )


    year = None


    if year_raw:

        try:

            year = int(
                year_raw
            )

        except ValueError:

            return (
                (
                    "Publication year "
                    "must be a number."
                ),
                400,
            )


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    cursor.execute(
        """
        INSERT INTO source_references (
            title,
            authors,
            source_type,
            publication_year,
            url,
            doi
        )

        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            title,

            normalize_optional(
                request.form.get(
                    "authors"
                )
            ),

            normalize_optional(
                request.form.get(
                    "source_type"
                )
            ),

            year,

            normalize_optional(
                request.form.get(
                    "url"
                )
            ),

            normalize_optional(
                request.form.get(
                    "doi"
                )
            ),
        ),
    )


    conn.commit()

    conn.close()


    return redirect(
        url_for(
            "records.references"
        )
    )


@records_bp.route(
    "/records/references/<int:source_id>/update",
    methods=[
        "POST",
    ],
)
def update_reference(
    source_id,
):

    user = (
        get_current_user()
    )


    if not can_manage_references(
        user
    ):

        return (
            "Access denied",
            403,
        )


    title = (
        request.form.get(
            "title",
            "",
        ).strip()
    )


    if not title:

        return (
            "Reference title is required.",
            400,
        )


    year_raw = (
        request.form.get(
            "publication_year",
            "",
        ).strip()
    )


    year = None


    if year_raw:

        try:

            year = int(
                year_raw
            )

        except ValueError:

            return (
                (
                    "Publication year "
                    "must be a number."
                ),
                400,
            )


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    cursor.execute(
        """
        UPDATE source_references

        SET
            title = ?,

            authors = ?,

            source_type = ?,

            publication_year = ?,

            url = ?,

            doi = ?

        WHERE
            source_reference_id = ?
        """,
        (
            title,

            normalize_optional(
                request.form.get(
                    "authors"
                )
            ),

            normalize_optional(
                request.form.get(
                    "source_type"
                )
            ),

            year,

            normalize_optional(
                request.form.get(
                    "url"
                )
            ),

            normalize_optional(
                request.form.get(
                    "doi"
                )
            ),

            source_id,
        ),
    )


    conn.commit()

    conn.close()


    return redirect(
        url_for(
            "records.references"
        )
    )


@records_bp.route(
    "/records/references/<int:source_id>/delete",
    methods=[
        "POST",
    ],
)
def delete_reference(
    source_id,
):

    user = (
        get_current_user()
    )


    if not can_manage_references(
        user
    ):

        return (
            "Access denied",
            403,
        )


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    linked = cursor.execute(
        """
        SELECT COUNT(*)

        FROM article_source_references

        WHERE
            source_reference_id = ?
        """,
        (
            source_id,
        ),
    ).fetchone()[0]


    if linked:

        conn.close()

        return (
            (
                "Unlink this source "
                "from all articles "
                "before deleting it."
            ),
            400,
        )


    try:

        cursor.execute(
            """
            DELETE FROM source_references

            WHERE
                source_reference_id = ?
            """,
            (
                source_id,
            ),
        )


        conn.commit()


    except sqlite3.IntegrityError as error:

        conn.rollback()

        conn.close()


        return (
            str(error),
            400,
        )


    conn.close()


    return redirect(
        url_for(
            "records.references"
        )
    )


@records_bp.route(
    "/records/references/link",
    methods=[
        "POST",
    ],
)
def link_reference():

    user = (
        get_current_user()
    )


    if not can_manage_references(
        user
    ):

        return (
            "Access denied",
            403,
        )


    try:

        article_id = int(
            request.form.get(
                "article_id",
                "",
            )
        )


        source_id = int(
            request.form.get(
                "source_id",
                "",
            )
        )


    except ValueError:

        return (
            "Invalid article or source.",
            400,
        )


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    term = (
        active_term(
            cursor
        )
    )


    if term is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    article = cursor.execute(
        """
        SELECT
            scientific_articles.scientific_article_id

        FROM scientific_articles

        JOIN article_terms

            ON article_terms.scientific_article_id =
               scientific_articles.scientific_article_id

        WHERE
            scientific_articles.scientific_article_id = ?

          AND article_terms.term_id = ?
        """,
        (
            article_id,

            term[
                "term_id"
            ],
        ),
    ).fetchone()


    source = cursor.execute(
        """
        SELECT
            source_reference_id

        FROM source_references

        WHERE
            source_reference_id = ?
        """,
        (
            source_id,
        ),
    ).fetchone()


    if (
        article is None
        or source is None
    ):

        conn.close()

        return (
            (
                "Article or source "
                "not found in active mandate."
            ),
            404,
        )


    try:

        cursor.execute(
            """
            INSERT OR IGNORE
            INTO article_source_references (
                scientific_article_id,
                source_reference_id
            )

            VALUES (?, ?)
            """,
            (
                article_id,
                source_id,
            ),
        )


        conn.commit()


    except sqlite3.IntegrityError as error:

        conn.rollback()

        conn.close()


        return (
            str(error),
            400,
        )


    conn.close()


    return redirect(
        url_for(
            "records.references"
        )
    )


@records_bp.route(
    (
        "/records/references/"
        "article/<int:article_id>/"
        "source/<int:source_id>/unlink"
    ),
    methods=[
        "POST",
    ],
)
def unlink_reference(
    article_id,
    source_id,
):

    user = (
        get_current_user()
    )


    if not can_manage_references(
        user
    ):

        return (
            "Access denied",
            403,
        )


    conn = (
        get_db_connection()
    )

    cursor = (
        conn.cursor()
    )


    term = (
        active_term(
            cursor
        )
    )


    if term is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    active_article = cursor.execute(
        """
        SELECT 1

        FROM article_terms

        WHERE
            scientific_article_id = ?

          AND term_id = ?
        """,
        (
            article_id,

            term[
                "term_id"
            ],
        ),
    ).fetchone()


    if active_article is None:

        conn.close()

        return (
            (
                "Only active-mandate "
                "article references "
                "can be edited."
            ),
            403,
        )


    try:

        cursor.execute(
            """
            DELETE FROM article_source_references

            WHERE
                scientific_article_id = ?

              AND source_reference_id = ?
            """,
            (
                article_id,
                source_id,
            ),
        )


        conn.commit()


    except sqlite3.IntegrityError as error:

        conn.rollback()

        conn.close()


        return (
            str(error),
            400,
        )


    conn.close()


    return redirect(
        url_for(
            "records.references"
        )
    )