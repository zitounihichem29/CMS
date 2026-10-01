import os
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

from context import get_active_term_id
from database import get_db_connection
from routes.notifications import create_notification


public_bp = Blueprint(
    "public",
    __name__,
)


# ========================================
# PUBLIC HOME
# ========================================

@public_bp.route("/website")
def home():

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = get_active_term_id()

    now = datetime.now()

    today = now.strftime(
        "%Y-%m-%d"
    )

    current_time = now.strftime(
        "%H:%M:%S"
    )


    # ========================================
    # NEXT EVENT
    # ACTIVE MANDATE ONLY
    # ========================================

    cursor.execute("""
        SELECT
            events.event_id,
            events.title,
            events.event_date,
            events.start_time,
            events.end_date,
            events.end_time,

            people.first_name
                AS leader_first_name,

            people.last_name
                AS leader_last_name

        FROM events

        JOIN memberships
            ON events.event_leader_membership_id =
               memberships.membership_id

        JOIN people
            ON memberships.person_id =
               people.person_id

        WHERE events.term_id = ?

          AND (
                events.end_date > ?

                OR (
                    events.end_date = ?

                    AND (
                        events.end_time IS NULL

                        OR events.end_time >= ?
                    )
                )
          )

        ORDER BY
            events.event_date ASC,

            CASE
                WHEN events.start_time IS NULL
                THEN 1
                ELSE 0
            END,

            events.start_time ASC

        LIMIT 1
    """, (
        active_term_id,
        today,
        today,
        current_time,
    ))


    event_row = cursor.fetchone()

    next_home_event = None


    if event_row is not None:

        event_date = datetime.strptime(
            str(
                event_row[
                    "event_date"
                ]
            ),
            "%Y-%m-%d",
        )


        next_home_event = {

            "event_id":
                event_row[
                    "event_id"
                ],

            "title":
                event_row[
                    "title"
                ],

            "leader_name":
                (
                    event_row[
                        "leader_first_name"
                    ]
                    + " "
                    + event_row[
                        "leader_last_name"
                    ]
                ),

            "day":
                event_date.strftime(
                    "%d"
                ),

            "month":
                event_date.strftime(
                    "%b"
                ).upper(),
        }


    # ========================================
    # NEXT TRAINING
    # ACTIVE MANDATE ONLY
    # ========================================

    cursor.execute("""
        SELECT
            trainings.training_id,
            trainings.title,
            trainings.training_date,
            trainings.start_time,
            trainings.end_time,

            coach.first_name
                AS coach_first_name,

            coach.last_name
                AS coach_last_name

        FROM trainings

        JOIN people AS coach
            ON trainings.coach_person_id =
               coach.person_id

        WHERE EXISTS (
            SELECT 1

            FROM training_terms

            JOIN terms
                ON training_terms.term_id =
                   terms.term_id

            WHERE training_terms.training_id =
                  trainings.training_id

              AND training_terms.term_id = ?

              AND terms.status = 'ACTIVE'
        )

          AND (
                trainings.training_date IS NULL

                OR trainings.training_date > ?

                OR (
                    trainings.training_date = ?

                    AND (
                        trainings.end_time IS NULL

                        OR trainings.end_time >= ?
                    )
                )
          )

        ORDER BY

            CASE
                WHEN trainings.training_date IS NULL
                THEN 1
                ELSE 0
            END,

            trainings.training_date ASC,

            CASE
                WHEN trainings.start_time IS NULL
                THEN 1
                ELSE 0
            END,

            trainings.start_time ASC

        LIMIT 1
    """, (
        active_term_id,
        today,
        today,
        current_time,
    ))


    training_row = cursor.fetchone()

    next_home_training = None


    if training_row is not None:

        training_day = "--"

        training_month = "TBD"


        if training_row[
            "training_date"
        ]:

            training_date = (
                datetime.strptime(
                    str(
                        training_row[
                            "training_date"
                        ]
                    ),
                    "%Y-%m-%d",
                )
            )

            training_day = (
                training_date.strftime(
                    "%d"
                )
            )

            training_month = (
                training_date
                .strftime(
                    "%b"
                )
                .upper()
            )


        next_home_training = {

            "training_id":
                training_row[
                    "training_id"
                ],

            "title":
                training_row[
                    "title"
                ],

            "coach_name":
                (
                    training_row[
                        "coach_first_name"
                    ]
                    + " "
                    + training_row[
                        "coach_last_name"
                    ]
                ),

            "day":
                training_day,

            "month":
                training_month,
        }


    # ========================================
    # CURRENT MEMBERS COUNT
    # ACTIVE MANDATE ONLY
    # ========================================

    cursor.execute("""
        SELECT
            COUNT(
                DISTINCT users.user_id
            ) AS total

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
    """, (
        active_term_id,
    ))


    members_count = (
        cursor.fetchone()[
            "total"
        ]
        or 0
    )


    # ========================================
    # DEPARTMENTS COUNT
    # ========================================

    cursor.execute("""
        SELECT
            COUNT(*) AS total

        FROM departments
    """)


    departments_count = (
        cursor.fetchone()[
            "total"
        ]
        or 0
    )


    conn.close()


    return render_template(
        "public/home.html",

        next_home_event=(
            next_home_event
        ),

        next_home_training=(
            next_home_training
        ),

        members_count=(
            members_count
        ),

        departments_count=(
            departments_count
        ),
    )


