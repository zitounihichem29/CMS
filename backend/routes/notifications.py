from flask import Blueprint, render_template, redirect, url_for

from database import get_db_connection
from permissions import login_required
from context import get_current_user


notifications_bp = Blueprint(
    "notifications",
    __name__
)


# ========================================
# CREATE NOTIFICATION
# Used by tasks / announcements
# ========================================

def create_notification(
    recipient_user_id,
    notification_type,
    title,
    message,
    target_url=None,
    conn=None
):

    own_connection = False

    if conn is None:
        conn = get_db_connection()
        own_connection = True

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO notifications (
            recipient_user_id,
            notification_type,
            title,
            message,
            target_url
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        recipient_user_id,
        notification_type,
        title,
        message,
        target_url
    ))

    if own_connection:
        conn.commit()
        conn.close()


# ========================================
# NOTIFICATIONS PAGE
# ========================================

@notifications_bp.route("/notifications")
@login_required
def notifications():

    current_user = get_current_user()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            notification_id,
            notification_type,
            title,
            message,
            target_url,
            is_read,
            created_at,
            read_at
        FROM notifications
        WHERE recipient_user_id = ?
        ORDER BY
            is_read ASC,
            created_at DESC
    """, (
        current_user["user_id"],
    ))

    user_notifications = cursor.fetchall()

    conn.close()

    return render_template(
        "notifications.html",
        notifications=user_notifications
    )


# ========================================
# OPEN NOTIFICATION
# Mark as read + redirect
# ========================================

@notifications_bp.route(
    "/notifications/<int:notification_id>/open"
)
@login_required
def open_notification(notification_id):

    current_user = get_current_user()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            notification_id,
            target_url
        FROM notifications
        WHERE notification_id = ?
          AND recipient_user_id = ?
    """, (
        notification_id,
        current_user["user_id"]
    ))

    notification = cursor.fetchone()

    if notification is None:
        conn.close()
        return "Notification not found", 404

    cursor.execute("""
        UPDATE notifications
        SET
            is_read = 1,
            read_at = CURRENT_TIMESTAMP
        WHERE notification_id = ?
          AND recipient_user_id = ?
    """, (
        notification_id,
        current_user["user_id"]
    ))

    conn.commit()
    conn.close()

    if notification["target_url"]:
        return redirect(
            notification["target_url"]
        )

    return redirect(
        url_for("notifications.notifications")
    )


# ========================================
# MARK ALL AS READ
# ========================================

@notifications_bp.route(
    "/notifications/read-all",
    methods=["POST"]
)
@login_required
def mark_all_as_read():

    current_user = get_current_user()

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE notifications
        SET
            is_read = 1,
            read_at = CURRENT_TIMESTAMP
        WHERE recipient_user_id = ?
          AND is_read = 0
    """, (
        current_user["user_id"],
    ))

    conn.commit()
    conn.close()

    return redirect(
        url_for("notifications.notifications")
    )