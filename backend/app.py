import os

from extensions import limiter

from datetime import datetime

from flask import (
    Flask,
    render_template,
    session,
    redirect
)

from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect

from permissions import login_required

from database import get_db_connection
from context import get_current_user, get_active_term_id


# ============================================================
# BLUEPRINTS
# ============================================================

from routes.departments import departments_bp
from routes.members import members_bp
from routes.dashboard import dashboard_bp
from routes.tasks import tasks_bp
from routes.announcements import announcements_bp
from routes.trainings import trainings_bp
from routes.events import events_bp
from routes.projects import projects_bp
from routes.articles import articles_bp
from routes.template_library import templates_bp
from routes.organizations import organizations_bp
from routes.applications import applications_bp
from routes.notifications import notifications_bp
from routes.profile import profile_bp
from routes.settings import settings_bp
from routes.public import public_bp
from routes.auth import auth_bp
from routes.mandates import mandates_bp
from routes.alumni import alumni_bp
from routes.public_alumni import public_alumni_bp
from routes.records import records_bp



# ============================================================
# FLASK APP
# ============================================================

load_dotenv()
app = Flask(__name__)

APP_ENV = os.getenv(
    "APP_ENV",
    "development"
)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "dev-secret-key"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True

app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

app.config["SESSION_COOKIE_SECURE"] = (
    APP_ENV == "production"
)


# ============================================================
# FILE UPLOAD CONFIGURATION
# ============================================================

UPLOAD_FOLDER = os.path.join(
    app.root_path,
    "uploads",
    "tasks"
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Maximum file size: 100 MB
app.config["MAX_CONTENT_LENGTH"] = (
    100 * 1024 * 1024
)


os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)



csrf = CSRFProtect(app)


# ============================================================
# CURRENT USER CONTEXT
# ============================================================

@app.context_processor
def inject_current_user():

    user = get_current_user()

    return {
        "current_user": user
    }


# ============================================================
# NOTIFICATION COUNT CONTEXT
# ============================================================

