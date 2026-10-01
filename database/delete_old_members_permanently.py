import argparse
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

REAL_DB = BASE_DIR / "rsclub.db"

TEST_DB = (
    BASE_DIR
    / "delete_old_members_permanently_test.db"
)

BACKUP_DB = (
    BASE_DIR
    / "rsclub_backup_before_permanent_people_cleanup.db"
)


TARGET_PEOPLE = [
    ("asma", "benaoudia"),
    ("chouayb", "mokrani"),
    ("fadoua", "slimani"),
    ("merazga", "safouane"),
    ("serine", "mekdad"),
]


TARGET_DRAFT_TERM = "2026/2027"


def connect(path):

    conn = sqlite3.connect(
        path,
        timeout=10,
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


def q(name):

    return (
        '"'
        + name.replace(
            '"',
            '""',
        )
        + '"'
    )


# ============================================================
# FIND FOREIGN KEYS
# ============================================================

def tables_referencing(
    cursor,
    target_table,
):

    results = []

    tables = cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        """
    ).fetchall()

    for table in tables:

        table_name = table["name"]

        foreign_keys = cursor.execute(
            f"""
            PRAGMA foreign_key_list(
                {q(table_name)}
            )
            """
        ).fetchall()

        for fk in foreign_keys:

            if fk["table"] == target_table:

                results.append(
                    {
                        "table": table_name,
                        "column": fk["from"],
                        "target_column": fk["to"],
                    }
                )

    return results


# ============================================================
# FIND TARGET PEOPLE
# ============================================================

def find_targets(cursor):

    people = []

    for first_name, last_name in TARGET_PEOPLE:

        rows = cursor.execute(
            """
            SELECT
                person_id,
                first_name,
                last_name

            FROM people

            WHERE
                LOWER(TRIM(first_name)) = LOWER(?)
                AND
                LOWER(TRIM(last_name)) = LOWER(?)
            """,
            (
                first_name,
                last_name,
            ),
        ).fetchall()

        if len(rows) != 1:

            raise RuntimeError(
                f"{first_name} {last_name}: "
                f"expected exactly 1 PEOPLE row, "
                f"found {len(rows)}."
            )

        people.append(
            rows[0]
        )

    return people


# ============================================================
# PLAN + SAFETY CHECKS
# ============================================================

def build_plan(cursor):

    people = find_targets(
        cursor
    )

    person_ids = [
        row["person_id"]
        for row in people
    ]

    placeholders = ",".join(
        "?"
        for _ in person_ids
    )

    # ========================================================
    # CHECK DIRECT PEOPLE REFERENCES
    # ========================================================

    allowed_people_tables = {
        "applications",
        "person_skills",
    }

    people_references = tables_referencing(
        cursor,
        "people",
    )

    unexpected = []

    for reference in people_references:

        table_name = reference["table"]
        column_name = reference["column"]

        count = cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM {q(table_name)}
            WHERE {q(column_name)}
                  IN ({placeholders})
            """,
            person_ids,
        ).fetchone()[0]

        if (
            count
            and
            table_name
            not in allowed_people_tables
        ):

            unexpected.append(
                (
                    table_name,
                    column_name,
                    count,
                )
            )

    if unexpected:

        print(
            "UNEXPECTED PEOPLE REFERENCES:"
        )

        for row in unexpected:

            print(
                " -",
                row[0],
                ".",
                row[1],
                ":",
                row[2],
            )

        raise RuntimeError(
            "Permanent deletion blocked."
        )

    # ========================================================
    # APPLICATIONS
    # ========================================================

    applications = cursor.execute(
        f"""
        SELECT
            applications.application_id,
            applications.person_id,
            applications.status,

            terms.name AS term_name,
            terms.status AS term_status

        FROM applications

        JOIN application_periods
            ON application_periods.application_period_id =
               applications.application_period_id

        JOIN terms
            ON terms.term_id =
               application_periods.term_id

        WHERE applications.person_id
              IN ({placeholders})

        ORDER BY applications.application_id
        """,
        person_ids,
    ).fetchall()

    application_ids = [
        row["application_id"]
        for row in applications
    ]

    # Every application being deleted must belong
    # exclusively to the DRAFT 2026/2027 mandate.

    for application in applications:

        if (
            application["term_name"]
            != TARGET_DRAFT_TERM
            or
            application["term_status"]
            != "DRAFT"
        ):

            raise RuntimeError(
                (
                    "Application "
                    f"{application['application_id']} "
                    "does not belong to "
                    "2026/2027 DRAFT. "
                    "Deletion aborted."
                )
            )

    app_meeting_ids = []
    general_meeting_ids = []

    if application_ids:

        app_placeholders = ",".join(
            "?"
            for _ in application_ids
        )

        # ----------------------------------------------------
        # APPLICATION MEETINGS
        # ----------------------------------------------------

        rows = cursor.execute(
            f"""
            SELECT meeting_id

            FROM application_meetings

            WHERE application_id
                  IN ({app_placeholders})
            """,
            application_ids,
        ).fetchall()

        app_meeting_ids = [
            row["meeting_id"]
            for row in rows
        ]

        # ----------------------------------------------------
        # GENERAL MEETINGS LINKED TO APPLICATION
        # ----------------------------------------------------

        rows = cursor.execute(
            f"""
            SELECT meeting_id

            FROM meetings

            WHERE application_id
                  IN ({app_placeholders})
            """,
            application_ids,
        ).fetchall()

        general_meeting_ids = [
            row["meeting_id"]
            for row in rows
        ]

        # ----------------------------------------------------
        # VERIFY APPLICATION REFERENCES
        # ----------------------------------------------------

        application_references = (
            tables_referencing(
                cursor,
                "applications",
            )
        )

        allowed_application_tables = {
            "application_meetings",
            "meetings",
        }

        for reference in application_references:

            table_name = reference["table"]
            column_name = reference["column"]

            count = cursor.execute(
                f"""
                SELECT COUNT(*)

                FROM {q(table_name)}

                WHERE {q(column_name)}
                      IN ({app_placeholders})
                """,
                application_ids,
            ).fetchone()[0]

            if (
                count
                and
                table_name
                not in allowed_application_tables
            ):

                raise RuntimeError(
                    (
                        "Unexpected application "
                        "reference: "
                        f"{table_name}."
                        f"{column_name} "
                        f"({count} rows)"
                    )
                )

    # ========================================================
    # VERIFY APPLICATION_MEETING CHILDREN
    # ========================================================

    if app_meeting_ids:

        placeholders2 = ",".join(
            "?"
            for _ in app_meeting_ids
        )

        references = tables_referencing(
            cursor,
            "application_meetings",
        )

        for reference in references:

            table_name = reference["table"]
            column_name = reference["column"]

            count = cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM {q(table_name)}
                WHERE {q(column_name)}
                      IN ({placeholders2})
                """,
                app_meeting_ids,
            ).fetchone()[0]

            if (
                count
                and
                table_name
                != "application_meeting_participants"
            ):

                raise RuntimeError(
                    (
                        "Unexpected application "
                        "meeting reference: "
                        f"{table_name}."
                        f"{column_name}"
                    )
                )

    # ========================================================
    # VERIFY GENERAL MEETING CHILDREN
    # ========================================================

    if general_meeting_ids:

        placeholders3 = ",".join(
            "?"
            for _ in general_meeting_ids
        )

        references = tables_referencing(
            cursor,
            "meetings",
        )

        for reference in references:

            table_name = reference["table"]
            column_name = reference["column"]

            count = cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM {q(table_name)}
                WHERE {q(column_name)}
                      IN ({placeholders3})
                """,
                general_meeting_ids,
            ).fetchone()[0]

            if (
                count
                and
                table_name
                != "meeting_attendance"
            ):

                raise RuntimeError(
                    (
                        "Unexpected meeting "
                        "reference: "
                        f"{table_name}."
                        f"{column_name}"
                    )
                )

    return {
        "people": people,
        "person_ids": person_ids,
        "applications": applications,
        "application_ids": application_ids,
        "app_meeting_ids": app_meeting_ids,
        "general_meeting_ids":
            general_meeting_ids,
    }


