import sqlite3


conn = sqlite3.connect("rsclub.db")
cursor = conn.cursor()

cursor.execute("PRAGMA foreign_keys = ON")


# ========================================
# ANNOUNCEMENTS
# ========================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS announcements (
        announcement_id INTEGER PRIMARY KEY,

        created_by_membership_id INTEGER NOT NULL,

        title TEXT NOT NULL,
        message TEXT NOT NULL,

        visibility TEXT NOT NULL DEFAULT 'public',

        status TEXT NOT NULL DEFAULT 'active',

        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME,

        FOREIGN KEY (created_by_membership_id)
            REFERENCES memberships(membership_id),

        CHECK (
            visibility IN (
                'public',
                'personalized'
            )
        ),

        CHECK (
            status IN (
                'active',
                'resolved'
            )
        )
    )
""")


# ========================================
# ANNOUNCEMENT RECIPIENTS
# ========================================

cursor.execute("""
    CREATE TABLE IF NOT EXISTS announcement_recipients (
        announcement_recipient_id INTEGER PRIMARY KEY,

        announcement_id INTEGER NOT NULL UNIQUE,
        recipient_membership_id INTEGER NOT NULL,

        is_read BOOLEAN NOT NULL DEFAULT 0,
        read_at DATETIME,

        FOREIGN KEY (announcement_id)
            REFERENCES announcements(announcement_id),

        FOREIGN KEY (recipient_membership_id)
            REFERENCES memberships(membership_id)
    )
""")


conn.commit()


# ========================================
# VERIFY
# ========================================

cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
      AND name IN (
          'announcements',
          'announcement_recipients'
      )
    ORDER BY name
""")

tables = cursor.fetchall()

print("Created tables:")
for table in tables:
    print("-", table[0])


conn.close()

print("Announcements migration completed successfully.")