# ========================================
# ABOUT
# ========================================

@public_bp.route("/about")
def about():

    return render_template(
        "public/about.html"
    )


# ========================================
# DEPARTMENTS
# ========================================

@public_bp.route(
    "/website/departments"
)
def departments():

    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            department_id,
            name

        FROM departments

        ORDER BY
            department_id ASC
    """)


    departments_list = (
        cursor.fetchall()
    )


    conn.close()


    return render_template(
        "public/departments.html",

        departments=(
            departments_list
        ),
    )


# ========================================
# DEPARTMENT DETAIL
# ========================================

@public_bp.route(
    "/website/departments/<int:department_id>"
)
def department_detail(
    department_id
):

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = (
        get_active_term_id()
    )


    # ========================================
    # DEPARTMENT
    # ========================================

    cursor.execute("""
        SELECT
            department_id,
            name

        FROM departments

        WHERE department_id = ?
    """, (
        department_id,
    ))


    department = (
        cursor.fetchone()
    )


    if department is None:

        conn.close()

        return (
            "Department not found",
            404,
        )


    department_name = (
        department[
            "name"
        ]
        .lower()
        .strip()
    )


    # ========================================
    # PUBLIC DESCRIPTION
    # ========================================

    if (
        "human"
        in department_name

        or department_name
        == "rh"

        or "ressources"
        in department_name
    ):

        description = (
            "The Human Resources Department is at the heart of "
            "ORSC’s internal community. It manages recruitment, "
            "member integration, follow-up and internal motivation, "
            "while helping create a supportive and organized "
            "environment where every member can grow and contribute."
        )


    elif (
        "communication"
        in department_name

        or "media"
        in department_name

        or department_name
        == "dcm"
    ):

        description = (
            "The Communication & Media Department shapes ORSC’s "
            "digital identity and public presence. It manages club "
            "communication, media content, online platforms, data "
            "and analytics to make ORSC’s activities, projects and "
            "impact visible to the wider community."
        )


    elif (
        "external"
        in department_name

        or "relation"
        in department_name

        or department_name
        == "re"
    ):

        description = (
            "The External Relations Department builds and maintains "
            "ORSC’s connections beyond the club. It develops "
            "partnerships, communicates with organizations and "
            "professionals, supports collaborations and helps "
            "coordinate external events and opportunities."
        )


    elif (
        "project"
        in department_name

        or "activit"
        in department_name

        or department_name
        == "dpa"
    ):

        description = (
            "The Projects & Activities Department turns ideas into "
            "real experiences. It organizes workshops, projects, "
            "competitions, challenges and practical activities that "
            "allow members to apply their skills, collaborate and "
            "learn through action."
        )


    elif (
        "research"
        in department_name

        or "innovation"
        in department_name
    ):

        description = (
            "The Research Department explores Operations Research "
            "problems through analysis, modeling and scientific "
            "investigation. It encourages members to study real "
            "optimization challenges, develop research-oriented "
            "projects and contribute to scientific articles and "
            "knowledge sharing."
        )


    else:

        description = (
            "This department contributes to ORSC’s mission through "
            "collaboration, organization and activities that support "
            "the club and its members."
        )


    # ========================================
    # ACTIVE DEPARTMENT LEADERSHIP
    # ========================================

    cursor.execute("""
        SELECT
            people.first_name,
            people.last_name,
            people.profile_photo,

            roles.name
                AS role_name

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

        WHERE memberships.department_id = ?

          AND memberships.term_id = ?

          AND users.is_active = 1

          AND roles.name IN (
              'HEAD',
              'SUB_HEAD'
          )

        ORDER BY

            CASE roles.name

                WHEN 'HEAD'
                THEN 1

                WHEN 'SUB_HEAD'
                THEN 2

                ELSE 3

            END,

            people.first_name,

            people.last_name
    """, (
        department_id,
        active_term_id,
    ))


    leadership = (
        cursor.fetchall()
    )


    conn.close()


    return render_template(
        "public/department_detail.html",

        department=(
            department
        ),

        description=(
            description
        ),

        leadership=(
            leadership
        ),
    )


# ========================================
# EVENTS
# ========================================

@public_bp.route(
    "/website/events"
)
def events():

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term_id = (
        get_active_term_id()
    )


    now = datetime.now()

    today = now.strftime(
        "%Y-%m-%d"
    )

    current_time = now.strftime(
        "%H:%M:%S"
    )


    # ========================================
    # NEXT / CURRENT EVENT
    # ACTIVE MANDATE ONLY
    # ========================================

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

            people.first_name
                AS leader_first_name,

            people.last_name
                AS leader_last_name

        FROM events

        JOIN memberships
            ON events.event_leader_membership_id =
               memberships.membership_id

        JOIN people
            ON memberships.person_id =
               people.person_id

        WHERE events.term_id = ?

          AND (
                events.end_date > ?

                OR (
                    events.end_date = ?

                    AND (
                        events.end_time IS NULL

                        OR events.end_time >= ?
                    )
                )
          )

        ORDER BY

            events.event_date ASC,

            CASE
                WHEN events.start_time IS NULL
                THEN 1
                ELSE 0
            END,

            events.start_time ASC

        LIMIT 1
    """, (
        active_term_id,
        today,
        today,
        current_time,
    ))


    next_event = (
        cursor.fetchone()
    )


    # ========================================
    # COUNTDOWN / EVENT STATUS
    # ========================================

    next_event_datetime = None

    event_in_progress = False


    if next_event is not None:

        event_date = str(
            next_event[
                "event_date"
            ]
        )

        start_time = (
            next_event[
                "start_time"
            ]
        )


        # ====================================
        # MULTI-DAY EVENT
        # ====================================

        if event_date < today:

            event_in_progress = True


        # ====================================
        # EVENT STARTS TODAY
        # ====================================

        elif event_date == today:

            if start_time:

                formatted_start_time = str(
                    start_time
                )


                if (
                    len(
                        formatted_start_time
                    )
                    == 5
                ):

                    formatted_start_time += (
                        ":00"
                    )


                if (
                    formatted_start_time
                    <= current_time
                ):

                    event_in_progress = True


                else:

                    next_event_datetime = (
                        f"{event_date}"
                        f"T{formatted_start_time}"
                    )


            else:

                event_in_progress = True


        # ====================================
        # FUTURE EVENT
        # ====================================

        else:

            if start_time:

                formatted_start_time = str(
                    start_time
                )


                if (
                    len(
                        formatted_start_time
                    )
                    == 5
                ):

                    formatted_start_time += (
                        ":00"
                    )


                next_event_datetime = (
                    f"{event_date}"
                    f"T{formatted_start_time}"
                )


    # ========================================
    # PAST EVENTS
    # ACTIVE + ARCHIVED ONLY
    # ========================================

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

            people.first_name
                AS leader_first_name,

            people.last_name
                AS leader_last_name

        FROM events

        JOIN memberships
            ON events.event_leader_membership_id =
               memberships.membership_id

        JOIN people
            ON memberships.person_id =
               people.person_id

        JOIN terms
            ON events.term_id =
               terms.term_id

        WHERE terms.status IN (
            'ACTIVE',
            'ARCHIVED'
        )

          AND (
                events.end_date < ?

                OR (
                    events.end_date = ?

                    AND events.end_time
                        IS NOT NULL

                    AND events.end_time < ?
                )
          )

        ORDER BY

            events.end_date DESC,

            CASE
                WHEN events.end_time IS NULL
                THEN 1
                ELSE 0
            END,

            events.end_time DESC,

            events.event_date DESC
    """, (
        today,
        today,
        current_time,
    ))


    past_events = (
        cursor.fetchall()
    )


    conn.close()


    return render_template(
        "public/events.html",

        next_event=(
            next_event
        ),

        next_event_datetime=(
            next_event_datetime
        ),

        event_in_progress=(
            event_in_progress
        ),

        past_events=(
            past_events
        ),
    )


# ========================================
# PUBLIC EVENT DETAIL
# PAST EVENTS ONLY
# ========================================

@public_bp.route(
    "/website/events/<int:event_id>"
)
def event_detail(
    event_id
):

    conn = get_db_connection()
    cursor = conn.cursor()


    now = datetime.now()

    today = now.strftime(
        "%Y-%m-%d"
    )

    current_time = now.strftime(
        "%H:%M:%S"
    )


    # ========================================
    # FINISHED EVENT
    # ACTIVE + ARCHIVED ONLY
    # ========================================

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

            people.first_name
                AS leader_first_name,

            people.last_name
                AS leader_last_name

        FROM events

        JOIN memberships
            ON events.event_leader_membership_id =
               memberships.membership_id

        JOIN people
            ON memberships.person_id =
               people.person_id

        JOIN terms
            ON events.term_id =
               terms.term_id

        WHERE events.event_id = ?

          AND terms.status IN (
              'ACTIVE',
              'ARCHIVED'
          )

          AND (
                events.end_date < ?

                OR (
                    events.end_date = ?

                    AND events.end_time
                        IS NOT NULL

                    AND events.end_time < ?
                )
          )
    """, (
        event_id,
        today,
        today,
        current_time,
    ))


    event = (
        cursor.fetchone()
    )


    if event is None:

        conn.close()

        return (
            "Event not found",
            404,
        )


    # ========================================
    # ORGANIZATIONS PRESENT
    # ========================================

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


    organizations = (
        cursor.fetchall()
    )


    conn.close()


    return render_template(
        "public/event_detail.html",

        event=event,

        organizations=(
            organizations
        ),
    )