# ============================================================
# DISPLAY PLAN
# ============================================================

def print_plan(plan):

    print(
        "========================================"
    )

    print(
        "PERMANENT PEOPLE CLEANUP PLAN"
    )

    print(
        "========================================"
    )

    print()

    for person in plan["people"]:

        print(
            "-",
            person["first_name"],
            person["last_name"],
            "| person_id =",
            person["person_id"],
        )

    print()

    print(
        "Applications to delete:",
        len(
            plan["application_ids"]
        ),
    )

    for application in plan[
        "applications"
    ]:

        print(
            "  - application_id =",
            application[
                "application_id"
            ],
            "|",
            application[
                "term_name"
            ],
            application[
                "term_status"
            ],
            "|",
            application[
                "status"
            ],
        )

    print(
        "Application meetings to delete:",
        len(
            plan["app_meeting_ids"]
        ),
    )

    print(
        "General meetings linked "
        "to those applications:",
        len(
            plan["general_meeting_ids"]
        ),
    )

    print()


# ============================================================
# APPLY CLEANUP
# ============================================================

def apply_cleanup(
    conn,
    plan,
):

    cursor = conn.cursor()

    person_ids = plan[
        "person_ids"
    ]

    application_ids = plan[
        "application_ids"
    ]

    app_meeting_ids = plan[
        "app_meeting_ids"
    ]

    general_meeting_ids = plan[
        "general_meeting_ids"
    ]

    conn.execute(
        "BEGIN IMMEDIATE"
    )

    try:

        # ====================================================
        # APPLICATION MEETING PARTICIPANTS
        # ====================================================

        if app_meeting_ids:

            placeholders = ",".join(
                "?"
                for _ in app_meeting_ids
            )

            cursor.execute(
                f"""
                DELETE FROM
                    application_meeting_participants

                WHERE meeting_id
                      IN ({placeholders})
                """,
                app_meeting_ids,
            )

            cursor.execute(
                f"""
                DELETE FROM
                    application_meetings

                WHERE meeting_id
                      IN ({placeholders})
                """,
                app_meeting_ids,
            )

        # ====================================================
        # GENERAL MEETINGS LINKED TO APPLICATIONS
        # ====================================================

        if general_meeting_ids:

            placeholders = ",".join(
                "?"
                for _ in general_meeting_ids
            )

            cursor.execute(
                f"""
                DELETE FROM meeting_attendance

                WHERE meeting_id
                      IN ({placeholders})
                """,
                general_meeting_ids,
            )

            cursor.execute(
                f"""
                DELETE FROM meetings

                WHERE meeting_id
                      IN ({placeholders})
                """,
                general_meeting_ids,
            )

        # ====================================================
        # APPLICATIONS
        # ====================================================

        if application_ids:

            placeholders = ",".join(
                "?"
                for _ in application_ids
            )

            cursor.execute(
                f"""
                DELETE FROM applications

                WHERE application_id
                      IN ({placeholders})
                """,
                application_ids,
            )

        # ====================================================
        # PERSON SKILLS
        # ====================================================

        placeholders = ",".join(
            "?"
            for _ in person_ids
        )

        cursor.execute(
            f"""
            DELETE FROM person_skills

            WHERE person_id
                  IN ({placeholders})
            """,
            person_ids,
        )

        # ====================================================
        # PEOPLE
        # ====================================================

        cursor.execute(
            f"""
            DELETE FROM people

            WHERE person_id
                  IN ({placeholders})
            """,
            person_ids,
        )

        conn.commit()

    except Exception:

        conn.rollback()

        raise