@app.context_processor
def inject_notification_count():

    if "user_id" not in session:

        return {
            "unread_notification_count": 0
        }


    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            COUNT(*) AS total

        FROM notifications

        WHERE recipient_user_id = ?
          AND is_read = 0
    """, (
        session["user_id"],
    ))


    result = cursor.fetchone()

    conn.close()


    return {
        "unread_notification_count":
            result["total"]
    }


app.config["RATELIMIT_STORAGE_URI"] = os.getenv(
    "RATELIMIT_STORAGE_URI",
    "memory://"
)

app.config["RATELIMIT_HEADERS_ENABLED"] = True

limiter.init_app(app)


# ============================================================
# REGISTER BLUEPRINTS
# ============================================================

app.register_blueprint(
    departments_bp
)

app.register_blueprint(
    members_bp
)

app.register_blueprint(
    dashboard_bp
)

app.register_blueprint(
    tasks_bp
)

app.register_blueprint(
    announcements_bp
)

app.register_blueprint(
    trainings_bp
)

app.register_blueprint(
    events_bp
)

app.register_blueprint(
    projects_bp
)

app.register_blueprint(
    articles_bp
)

app.register_blueprint(
    templates_bp
)

app.register_blueprint(
    organizations_bp
)

app.register_blueprint(
    applications_bp
)

app.register_blueprint(
    notifications_bp
)

app.register_blueprint(
    profile_bp
)

app.register_blueprint(
    settings_bp
)

app.register_blueprint(
    public_bp
)

app.register_blueprint(
    auth_bp
)

app.register_blueprint(
    mandates_bp
)


app.register_blueprint(
    alumni_bp
)


app.register_blueprint(
    public_alumni_bp
)


app.register_blueprint(
    records_bp
)


# ============================================================
# HOME
# ============================================================

@app.route("/")
@app.route("/home")
@login_required
def home_page():

    conn = get_db_connection()
    cursor = conn.cursor()


    user_id = session["user_id"]


    now = datetime.now()

    today = now.strftime(
        "%Y-%m-%d"
    )

    current_time = now.strftime(
        "%H:%M:%S"
    )


    # ========================================================
    # CURRENT USER
    # ========================================================

    cursor.execute("""
        SELECT
            users.user_id,
            people.person_id,
            people.first_name,
            people.last_name

        FROM users

        JOIN people
            ON users.person_id =
               people.person_id

        WHERE users.user_id = ?
    """, (
        user_id,
    ))


    user = cursor.fetchone()


    if user is None:

        conn.close()

        return redirect(
            "/login"
        )

    # ========================================================
    # ACTIVE TERM
    # ========================================================

    active_term_id = get_active_term_id()

    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503
        )


    # ========================================================
    # CURRENT MEMBERSHIP
    # ========================================================

    cursor.execute("""
        SELECT
            memberships.membership_id

        FROM memberships

        JOIN users
            ON memberships.person_id =
               users.person_id

        WHERE users.user_id = ?
          AND memberships.term_id = ?

        LIMIT 1
    """, (
        user_id,
        active_term_id,
    ))


    current_membership = (
        cursor.fetchone()
    )


    # ========================================================
    # COMING UP FOR YOU
    # ========================================================

    next_task = None
    next_training = None
    next_meeting = None


    if current_membership is not None:

        current_membership_id = (
            current_membership[
                "membership_id"
            ]
        )


        # ====================================================
        # NEXT TASK
        # ====================================================

        cursor.execute("""
            SELECT
                tasks.task_id,
                tasks.title,
                tasks.description,
                tasks.due_date,
                tasks.status

            FROM tasks

            JOIN task_assignees
                ON tasks.task_id =
                   task_assignees.task_id

            WHERE
                task_assignees.membership_id = ?

                AND tasks.status !=
                    'completed'

            ORDER BY

                CASE
                    WHEN tasks.due_date
                         IS NULL
                    THEN 1

                    ELSE 0
                END,

                tasks.due_date ASC,
                tasks.created_at ASC

            LIMIT 1
        """, (
            current_membership_id,
        ))


        next_task = (
            cursor.fetchone()
        )


        # ====================================================
        # NEXT TRAINING
        # CURRENT TERM
        # ====================================================

        cursor.execute("""
            SELECT
                trainings.training_id,
                trainings.title,
                trainings.training_date,
                trainings.start_time,
                trainings.location

            FROM trainings

            JOIN training_terms
                ON trainings.training_id =
                   training_terms.training_id

            WHERE
                training_terms.term_id = ?

                AND trainings.training_date >= ?

            ORDER BY
                trainings.training_date ASC,
                trainings.start_time ASC

            LIMIT 1
        """, (
            active_term_id,
            today,
        ))


        next_training = (
            cursor.fetchone()
        )


        # ====================================================
        # NEXT MEETING
        # ====================================================

        cursor.execute("""
            SELECT DISTINCT
                meetings.meeting_id,
                meetings.title,
                meetings.meeting_date,
                meetings.start_time,
                meetings.location

            FROM meetings

            LEFT JOIN meeting_attendance
                ON meetings.meeting_id =
                   meeting_attendance.meeting_id

            WHERE
                meetings.meeting_date >= ?

                AND (
                    meetings.organizer_membership_id = ?

                    OR

                    meeting_attendance.membership_id = ?
                )

            ORDER BY
                meetings.meeting_date ASC,
                meetings.start_time ASC

            LIMIT 1
        """, (
            today,
            current_membership_id,
            current_membership_id
        ))


        next_meeting = (
            cursor.fetchone()
        )


    # ========================================================
    # PENDING TASKS
    # ========================================================

    pending_tasks_count = 0


    if current_membership is not None:

        cursor.execute("""
            SELECT
                COUNT(
                    DISTINCT tasks.task_id
                ) AS total

            FROM tasks

            JOIN task_assignees
                ON tasks.task_id =
                   task_assignees.task_id

            WHERE
                task_assignees.membership_id = ?

                AND tasks.status =
                    'pending'
        """, (
            current_membership[
                "membership_id"
            ],
        ))


        pending_tasks_count = (
            cursor.fetchone()[
                "total"
            ]
        )


    # ========================================================
    # UNREAD NOTIFICATIONS
    # ========================================================

    cursor.execute("""
        SELECT
            COUNT(*) AS total

        FROM notifications

        WHERE recipient_user_id = ?
          AND is_read = 0
    """, (
        user_id,
    ))


    unread_notification_count = (
        cursor.fetchone()[
            "total"
        ]
    )


    # ========================================================
    # NEXT EVENT
    # ========================================================

    now = datetime.now()

    today = now.strftime(
        "%Y-%m-%d"
    )

    current_time = now.strftime(
        "%H:%M:%S"
    )


    cursor.execute("""
        SELECT

            event_id,
            title,
            description,
            event_date,
            start_time,
            end_time,
            location

        FROM events

        WHERE
            term_id = ?

            AND (
                event_date > ?

                OR (
                    event_date = ?

                    AND (
                        start_time IS NULL
                        OR start_time >= ?
                    )
                )
            )

        ORDER BY
            event_date ASC,

            CASE
                WHEN start_time IS NULL
                THEN 1
                ELSE 0
            END,

            start_time ASC

        LIMIT 1
    """, (
        active_term_id,
        today,
        today,
        current_time
    ))


    next_event = (
        cursor.fetchone()
    )


    # ========================================================
    # EVENT DATETIME FOR COUNTDOWN
    # ========================================================

    next_event_datetime = None


    if (
        next_event is not None
        and next_event["start_time"]
    ):

        event_time = str(
            next_event[
                "start_time"
            ]
        )


        if len(event_time) == 5:

            event_time += ":00"


        next_event_datetime = (
            f"{next_event['event_date']}"
            f"T{event_time}"
        )


    conn.close()


    return render_template(
        "index.html",

        first_name=user[
            "first_name"
        ],

        last_name=user[
            "last_name"
        ],

        user_id=user[
            "user_id"
        ],

        next_event=next_event,

        next_event_datetime=(
            next_event_datetime
        ),

        pending_tasks_count=(
            pending_tasks_count
        ),

        unread_notification_count=(
            unread_notification_count
        ),

        next_task=next_task,

        next_training=next_training,

        next_meeting=next_meeting
    )


# ============================================================
# HELP PAGE
# ============================================================

@app.route("/help")
@login_required
def help_page():

    return render_template(
        "help.html"
    )







# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        "/login"
    )


# ============================================================
# RUN APPLICATION
# MUST STAY AT THE END OF THIS FILE
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=(
            os.getenv(
                "FLASK_DEBUG",
                "0"
            ) == "1"
        )
    )