# ========================================
# PUBLIC TRAININGS
# ========================================

@public_bp.route(
    "/website/trainings"
)
def trainings():

    conn = get_db_connection()
    cursor = conn.cursor()


    now = datetime.now()

    today = now.strftime(
        "%Y-%m-%d"
    )

    current_time = now.strftime(
        "%H:%M:%S"
    )


    # ========================================
    # ACTIVE + ARCHIVED TRAININGS
    # DRAFT IS HIDDEN
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

            (
                SELECT
                    training_media.training_media_id

                FROM training_media

                WHERE training_media.training_id =
                      trainings.training_id

                  AND training_media.media_type =
                      'image'

                  AND training_media.is_public = 1

                ORDER BY
                    training_media.uploaded_at ASC

                LIMIT 1
            ) AS cover_media_id

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
            trainings.training_id,
            trainings.title,
            trainings.description,
            trainings.training_date,
            trainings.start_time,
            trainings.end_time,
            trainings.location,
            trainings.registration_link,

            coach.first_name,
            coach.last_name,
            coach.profession

        ORDER BY
            trainings.training_date ASC
    """)


    all_trainings = (
        cursor.fetchall()
    )


    conn.close()


    # ========================================
    # UPCOMING / PAST
    # ========================================

    upcoming_trainings = []

    past_trainings = []


    for training in all_trainings:

        training_date = (
            training[
                "training_date"
            ]
        )

        training_end_time = (
            training[
                "end_time"
            ]
        )

        is_active_training = bool(
            training[
                "is_active_training"
            ]
        )


        # ====================================
        # NO DATE
        # Upcoming only if ACTIVE mandate
        # ====================================

        if training_date is None:

            if is_active_training:

                upcoming_trainings.append(
                    training
                )

            continue


        training_date = str(
            training_date
        )


        # ====================================
        # FUTURE
        # Only ACTIVE mandate
        # ====================================

        if training_date > today:

            if is_active_training:

                upcoming_trainings.append(
                    training
                )


        # ====================================
        # PAST
        # ACTIVE + ARCHIVED
        # ====================================

        elif training_date < today:

            past_trainings.append(
                training
            )


        # ====================================
        # TODAY
        # ====================================

        else:

            if training_end_time:

                formatted_end_time = str(
                    training_end_time
                )


                if (
                    len(
                        formatted_end_time
                    )
                    == 5
                ):

                    formatted_end_time += (
                        ":00"
                    )


                if (
                    formatted_end_time
                    < current_time
                ):

                    past_trainings.append(
                        training
                    )


                elif is_active_training:

                    upcoming_trainings.append(
                        training
                    )


            elif is_active_training:

                upcoming_trainings.append(
                    training
                )


    past_trainings.reverse()


    return render_template(
        "public/trainings.html",

        upcoming_trainings=(
            upcoming_trainings
        ),

        past_trainings=(
            past_trainings
        ),
    )


# ========================================
# PUBLIC TRAINING IMAGE
# ========================================

@public_bp.route(
    "/website/trainings/media/<int:training_media_id>"
)
def public_training_media(
    training_media_id
):

    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            training_media.training_media_id,
            training_media.media_type,
            training_media.file_path,
            training_media.original_filename,
            training_media.is_public

        FROM training_media

        WHERE training_media.training_media_id = ?

          AND EXISTS (
                SELECT 1

                FROM training_terms

                JOIN terms
                    ON training_terms.term_id =
                       terms.term_id

                WHERE training_terms.training_id =
                      training_media.training_id

                  AND terms.status IN (
                      'ACTIVE',
                      'ARCHIVED'
                  )
          )
    """, (
        training_media_id,
    ))


    media = (
        cursor.fetchone()
    )


    conn.close()


    if media is None:

        return (
            "Media not found",
            404,
        )


    if (
        media[
            "media_type"
        ]
        != "image"

        or not media[
            "is_public"
        ]
    ):

        return (
            "Media not available",
            404,
        )


    stored_filename = (
        os.path.basename(
            media[
                "file_path"
            ]
        )
    )


    upload_folder = os.path.join(
        current_app.root_path,
        "uploads",
        "trainings",
    )


    return send_from_directory(
        upload_folder,
        stored_filename,
        as_attachment=False,
        download_name=(
            media[
                "original_filename"
            ]
        ),
    )


