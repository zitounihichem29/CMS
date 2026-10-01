import sqlite3

conn = sqlite3.connect("rsclub.db")
cursor = conn.cursor()


# Ajouter review_status
try:
    cursor.execute("""
        ALTER TABLE tasks
        ADD COLUMN review_status TEXT
        NOT NULL DEFAULT 'not_reviewed'
    """)
except sqlite3.OperationalError:
    print("review_status existe déjà")


# Ajouter reviewed_by_membership_id
try:
    cursor.execute("""
        ALTER TABLE tasks
        ADD COLUMN reviewed_by_membership_id INTEGER
        REFERENCES memberships(membership_id)
    """)
except sqlite3.OperationalError:
    print("reviewed_by_membership_id existe déjà")


# Ajouter reviewed_at
try:
    cursor.execute("""
        ALTER TABLE tasks
        ADD COLUMN reviewed_at DATETIME
    """)
except sqlite3.OperationalError:
    print("reviewed_at existe déjà")


conn.commit()
conn.close()

print("Task review fields added successfully.")