# ============================================================
# VERIFY
# ============================================================

def verify(conn):

    cursor = conn.cursor()

    errors = []

    # Targets must be gone.

    for first_name, last_name in TARGET_PEOPLE:

        count = cursor.execute(
            """
            SELECT COUNT(*)

            FROM people

            WHERE
                LOWER(TRIM(first_name))
                = LOWER(?)

              AND

                LOWER(TRIM(last_name))
                = LOWER(?)
            """,
            (
                first_name,
                last_name,
            ),
        ).fetchone()[0]

        if count != 0:

            errors.append(
                (
                    f"{first_name} "
                    f"{last_name} "
                    "still exists."
                )
            )

    # 2025/2026 must still be ACTIVE.

    active = cursor.execute(
        """
        SELECT status

        FROM terms

        WHERE name = '2025/2026'
        """
    ).fetchone()

    if (
        active is None
        or active["status"]
        != "ACTIVE"
    ):

        errors.append(
            "2025/2026 is no longer ACTIVE."
        )

    # 2026/2027 must still be DRAFT.

    draft = cursor.execute(
        """
        SELECT status

        FROM terms

        WHERE name = '2026/2027'
        """
    ).fetchone()

    if (
        draft is None
        or draft["status"]
        != "DRAFT"
    ):

        errors.append(
            "2026/2027 state changed."
        )

    integrity = cursor.execute(
        "PRAGMA integrity_check"
    ).fetchone()[0]

    foreign_keys = cursor.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    if integrity != "ok":

        errors.append(
            (
                "Integrity check: "
                f"{integrity}"
            )
        )

    if foreign_keys:

        errors.append(
            "Foreign key violations found."
        )

    return (
        integrity,
        foreign_keys,
        errors,
    )