# ========================================
# PUBLIC EVENT IMAGE
# ========================================

@public_bp.route(
    "/website/events/media/<int:event_media_id>"
)
def public_event_media(
    event_media_id
):

    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            event_media.event_media_id,
            event_media.event_id,
            event_media.media_type,
            event_media.file_path,
            event_media.is_public

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


    media = (
        cursor.fetchone()
    )


    conn.close()


    if media is None:

        return (
            "Media not found",
            404,
        )


    if (
        media[
            "media_type"
        ]
        != "image"

        or not media[
            "is_public"
        ]
    ):

        return (
            "Media not available",
            404,
        )


    stored_filename = (
        os.path.basename(
            media[
                "file_path"
            ]
        )
    )


    upload_folder = os.path.join(
        current_app.root_path,
        "uploads",
        "events",
        "media",
        str(
            media[
                "event_id"
            ]
        ),
    )


    return send_from_directory(
        upload_folder,
        stored_filename,
        as_attachment=False,
    )


# ========================================
# PUBLIC GALLERY
# EVENTS + TRAININGS
# ========================================

@public_bp.route(
    "/website/gallery"
)
def gallery():

    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            event_media.event_media_id
                AS media_id,

            'event'
                AS source_type,

            events.title
                AS source_title,

            events.event_date
                AS source_date

        FROM event_media

        JOIN events
            ON event_media.event_id =
               events.event_id

        JOIN terms AS event_terms
            ON events.term_id =
               event_terms.term_id

        WHERE event_media.media_type = 'image'

          AND event_media.is_public = 1

          AND event_terms.status IN (
              'ACTIVE',
              'ARCHIVED'
          )


        UNION ALL


        SELECT
            training_media.training_media_id
                AS media_id,

            'training'
                AS source_type,

            trainings.title
                AS source_title,

            trainings.training_date
                AS source_date

        FROM training_media

        JOIN trainings
            ON training_media.training_id =
               trainings.training_id

        WHERE training_media.media_type = 'image'

          AND training_media.is_public = 1

          AND EXISTS (
                SELECT 1

                FROM training_terms

                JOIN terms
                    AS training_terms_data

                    ON training_terms.term_id =
                       training_terms_data.term_id

                WHERE training_terms.training_id =
                      trainings.training_id

                  AND training_terms_data.status IN (
                      'ACTIVE',
                      'ARCHIVED'
                  )
          )

        ORDER BY
            source_date DESC,
            media_id DESC
    """)


    gallery_items = (
        cursor.fetchall()
    )


    conn.close()


    return render_template(
        "public/gallery.html",

        gallery_items=(
            gallery_items
        ),
    )


# ========================================
# PUBLIC CONTACT
# ========================================

@public_bp.route(
    "/website/contact",
    methods=[
        "GET",
        "POST",
    ],
)
def contact():

    error = None


    if request.method == "POST":

        sender_email = (
            request.form.get(
                "sender_email",
                "",
            ).strip()
        )


        message = (
            request.form.get(
                "message",
                "",
            ).strip()
        )


        # ====================================
        # VALIDATION
        # ====================================

        if not message:

            error = (
                "Please enter a message."
            )


        elif len(message) > 2000:

            error = (
                "Your message is too long."
            )


        else:

            conn = get_db_connection()
            cursor = conn.cursor()


            cursor.execute("""
                INSERT INTO contact_messages (
                    sender_type,
                    sender_email,
                    message,
                    is_read
                )

                VALUES (?, ?, ?, ?)
            """, (
                "guest",

                sender_email
                if sender_email
                else None,

                message,

                0,
            ))


            active_term_id = (
                get_active_term_id()
            )


            # ====================================
            # NOTIFY CURRENT CMS MEMBERS ONLY
            # ====================================

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
            """, (
                active_term_id,
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
                        "New guest message"
                    ),

                    message=(
                        "A new message was received "
                        "from the public website."
                    ),

                    target_url=(
                        "/announcements"
                        "#guest-messages"
                    ),

                    conn=conn,
                )


            conn.commit()

            conn.close()


            return redirect(
                url_for(
                    "public.contact",
                    sent="1",
                )
            )


    sent = (
        request.args.get(
            "sent"
        )
        == "1"
    )


    return render_template(
        "public/contact.html",

        sent=sent,

        error=error,
    )


