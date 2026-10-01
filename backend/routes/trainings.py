import os
import uuid

from datetime import date

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    session,
    url_for,
)

from werkzeug.utils import secure_filename

from context import get_active_term_id
from database import get_db_connection
from permissions import login_required


trainings_bp = Blueprint(
    "trainings",
    __name__,
)


HR_DEPARTMENT_ID = 1
DPA_DEPARTMENT_ID = 2
DCM_DEPARTMENT_ID = 4


# ========================================
# TRAINING MEDIA
# ========================================

ALLOWED_IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

ALLOWED_VIDEO_EXTENSIONS = {
    ".mp4",
    ".webm",
    ".mov",
}


def get_training_media_folder():

    folder = os.path.join(
        current_app.root_path,
        "uploads",
        "trainings",
    )

    os.makedirs(
        folder,
        exist_ok=True,
    )

    return folder


def get_training_media_type(filename):

    extension = os.path.splitext(
        filename
    )[1].lower()

    if extension in ALLOWED_IMAGE_EXTENSIONS:
        return "image"

    if extension in ALLOWED_VIDEO_EXTENSIONS:
        return "video"

    return None


# ========================================
# CURRENT MEMBER
# ========================================

def get_current_training_member(conn):

    active_term_id = get_active_term_id()

    if active_term_id is None:
        return None

    cursor = conn.cursor()

    # ========================================
    # CURRENT MEMBER
    # ========================================

    cursor.execute("""
        SELECT
            memberships.membership_id,
            memberships.term_id,
            memberships.department_id,
            departments.name AS department_name,
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

    member = cursor.fetchone()

    if member is not None:
        return member

    # ========================================
    # ALUMNI
    # Latest ARCHIVED membership only
    # ========================================

    cursor.execute("""
        SELECT
            memberships.membership_id,
            memberships.term_id,
            memberships.department_id,
            departments.name AS department_name,
            roles.name AS role_name,
            1 AS is_alumni

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
# HELPERS
# ========================================

def is_current_dpa_manager(member):

    return (
        member is not None
        and not member["is_alumni"]
        and member["department_id"]
        == DPA_DEPARTMENT_ID
        and member["role_name"]
        in (
            "HEAD",
            "SUB_HEAD",
        )
    )


def is_current_hr_member(member):

    return (
        member is not None
        and not member["is_alumni"]
        and member["department_id"]
        == HR_DEPARTMENT_ID
    )


def is_current_dcm_manager(member):

    return (
        member is not None
        and not member["is_alumni"]
        and member["department_id"]
        == DCM_DEPARTMENT_ID
        and member["role_name"]
        in (
            "HEAD",
            "SUB_HEAD",
        )
    )


def is_current_dcm_head(member):

    return (
        member is not None
        and not member["is_alumni"]
        and member["department_id"]
        == DCM_DEPARTMENT_ID
        and member["role_name"]
        == "HEAD"
    )


def get_training_term_state(
    cursor,
    training_id,
    active_term_id,
):

    cursor.execute("""
        SELECT
            EXISTS (
                SELECT 1

                FROM training_terms

                WHERE training_id = ?
                  AND term_id = ?
            ) AS is_active_training,

            EXISTS (
                SELECT 1

                FROM training_terms

                JOIN terms
                    ON training_terms.term_id =
                       terms.term_id

                WHERE training_terms.training_id = ?
                  AND terms.status = 'ARCHIVED'
            ) AS has_archived_term
    """, (
        training_id,
        active_term_id,
        training_id,
    ))

    return cursor.fetchone()


# ========================================
# TRAININGS LIST
# ========================================

@trainings_bp.route("/trainings")
@login_required
def trainings():

    conn = get_db_connection()
    cursor = conn.cursor()

    current_member = get_current_training_member(
        conn
    )

    if current_member is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    can_manage_trainings = (
        is_current_dpa_manager(
            current_member
        )
    )

    # ========================================
    # GET TRAININGS
    #
    # ACTIVE + ARCHIVED only.
    # DRAFT mandates are hidden.
    # ========================================

    cursor.execute("""
        SELECT
            trainings.training_id,
            trainings.title,
            trainings.description,
            trainings.training_date,
            trainings.start_time,
            trainings.end_time,
            trainings.location,

            coach.person_id
                AS coach_person_id,

            coach.first_name
                AS coach_first_name,

            coach.last_name
                AS coach_last_name,

            GROUP_CONCAT(
                DISTINCT terms.name
            ) AS term_names,

            MAX(
                CASE
                    WHEN terms.status = 'ACTIVE'
                    THEN 1
                    ELSE 0
                END
            ) AS is_active_training

        FROM trainings

        JOIN people AS coach
            ON trainings.coach_person_id =
               coach.person_id

        JOIN training_terms
            ON trainings.training_id =
               training_terms.training_id

        JOIN terms
            ON training_terms.term_id =
               terms.term_id

        WHERE terms.status IN (
            'ACTIVE',
            'ARCHIVED'
        )

        GROUP BY
            trainings.training_id

        ORDER BY
            trainings.training_date ASC
    """)

    all_trainings = cursor.fetchall()

    conn.close()

    # ========================================
    # UPCOMING / PAST
    # ========================================

    today = date.today().isoformat()

    upcoming_trainings = []
    past_trainings = []

    for training in all_trainings:

        training_date = (
            training["training_date"]
        )

        if training_date is None:

            upcoming_trainings.append(
                training
            )

        elif training_date >= today:

            upcoming_trainings.append(
                training
            )

        else:

            past_trainings.append(
                training
            )

    past_trainings.reverse()

    return render_template(
        "trainings.html",

        upcoming_trainings=(
            upcoming_trainings
        ),

        past_trainings=(
            past_trainings
        ),

        can_manage_trainings=(
            can_manage_trainings
        ),
    )


# ========================================
# NEW TRAINING
# ========================================

@trainings_bp.route(
    "/trainings/new",
    methods=["GET", "POST"],
)
@login_required
def new_training():

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    current_member = (
        get_current_training_member(
            conn
        )
    )

    if current_member is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    if not is_current_dpa_manager(
        current_member
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    # ========================================
    # AVAILABLE COACHES
    # ========================================

    cursor.execute("""
        SELECT
            person_id,
            first_name,
            last_name,
            profession

        FROM people

        ORDER BY
            first_name ASC,
            last_name ASC
    """)

    coaches = cursor.fetchall()

    # ========================================
    # CREATE TRAINING
    # ========================================

    if request.method == "POST":

        title = request.form.get(
            "title",
            "",
        ).strip()

        description = request.form.get(
            "description",
            "",
        ).strip()

        coach_person_id = (
            request.form.get(
                "coach_person_id"
            )
        )

        training_date = (
            request.form.get(
                "training_date"
            )
            or None
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

        registration_link = (
            request.form.get(
                "registration_link",
                "",
            ).strip()
            or None
        )

        # ====================================
        # REQUIRED FIELDS
        # ====================================

        if not title:

            conn.close()

            return (
                "Title is required",
                400,
            )

        if not coach_person_id:

            conn.close()

            return (
                "Coach is required",
                400,
            )

        if (
            start_time
            and end_time
            and end_time < start_time
        ):

            conn.close()

            return (
                "End time cannot be before "
                "start time",
                400,
            )

        # ====================================
        # VERIFY COACH
        # ====================================

        cursor.execute("""
            SELECT
                person_id

            FROM people

            WHERE person_id = ?
        """, (
            coach_person_id,
        ))

        coach = cursor.fetchone()

        if coach is None:

            conn.close()

            return (
                "Coach not found",
                404,
            )

        # ====================================
        # CREATE TRAINING
        # ====================================

        cursor.execute("""
            INSERT INTO trainings (
                coach_person_id,
                title,
                description,
                training_date,
                start_time,
                end_time,
                location,
                registration_link
            )

            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (
            coach_person_id,
            title,
            description or None,
            training_date,
            start_time,
            end_time,
            location,
            registration_link,
        ))

        training_id = cursor.lastrowid

        # ====================================
        # LINK TO ACTIVE TERM
        # ====================================

        cursor.execute("""
            INSERT INTO training_terms (
                training_id,
                term_id
            )

            VALUES (?, ?)
        """, (
            training_id,
            active_term_id,
        ))

        conn.commit()
        conn.close()

        return redirect(
            url_for(
                "trainings.trainings"
            )
        )

    conn.close()

    return render_template(
        "new_training.html",
        coaches=coaches,
    )


# ========================================
# TRAINING DETAIL
# ========================================

@trainings_bp.route(
    "/trainings/<int:training_id>"
)
@login_required
def training_detail(training_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    current_member = (
        get_current_training_member(
            conn
        )
    )

    if current_member is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    # ========================================
    # TRAINING
    # ACTIVE + ARCHIVED
    # ========================================

    cursor.execute("""
        SELECT
            trainings.training_id,
            trainings.title,
            trainings.description,
            trainings.training_date,
            trainings.start_time,
            trainings.end_time,
            trainings.location,
            trainings.registration_link,

            coach.person_id
                AS coach_person_id,

            coach.first_name
                AS coach_first_name,

            coach.last_name
                AS coach_last_name,

            coach.profession
                AS coach_profession,

            GROUP_CONCAT(
                DISTINCT terms.name
            ) AS term_names,

            MAX(
                CASE
                    WHEN terms.status = 'ACTIVE'
                    THEN 1
                    ELSE 0
                END
            ) AS is_active_training,

            MAX(
                CASE
                    WHEN terms.status = 'ARCHIVED'
                    THEN 1
                    ELSE 0
                END
            ) AS has_archived_term

        FROM trainings

        JOIN people AS coach
            ON trainings.coach_person_id =
               coach.person_id

        JOIN training_terms
            ON trainings.training_id =
               training_terms.training_id

        JOIN terms
            ON training_terms.term_id =
               terms.term_id

        WHERE trainings.training_id = ?
          AND terms.status IN (
              'ACTIVE',
              'ARCHIVED'
          )

        GROUP BY
            trainings.training_id
    """, (
        training_id,
    ))

    training = cursor.fetchone()

    if training is None:

        conn.close()

        return (
            "Training not found",
            404,
        )

    is_active_training = bool(
        training["is_active_training"]
    )

    has_archived_term = bool(
        training["has_archived_term"]
    )

    can_modify_training = (
        is_active_training
        and not has_archived_term
    )

    # ========================================
    # PERMISSIONS
    # ========================================

    can_manage_trainings = (
        can_modify_training
        and is_current_dpa_manager(
            current_member
        )
    )

    can_manage_attendance = (
        is_active_training
        and is_current_hr_member(
            current_member
        )
    )

    can_manage_media = (
        can_modify_training
        and is_current_dcm_manager(
            current_member
        )
    )

    can_publish_media = (
        can_modify_training
        and is_current_dcm_head(
            current_member
        )
    )

    # ========================================
    # TRAINING MEDIA
    # ========================================

    cursor.execute("""
        SELECT
            training_media.training_media_id,
            training_media.media_type,
            training_media.file_path,
            training_media.original_filename,
            training_media.caption,
            training_media.is_public,
            training_media.uploaded_at,

            people.first_name
                AS uploader_first_name,

            people.last_name
                AS uploader_last_name

        FROM training_media

        JOIN memberships
            ON training_media.uploaded_by_membership_id =
               memberships.membership_id

        JOIN people
            ON memberships.person_id =
               people.person_id

        WHERE training_media.training_id = ?

        ORDER BY
            training_media.uploaded_at DESC
    """, (
        training_id,
    ))

    training_media = cursor.fetchall()

    conn.close()

    return render_template(
        "training_detail.html",

        training=training,

        can_manage_trainings=(
            can_manage_trainings
        ),

        can_manage_attendance=(
            can_manage_attendance
        ),

        training_media=(
            training_media
        ),

        can_manage_media=(
            can_manage_media
        ),

        can_publish_media=(
            can_publish_media
        ),
    )


# ========================================
# UPLOAD TRAINING MEDIA
# HEAD / SUB_HEAD DCM ONLY
# ACTIVE TRAINING ONLY
# ========================================

@trainings_bp.route(
    "/trainings/<int:training_id>/media/upload",
    methods=["POST"],
)
@login_required
def upload_training_media(training_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    current_member = (
        get_current_training_member(
            conn
        )
    )

    if current_member is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    if not is_current_dcm_manager(
        current_member
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    # ========================================
    # VERIFY TRAINING
    # ========================================

    state = get_training_term_state(
        cursor,
        training_id,
        active_term_id,
    )

    if (
        state is None
        or not state["is_active_training"]
    ):

        conn.close()

        return (
            "Training not found",
            404,
        )

    if state["has_archived_term"]:

        conn.close()

        return (
            "Archived training data is read-only.",
            403,
        )

    # ========================================
    # GET FILE
    # ========================================

    media_file = request.files.get(
        "media_file"
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

    original_filename = secure_filename(
        media_file.filename
    )

    media_type = get_training_media_type(
        original_filename
    )

    if media_type is None:

        conn.close()

        return (
            "Unsupported file type. "
            "Allowed images: JPG, JPEG, PNG, WEBP. "
            "Allowed videos: MP4, WEBM, MOV.",
            400,
        )

    # ========================================
    # CAPTION
    # ========================================

    caption = (
        request.form.get(
            "caption",
            "",
        ).strip()
        or None
    )

    # ========================================
    # UNIQUE FILE NAME
    # ========================================

    extension = os.path.splitext(
        original_filename
    )[1].lower()

    stored_filename = (
        "training_"
        + str(training_id)
        + "_"
        + uuid.uuid4().hex
        + extension
    )

    upload_folder = (
        get_training_media_folder()
    )

    save_path = os.path.join(
        upload_folder,
        stored_filename,
    )

    # ========================================
    # SAVE FILE
    # ========================================

    media_file.save(
        save_path
    )

    relative_path = os.path.join(
        "uploads",
        "trainings",
        stored_filename,
    ).replace(
        "\\",
        "/",
    )

    # ========================================
    # SAVE DATABASE RECORD
    # ========================================

    cursor.execute("""
        INSERT INTO training_media (
            training_id,
            uploaded_by_membership_id,
            media_type,
            file_path,
            original_filename,
            caption,
            is_public
        )

        VALUES (?, ?, ?, ?, ?, ?, 0)
    """, (
        training_id,
        current_member[
            "membership_id"
        ],
        media_type,
        relative_path,
        original_filename,
        caption,
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "trainings.training_detail",
            training_id=training_id,
        )
    )


# ========================================
# VIEW TRAINING MEDIA
# ========================================

@trainings_bp.route(
    "/trainings/media/<int:training_media_id>"
)
@login_required
def view_training_media(
    training_media_id
):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_member = (
        get_current_training_member(
            conn
        )
    )

    if current_member is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    cursor.execute("""
        SELECT DISTINCT
            training_media.training_media_id,
            training_media.file_path,
            training_media.original_filename,
            training_media.media_type

        FROM training_media

        JOIN training_terms
            ON training_media.training_id =
               training_terms.training_id

        JOIN terms
            ON training_terms.term_id =
               terms.term_id

        WHERE training_media.training_media_id = ?
          AND terms.status IN (
              'ACTIVE',
              'ARCHIVED'
          )
    """, (
        training_media_id,
    ))

    media = cursor.fetchone()

    conn.close()

    if media is None:

        return (
            "Media not found",
            404,
        )

    stored_filename = os.path.basename(
        media["file_path"]
    )

    return send_from_directory(
        get_training_media_folder(),
        stored_filename,
        as_attachment=False,
        download_name=(
            media["original_filename"]
        ),
    )


# ========================================
# DOWNLOAD TRAINING MEDIA
# ========================================

@trainings_bp.route(
    "/trainings/media/<int:training_media_id>/download"
)
@login_required
def download_training_media(
    training_media_id
):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_member = (
        get_current_training_member(
            conn
        )
    )

    if current_member is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    cursor.execute("""
        SELECT DISTINCT
            training_media.training_media_id,
            training_media.file_path,
            training_media.original_filename

        FROM training_media

        JOIN training_terms
            ON training_media.training_id =
               training_terms.training_id

        JOIN terms
            ON training_terms.term_id =
               terms.term_id

        WHERE training_media.training_media_id = ?
          AND terms.status IN (
              'ACTIVE',
              'ARCHIVED'
          )
    """, (
        training_media_id,
    ))

    media = cursor.fetchone()

    conn.close()

    if media is None:

        return (
            "Media not found",
            404,
        )

    stored_filename = os.path.basename(
        media["file_path"]
    )

    return send_from_directory(
        get_training_media_folder(),
        stored_filename,
        as_attachment=True,
        download_name=(
            media["original_filename"]
        ),
    )


# ========================================
# DELETE TRAINING MEDIA
# ========================================

@trainings_bp.route(
    "/trainings/media/<int:training_media_id>/delete",
    methods=["POST"],
)
@login_required
def delete_training_media(
    training_media_id
):

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    current_member = (
        get_current_training_member(
            conn
        )
    )

    if current_member is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    if not is_current_dcm_manager(
        current_member
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    cursor.execute("""
        SELECT
            training_media.training_media_id,
            training_media.training_id,
            training_media.file_path

        FROM training_media

        WHERE training_media_id = ?
    """, (
        training_media_id,
    ))

    media = cursor.fetchone()

    if media is None:

        conn.close()

        return (
            "Media not found",
            404,
        )

    state = get_training_term_state(
        cursor,
        media["training_id"],
        active_term_id,
    )

    if (
        state is None
        or not state["is_active_training"]
    ):

        conn.close()

        return (
            "Training not found",
            404,
        )

    if state["has_archived_term"]:

        conn.close()

        return (
            "Archived training data is read-only.",
            403,
        )

    training_id = (
        media["training_id"]
    )

    file_path = (
        media["file_path"]
    )

    cursor.execute("""
        DELETE FROM training_media

        WHERE training_media_id = ?
    """, (
        training_media_id,
    ))

    conn.commit()
    conn.close()

    stored_filename = os.path.basename(
        file_path
    )

    physical_path = os.path.join(
        get_training_media_folder(),
        stored_filename,
    )

    if os.path.exists(
        physical_path
    ):

        try:

            os.remove(
                physical_path
            )

        except OSError:

            pass

    return redirect(
        url_for(
            "trainings.training_detail",
            training_id=training_id,
        )
    )


# ========================================
# TOGGLE TRAINING MEDIA PUBLICATION
# ========================================

@trainings_bp.route(
    "/trainings/media/<int:training_media_id>/publication/toggle",
    methods=["POST"],
)
@login_required
def toggle_training_media_publication(
    training_media_id
):

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    current_member = (
        get_current_training_member(
            conn
        )
    )

    if current_member is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    if not is_current_dcm_head(
        current_member
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    cursor.execute("""
        SELECT
            training_media_id,
            training_id,
            media_type,
            is_public

        FROM training_media

        WHERE training_media_id = ?
    """, (
        training_media_id,
    ))

    media = cursor.fetchone()

    if media is None:

        conn.close()

        return (
            "Media not found",
            404,
        )

    state = get_training_term_state(
        cursor,
        media["training_id"],
        active_term_id,
    )

    if (
        state is None
        or not state["is_active_training"]
    ):

        conn.close()

        return (
            "Training not found",
            404,
        )

    if state["has_archived_term"]:

        conn.close()

        return (
            "Archived training data is read-only.",
            403,
        )

    if media["media_type"] != "image":

        conn.close()

        return (
            "Only images can be published "
            "on the public website.",
            400,
        )

    new_public_status = (
        0
        if media["is_public"]
        else 1
    )

    cursor.execute("""
        UPDATE training_media

        SET is_public = ?

        WHERE training_media_id = ?
    """, (
        new_public_status,
        training_media_id,
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for(
            "trainings.training_detail",
            training_id=(
                media["training_id"]
            ),
        )
    )


# ========================================
# EDIT TRAINING
# ========================================

@trainings_bp.route(
    "/trainings/<int:training_id>/edit",
    methods=["GET", "POST"],
)
@login_required
def edit_training(training_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    current_member = (
        get_current_training_member(
            conn
        )
    )

    if current_member is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    if not is_current_dpa_manager(
        current_member
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    cursor.execute("""
        SELECT
            trainings.training_id,
            trainings.coach_person_id,
            trainings.title,
            trainings.description,
            trainings.training_date,
            trainings.start_time,
            trainings.end_time,
            trainings.location,
            trainings.registration_link

        FROM trainings

        JOIN training_terms
            ON trainings.training_id =
               training_terms.training_id

        WHERE trainings.training_id = ?
          AND training_terms.term_id = ?

        LIMIT 1
    """, (
        training_id,
        active_term_id,
    ))

    training = cursor.fetchone()

    if training is None:

        conn.close()

        return (
            "Training not found",
            404,
        )

    state = get_training_term_state(
        cursor,
        training_id,
        active_term_id,
    )

    if state["has_archived_term"]:

        conn.close()

        return (
            "Archived training data is read-only.",
            403,
        )

    # ========================================
    # COACH LIST
    # ========================================

    cursor.execute("""
        SELECT
            person_id,
            first_name,
            last_name,
            profession

        FROM people

        ORDER BY
            first_name ASC,
            last_name ASC
    """)

    coaches = cursor.fetchall()

    # ========================================
    # UPDATE
    # ========================================

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

        coach_person_id = (
            request.form.get(
                "coach_person_id"
            )
        )

        training_date = (
            request.form.get(
                "training_date"
            )
            or None
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

        registration_link = (
            request.form.get(
                "registration_link",
                "",
            ).strip()
            or None
        )

        if not title:

            conn.close()

            return (
                "Title is required",
                400,
            )

        if not coach_person_id:

            conn.close()

            return (
                "Coach is required",
                400,
            )

        if (
            start_time
            and end_time
            and end_time < start_time
        ):

            conn.close()

            return (
                "End time cannot be before "
                "start time",
                400,
            )

        cursor.execute("""
            SELECT
                person_id

            FROM people

            WHERE person_id = ?
        """, (
            coach_person_id,
        ))

        if cursor.fetchone() is None:

            conn.close()

            return (
                "Coach not found",
                404,
            )

        cursor.execute("""
            UPDATE trainings

            SET
                coach_person_id = ?,
                title = ?,
                description = ?,
                training_date = ?,
                start_time = ?,
                end_time = ?,
                location = ?,
                registration_link = ?

            WHERE training_id = ?
              AND training_id IN (
                    SELECT training_id

                    FROM training_terms

                    WHERE term_id = ?
              )
        """, (
            coach_person_id,
            title,
            description,
            training_date,
            start_time,
            end_time,
            location,
            registration_link,
            training_id,
            active_term_id,
        ))

        conn.commit()
        conn.close()

        return redirect(
            url_for(
                "trainings.training_detail",
                training_id=training_id,
            )
        )

    conn.close()

    return render_template(
        "edit_training.html",
        training=training,
        coaches=coaches,
    )


# ========================================
# DELETE TRAINING
# ========================================

@trainings_bp.route(
    "/trainings/<int:training_id>/delete",
    methods=["POST"],
)
@login_required
def delete_training(training_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    current_member = (
        get_current_training_member(
            conn
        )
    )

    if current_member is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    if not is_current_dpa_manager(
        current_member
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    state = get_training_term_state(
        cursor,
        training_id,
        active_term_id,
    )

    if (
        state is None
        or not state["is_active_training"]
    ):

        conn.close()

        return (
            "Training not found",
            404,
        )

    if state["has_archived_term"]:

        conn.close()

        return (
            "Archived training data cannot be deleted.",
            403,
        )

    # ========================================
    # GET MEDIA FILES
    # ========================================

    cursor.execute("""
        SELECT
            file_path

        FROM training_media

        WHERE training_id = ?
    """, (
        training_id,
    ))

    media_files = cursor.fetchall()

    # ========================================
    # DELETE DATABASE DATA
    # ========================================

    cursor.execute("""
        DELETE FROM training_media

        WHERE training_id = ?
    """, (
        training_id,
    ))

    cursor.execute("""
        DELETE FROM training_attendance

        WHERE training_id = ?
    """, (
        training_id,
    ))

    cursor.execute("""
        DELETE FROM training_terms

        WHERE training_id = ?
          AND term_id = ?
    """, (
        training_id,
        active_term_id,
    ))

    cursor.execute("""
        DELETE FROM trainings

        WHERE training_id = ?
    """, (
        training_id,
    ))

    conn.commit()
    conn.close()

    # ========================================
    # DELETE PHYSICAL MEDIA FILES
    # ========================================

    media_folder = (
        get_training_media_folder()
    )

    for media in media_files:

        stored_filename = (
            os.path.basename(
                media["file_path"]
            )
        )

        physical_path = os.path.join(
            media_folder,
            stored_filename,
        )

        try:

            if os.path.exists(
                physical_path
            ):

                os.remove(
                    physical_path
                )

        except OSError:

            pass

    return redirect(
        url_for(
            "trainings.trainings"
        )
    )


# ========================================
# ATTENDANCE SHEET
# HR ONLY
# ACTIVE TRAINING ONLY
# ========================================

@trainings_bp.route(
    "/trainings/<int:training_id>/attendance-sheet"
)
@login_required
def attendance_sheet(training_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    current_member = (
        get_current_training_member(
            conn
        )
    )

    if current_member is None:

        conn.close()

        return (
            "Current membership not found",
            404,
        )

    if not is_current_hr_member(
        current_member
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )

    cursor.execute("""
        SELECT
            trainings.training_id,
            trainings.title,
            trainings.training_date

        FROM trainings

        JOIN training_terms
            ON trainings.training_id =
               training_terms.training_id

        WHERE trainings.training_id = ?
          AND training_terms.term_id = ?

        LIMIT 1
    """, (
        training_id,
        active_term_id,
    ))

    training = cursor.fetchone()

    conn.close()

    if training is None:

        return (
            "Training not found",
            404,
        )

    file_path = os.path.join(
        os.path.dirname(
            __file__
        ),
        "..",
        "resources",
        "attendance_template.xlsx",
    )

    file_path = os.path.abspath(
        file_path
    )

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
        in training["title"]
    ).strip()

    download_name = (
        f"{safe_title}"
        f"_attendance.xlsx"
    )

    return send_file(
        file_path,
        as_attachment=True,
        download_name=download_name,
    )