# ============================================================
# TEST ON COPY
# ============================================================

def run_test():

    if TEST_DB.exists():

        TEST_DB.unlink()

    source = connect(
        REAL_DB
    )

    destination = sqlite3.connect(
        TEST_DB
    )

    try:

        source.backup(
            destination
        )

    finally:

        source.close()
        destination.close()

    try:

        conn = connect(
            TEST_DB
        )

        plan = build_plan(
            conn.cursor()
        )

        print_plan(
            plan
        )

        apply_cleanup(
            conn,
            plan,
        )

        (
            integrity,
            foreign_keys,
            errors,
        ) = verify(
            conn
        )

        conn.close()

        if errors:

            print(
                "TEST FAILED"
            )

            for error in errors:

                print(
                    "-",
                    error,
                )

            raise RuntimeError(
                "Test cleanup failed."
            )

        print(
            "========================================"
        )

        print(
            "PERMANENT CLEANUP TEST SUCCESSFUL"
        )

        print(
            "========================================"
        )

        print(
            "5 target people deleted: OK"
        )

        print(
            "Their test applications deleted: OK"
        )

        print(
            "Their test recruitment meetings deleted: OK"
        )

        print(
            "Their person skills deleted: OK"
        )

        print(
            "2025/2026 still ACTIVE: OK"
        )

        print(
            "2026/2027 still DRAFT: OK"
        )

        print(
            "Integrity check:",
            integrity,
        )

        print(
            "Foreign key check:",
            foreign_keys,
        )

    finally:

        if TEST_DB.exists():

            TEST_DB.unlink()

        print(
            "Temporary database deleted."
        )


# ============================================================
# BACKUP
# ============================================================

def create_backup():

    if BACKUP_DB.exists():

        print(
            "Backup already exists:"
        )

        print(
            BACKUP_DB
        )

        return

    source = connect(
        REAL_DB
    )

    destination = sqlite3.connect(
        BACKUP_DB
    )

    try:

        source.backup(
            destination
        )

    finally:

        source.close()
        destination.close()

    print(
        "Backup created:"
    )

    print(
        BACKUP_DB
    )


# ============================================================
# REAL APPLY
# ============================================================

def run_apply():

    conn = connect(
        REAL_DB
    )

    plan = build_plan(
        conn.cursor()
    )

    print_plan(
        plan
    )

    conn.close()

    create_backup()

    conn = connect(
        REAL_DB
    )

    plan = build_plan(
        conn.cursor()
    )

    apply_cleanup(
        conn,
        plan,
    )

    (
        integrity,
        foreign_keys,
        errors,
    ) = verify(
        conn
    )

    conn.close()

    if errors:

        print(
            "REAL CLEANUP VERIFICATION FAILED"
        )

        for error in errors:

            print(
                "-",
                error,
            )

        print(
            "Backup:",
            BACKUP_DB
        )

        raise RuntimeError(
            "Cleanup failed."
        )

    print(
        "========================================"
    )

    print(
        "PERMANENT PEOPLE CLEANUP SUCCESSFUL"
    )

    print(
        "========================================"
    )

    print(
        "5 target people deleted: OK"
    )

    print(
        "Test recruitment data removed: OK"
    )

    print(
        "2025/2026 still ACTIVE: OK"
    )

    print(
        "2026/2027 still DRAFT: OK"
    )

    print(
        "Integrity check:",
        integrity,
    )

    print(
        "Foreign key check:",
        foreign_keys,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--test",
        action="store_true",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
    )

    args = parser.parse_args()

    if (
        args.test
        and args.apply
    ):

        raise SystemExit(
            "Choose --test OR --apply."
        )

    if args.test:

        run_test()

    elif args.apply:

        run_apply()

    else:

        conn = connect(
            REAL_DB
        )

        plan = build_plan(
            conn.cursor()
        )

        print_plan(
            plan
        )

        conn.close()

        print(
            "DRY RUN ONLY."
        )


if __name__ == "__main__":

    main()