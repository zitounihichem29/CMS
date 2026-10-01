import sqlite3

db_path = "rsclub.db"

conn = sqlite3.connect(db_path)

conn.execute("""
CREATE TABLE IF NOT EXISTS task_attachments (
    task_attachment_id INTEGER PRIMARY KEY,

    task_id INTEGER NOT NULL,
    uploaded_by_membership_id INTEGER NOT NULL,

    original_filename TEXT NOT NULL,
    stored_filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    mime_type TEXT,
    file_size INTEGER,

    uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (task_id)
        REFERENCES tasks(task_id),

    FOREIGN KEY (uploaded_by_membership_id)
        REFERENCES memberships(membership_id)
);
""")

conn.commit()
conn.close()

print("TASK_ATTACHMENTS table added successfully.")