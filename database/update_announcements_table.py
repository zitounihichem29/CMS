import sqlite3
import os


db_path = os.path.join(
    os.path.dirname(__file__),
    "rsclub.db"
)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")


# ========================================
# GET CURRENT COLUMNS
# ========================================

cursor.execute("PRAGMA table_info(announcements)")
columns = [row[1] for row in cursor.fetchall()]


# ========================================
# RENAME OLD COLUMNS
# ========================================

if (
    "author_membership_id" in columns
    and "created_by_membership_id" not in columns
):
    cursor.execute("""
        ALTER TABLE announcements
        RENAME COLUMN author_membership_id
        TO created_by_membership_id
    """)


if (
    "content" in columns
    and "message" not in columns
):
    cursor.execute("""
        ALTER TABLE announcements
        RENAME COLUMN content
        TO message
    """)


# Refresh columns
cursor.execute("PRAGMA table_info(announcements)")
columns = [row[1] for row in cursor.fetchall()]


# ========================================
# ADD NEW COLUMNS
# ========================================

if "visibility" not in columns:
    cursor.execute("""
        ALTER TABLE announcements
        ADD COLUMN visibility TEXT
        NOT NULL DEFAULT 'public'
        CHECK (
            visibility IN (
                'public',
                'personalized'
            )
        )
    """)


if "status" not in columns:
    cursor.execute("""
        ALTER TABLE announcements
        ADD COLUMN status TEXT
        NOT NULL DEFAULT 'active'
        CHECK (
            status IN (
                'active',
                'resolved'
            )
        )
    """)


if "updated_at" not in columns:
    cursor.execute("""
        ALTER TABLE announcements
        ADD COLUMN updated_at DATETIME
    """)


conn.commit()


# ========================================
# VERIFY
# ========================================

cursor.execute("PRAGMA table_info(announcements)")

print("ANNOUNCEMENTS columns:")

for column in cursor.fetchall():
    print("-", column[1])


conn.close()

print("Announcements table updated successfully.")