# ========================================
# RESEARCH & INNOVATION
# ========================================

@public_bp.route(
    "/website/research-innovation"
)
def research_innovation():

    conn = get_db_connection()
    cursor = conn.cursor()


    # ========================================
    # PUBLIC PROJECTS
    # ACTIVE + ARCHIVED ONLY
    # ========================================

    cursor.execute("""
        SELECT
            projects.project_id,
            projects.name,
            projects.description,
            projects.project_link,

            people.first_name
                AS owner_first_name,

            people.last_name
                AS owner_last_name,

            GROUP_CONCAT(
                DISTINCT
                team_people.first_name
                || ' '
                || team_people.last_name
            ) AS team_names

        FROM projects

        JOIN memberships
            AS owner_membership

            ON projects.idea_owner_membership_id =
               owner_membership.membership_id

        JOIN people
            ON owner_membership.person_id =
               people.person_id

        LEFT JOIN project_members
            ON projects.project_id =
               project_members.project_id

        LEFT JOIN memberships
            AS team_membership

            ON project_members.membership_id =
               team_membership.membership_id

        LEFT JOIN people
            AS team_people

            ON team_membership.person_id =
               team_people.person_id

        WHERE projects.is_public = 1

          AND EXISTS (
                SELECT 1

                FROM project_terms

                JOIN terms
                    ON project_terms.term_id =
                       terms.term_id

                WHERE project_terms.project_id =
                      projects.project_id

                  AND terms.status IN (
                      'ACTIVE',
                      'ARCHIVED'
                  )
          )

        GROUP BY
            projects.project_id,
            projects.name,
            projects.description,
            projects.project_link,

            people.first_name,
            people.last_name

        ORDER BY
            projects.created_at DESC
    """)


    public_projects = (
        cursor.fetchall()
    )


    # ========================================
    # PUBLIC SCIENTIFIC ARTICLES
    # ACTIVE + ARCHIVED ONLY
    # ========================================

    cursor.execute("""
        SELECT
            scientific_articles.scientific_article_id,
            scientific_articles.title,
            scientific_articles.abstract,
            scientific_articles.publication_date,
            scientific_articles.file_path,
            scientific_articles.original_filename,

            owner_people.first_name
                AS owner_first_name,

            owner_people.last_name
                AS owner_last_name,

            GROUP_CONCAT(
                DISTINCT
                author_people.first_name
                || ' '
                || author_people.last_name
            ) AS author_names

        FROM scientific_articles

        JOIN memberships
            AS owner_membership

            ON scientific_articles.article_owner_membership_id =
               owner_membership.membership_id

        JOIN people
            AS owner_people

            ON owner_membership.person_id =
               owner_people.person_id

        LEFT JOIN article_authors
            ON scientific_articles.scientific_article_id =
               article_authors.scientific_article_id

        LEFT JOIN memberships
            AS author_membership

            ON article_authors.membership_id =
               author_membership.membership_id

        LEFT JOIN people
            AS author_people

            ON author_membership.person_id =
               author_people.person_id

        WHERE scientific_articles.is_public = 1

          AND scientific_articles.status =
              'completed'

          AND scientific_articles.file_path
              IS NOT NULL

          AND EXISTS (
                SELECT 1

                FROM article_terms

                JOIN terms
                    ON article_terms.term_id =
                       terms.term_id

                WHERE article_terms.scientific_article_id =
                      scientific_articles.scientific_article_id

                  AND terms.status IN (
                      'ACTIVE',
                      'ARCHIVED'
                  )
          )

        GROUP BY
            scientific_articles.scientific_article_id,
            scientific_articles.title,
            scientific_articles.abstract,
            scientific_articles.publication_date,
            scientific_articles.file_path,
            scientific_articles.original_filename,

            owner_people.first_name,
            owner_people.last_name

        ORDER BY
            scientific_articles.created_at DESC
    """)


    public_articles = (
        cursor.fetchall()
    )


    conn.close()


    return render_template(
        "public/research_innovation.html",

        projects=(
            public_projects
        ),

        articles=(
            public_articles
        ),
    )


# ========================================
# PUBLIC SCIENTIFIC ARTICLE PDF
# ========================================

@public_bp.route(
    "/website/articles/<int:article_id>/pdf"
)
def public_article_pdf(
    article_id
):

    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            scientific_articles.scientific_article_id,
            scientific_articles.file_path,
            scientific_articles.original_filename,
            scientific_articles.status,
            scientific_articles.is_public

        FROM scientific_articles

        WHERE scientific_articles.scientific_article_id = ?

          AND EXISTS (
                SELECT 1

                FROM article_terms

                JOIN terms
                    ON article_terms.term_id =
                       terms.term_id

                WHERE article_terms.scientific_article_id =
                      scientific_articles.scientific_article_id

                  AND terms.status IN (
                      'ACTIVE',
                      'ARCHIVED'
                  )
          )
    """, (
        article_id,
    ))


    article = (
        cursor.fetchone()
    )


    conn.close()


    if article is None:

        return (
            "Article not found",
            404,
        )


    if (
        not article[
            "is_public"
        ]

        or article[
            "status"
        ] != "completed"

        or not article[
            "file_path"
        ]
    ):

        return (
            "Article not available",
            404,
        )


    stored_filename = (
        os.path.basename(
            article[
                "file_path"
            ]
        )
    )


    upload_folder = os.path.join(
        current_app.root_path,
        "uploads",
        "articles",
    )


    return send_from_directory(
        upload_folder,
        stored_filename,
        mimetype=(
            "application/pdf"
        ),
        as_attachment=False,
        download_name=(
            article[
                "original_filename"
            ]
        ),
    )