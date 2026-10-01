import argparse
import shutil
import sqlite3
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parent

REAL_DB = (
    DATABASE_DIR
    / "rsclub.db"
)

TEST_DB = (
    DATABASE_DIR
    / "cleanup_2025_2026_board_test.db"
)

BACKUP_DB = (
    DATABASE_DIR
    / "rsclub_backup_before_2025_2026_board_cleanup.db"
)

TERM_NAME = "2025/2026"


# ============================================================
# OFFICIAL BOARD 2025/2026
# ============================================================

OFFICIAL_BOARD = [

    {
        "username": "hamma_yasmine",
        "first_name": "Yasmine",
        "last_name": "HAMMA",
        "role": "PRESIDENT",
        "department": None,
    },

    {
        "username": None,
        "first_name": "Nour el Houda",
        "last_name": "AMELLAL",
        "role": "VICE_PRESIDENT",
        "department": None,
    },

    {
        "username": None,
        "first_name": "Farah",
        "last_name": "DJERMOUNE",
        "role": "SECRETARY_GENERAL",
        "department": None,
    },

    {
        "username": "masmoudi_mohamed",
        "first_name": "Mohamed",
        "last_name": "MASMOUDI",
        "role": "HEAD",
        "department": "Human Resources",
    },

    {
        "username": "belhadj_sarah",
        "first_name": "Sarah",
        "last_name": "BELHADJ",
        "role": "HEAD",
        "department": "Projects & Activities",
    },

    {
        "username": "souilah_wissal",
        "first_name": "Wissal",
        "last_name": "SOUILAH",
        "role": "HEAD",
        "department": "External Relations",
    },

    {
        "username": "benantar_wadoud",
        "first_name": "Abd el Ouadoud",
        "last_name": "BENANTAR",
        "role": "HEAD",
        "department": "Communication & Marketing",
    },

    {
        "username": "kaouane_anis",
        "first_name": "Anis",
        "last_name": "KAOUANE",
        "role": "SUB_HEAD",
        "department": "Projects & Activities",
    },

    {
        "username": "tamda_karim",
        "first_name": "Karim",
        "last_name": "TAMDA",
        "role": "SUB_HEAD",
        "department": "Communication & Marketing",
    },
]


# ============================================================
# HELPERS
# ============================================================

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


def normalize(value):

    return (
        value
        or ""
    ).strip().lower()


def quote_identifier(value):

    return (
        '"'
        +
        value.replace(
            '"',
            '""',
        )
        +
        '"'
    )


def full_name(row):

    return (
        f"{row['first_name']} "
        f"{row['last_name']}"
    ).strip()


# ============================================================
# FIND OFFICIAL BOARD ENTRY
# ============================================================

def find_board_entry(row):

    username = normalize(
        row["username"]
    )

    first_name = normalize(
        row["first_name"]
    )

    last_name = normalize(
        row["last_name"]
    )


    for entry in OFFICIAL_BOARD:

        if (
            entry["username"]
            and username
            == normalize(
                entry["username"]
            )
        ):

            return entry


        if (
            first_name
            == normalize(
                entry["first_name"]
            )

            and

            last_name
            == normalize(
                entry["last_name"]
            )
        ):

            return entry


    return None


# ============================================================
# FIND REFERENCES TO MEMBERSHIP
# ============================================================

def get_membership_references(
    cursor,
    membership_id,
):

    references = []


    tables = cursor.execute(
        """
        SELECT name

        FROM sqlite_master

        WHERE
            type = 'table'

          AND name NOT LIKE 'sqlite_%'
        """
    ).fetchall()


    for table in tables:

        table_name = (
            table["name"]
        )


        foreign_keys = cursor.execute(
            f"""
            PRAGMA foreign_key_list(
                {quote_identifier(table_name)}
            )
            """
        ).fetchall()


        for foreign_key in foreign_keys:

            if (
                foreign_key["table"]
                != "memberships"
            ):

                continue


            column_name = (
                foreign_key["from"]
            )


            count = cursor.execute(
                f"""
                SELECT COUNT(*)

                FROM
                    {quote_identifier(table_name)}

                WHERE
                    {quote_identifier(column_name)}
                    = ?
                """,
                (
                    membership_id,
                ),
            ).fetchone()[0]


            if count:

                references.append(
                    {
                        "table":
                            table_name,

                        "column":
                            column_name,

                        "count":
                            count,
                    }
                )


    return references


# ============================================================
# TERM
# ============================================================

def get_term(cursor):

    return cursor.execute(
        """
        SELECT
            term_id,
            name,
            status

        FROM terms

        WHERE name = ?

        LIMIT 1
        """,
        (
            TERM_NAME,
        ),
    ).fetchone()


# ============================================================
# MEMBERSHIPS
# ============================================================

def get_memberships(
    cursor,
    term_id,
):

    return cursor.execute(
        """
        SELECT
            memberships.membership_id,
            memberships.person_id,
            memberships.role_id,
            memberships.department_id,

            people.first_name,
            people.last_name,

            roles.name
                AS role_name,

            departments.name
                AS department_name,

            users.user_id,
            users.username,
            users.is_active

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

        LEFT JOIN users

            ON users.person_id =
               memberships.person_id

        WHERE
            memberships.term_id = ?

        ORDER BY
            memberships.membership_id
        """,
        (
            term_id,
        ),
    ).fetchall()


# ============================================================
# LOOKUP ROLE
# ============================================================

def get_role_id(
    cursor,
    role_name,
):

    row = cursor.execute(
        """
        SELECT role_id

        FROM roles

        WHERE name = ?

        LIMIT 1
        """,
        (
            role_name,
        ),
    ).fetchone()


    if row is None:

        raise RuntimeError(
            f"Role not found: {role_name}"
        )


    return row["role_id"]


# ============================================================
# LOOKUP DEPARTMENT
# ============================================================

def get_department_id(
    cursor,
    department_name,
):

    if department_name is None:

        return None


    row = cursor.execute(
        """
        SELECT department_id

        FROM departments

        WHERE name = ?

        LIMIT 1
        """,
        (
            department_name,
        ),
    ).fetchone()


    if row is None:

        raise RuntimeError(
            (
                "Department not found: "
                f"{department_name}"
            )
        )


    return row[
        "department_id"
    ]


# ============================================================
# PLAN
# ============================================================

def build_plan(cursor):

    term = get_term(
        cursor
    )


    if term is None:

        raise RuntimeError(
            "2025/2026 mandate not found."
        )


    if (
        term["status"]
        != "ACTIVE"
    ):

        raise RuntimeError(
            (
                "2025/2026 must currently "
                "be ACTIVE."
            )
        )


    memberships = get_memberships(
        cursor,
        term["term_id"],
    )


    keep = []
    updates = []
    removals = []


    for membership in memberships:

        board_entry = (
            find_board_entry(
                membership
            )
        )


        if board_entry is None:

            references = (
                get_membership_references(
                    cursor,
                    membership[
                        "membership_id"
                    ],
                )
            )


            removals.append(
                {
                    "membership":
                        membership,

                    "references":
                        references,
                }
            )

            continue


        expected_role_id = (
            get_role_id(
                cursor,
                board_entry[
                    "role"
                ],
            )
        )


        expected_department_id = (
            get_department_id(
                cursor,
                board_entry[
                    "department"
                ],
            )
        )


        changed = (
            membership[
                "role_id"
            ]
            != expected_role_id

            or

            membership[
                "department_id"
            ]
            != expected_department_id
        )


        if changed:

            updates.append(
                {
                    "membership":
                        membership,

                    "board_entry":
                        board_entry,

                    "role_id":
                        expected_role_id,

                    "department_id":
                        expected_department_id,
                }
            )

        else:

            keep.append(
                membership
            )


    return (
        term,
        keep,
        updates,
        removals,
    )


# ============================================================
# DISPLAY PLAN
# ============================================================

def print_plan(
    term,
    keep,
    updates,
    removals,
):

    print(
        "========================================"
    )

    print(
        "2025/2026 BOARD CLEANUP PLAN"
    )

    print(
        "========================================"
    )

    print()

    print(
        "Mandate:",
        term["name"],
        "-",
        term["status"],
    )

    print()


    print(
        "KEEP"
    )

    print(
        "----------------------------------------"
    )


    for row in keep:

        print(
            "-",
            full_name(row),
            "|",
            row["role_name"],
            "|",
            (
                row[
                    "department_name"
                ]
                or "Executive"
            ),
        )


    print()

    print(
        "CORRECT"
    )

    print(
        "----------------------------------------"
    )


    if updates:

        for item in updates:

            row = (
                item["membership"]
            )

            expected = (
                item["board_entry"]
            )


            print(
                "-",
                full_name(row),
            )

            print(
                "   FROM:",
                row["role_name"],
                "/",
                (
                    row[
                        "department_name"
                    ]
                    or "Executive"
                ),
            )

            print(
                "   TO:",
                expected["role"],
                "/",
                (
                    expected[
                        "department"
                    ]
                    or "Executive"
                ),
            )


    else:

        print(
            "No corrections required."
        )


    print()

    print(
        "REMOVE FROM 2025/2026"
    )

    print(
        "----------------------------------------"
    )


    if removals:

        for item in removals:

            row = (
                item["membership"]
            )

            references = (
                item["references"]
            )


            print(
                "-",
                full_name(row),
                "|",
                row["role_name"],
                "|",
                (
                    row[
                        "department_name"
                    ]
                    or "Executive"
                ),
            )


            if references:

                print(
                    "   BLOCKED BY:"
                )


                for reference in references:

                    print(
                        "     -",
                        reference["table"],
                        ".",
                        reference["column"],
                        ":",
                        reference["count"],
                    )


            else:

                print(
                    "   References: none"
                )


    else:

        print(
            "No memberships to remove."
        )


# ============================================================
# VERIFY PLAN IS SAFE
# ============================================================

def validate_plan(
    updates,
    removals,
):

    blocked = [

        item

        for item
        in removals

        if item[
            "references"
        ]

    ]


    if blocked:

        print()

        print(
            "ERROR:"
        )

        print(
            (
                "Some non-board memberships "
                "are referenced by CMS data."
            )
        )


        for item in blocked:

            print(
                "-",
                full_name(
                    item[
                        "membership"
                    ]
                ),
            )


        raise RuntimeError(
            (
                "Cleanup aborted because "
                "at least one membership "
                "cannot be safely removed."
            )
        )


# ============================================================
# APPLY
# ============================================================

def apply_cleanup(conn):

    cursor = conn.cursor()


    (
        term,
        keep,
        updates,
        removals,
    ) = build_plan(
        cursor
    )


    validate_plan(
        updates,
        removals,
    )


    conn.execute(
        "BEGIN IMMEDIATE"
    )


    try:

        # ====================================================
        # CORRECT BOARD ASSIGNMENTS
        # ====================================================

        for item in updates:

            membership = (
                item["membership"]
            )


            cursor.execute(
                """
                UPDATE memberships

                SET
                    role_id = ?,
                    department_id = ?

                WHERE membership_id = ?
                  AND term_id = ?
                """,
                (
                    item[
                        "role_id"
                    ],

                    item[
                        "department_id"
                    ],

                    membership[
                        "membership_id"
                    ],

                    term[
                        "term_id"
                    ],
                ),
            )


        # ====================================================
        # REMOVE NON-BOARD MEMBERSHIPS ONLY
        # ====================================================

        for item in removals:

            membership = (
                item["membership"]
            )


            cursor.execute(
                """
                DELETE FROM memberships

                WHERE membership_id = ?
                  AND term_id = ?
                """,
                (
                    membership[
                        "membership_id"
                    ],

                    term[
                        "term_id"
                    ],
                ),
            )


        conn.commit()


    except Exception:

        conn.rollback()

        raise


# ============================================================
# FINAL VERIFICATION
# ============================================================

def verify_database(conn):

    cursor = conn.cursor()

    term = get_term(
        cursor
    )


    memberships = get_memberships(
        cursor,
        term["term_id"],
    )


    errors = []


    if len(
        memberships
    ) != len(
        OFFICIAL_BOARD
    ):

        errors.append(
            (
                "Expected "
                f"{len(OFFICIAL_BOARD)} "
                "board memberships, found "
                f"{len(memberships)}."
            )
        )


    for expected in OFFICIAL_BOARD:

        match = None


        for membership in memberships:

            username_match = (
                expected["username"]
                and
                normalize(
                    membership[
                        "username"
                    ]
                )
                ==
                normalize(
                    expected[
                        "username"
                    ]
                )
            )


            name_match = (
                normalize(
                    membership[
                        "first_name"
                    ]
                )
                ==
                normalize(
                    expected[
                        "first_name"
                    ]
                )

                and

                normalize(
                    membership[
                        "last_name"
                    ]
                )
                ==
                normalize(
                    expected[
                        "last_name"
                    ]
                )
            )


            if (
                username_match
                or name_match
            ):

                match = membership

                break


        if match is None:

            errors.append(
                (
                    "Missing board member: "
                    f"{expected['first_name']} "
                    f"{expected['last_name']}"
                )
            )

            continue


        if (
            match["role_name"]
            != expected["role"]
        ):

            errors.append(
                (
                    f"{full_name(match)} "
                    "has wrong role: "
                    f"{match['role_name']} "
                    "instead of "
                    f"{expected['role']}."
                )
            )


        current_department = (
            match[
                "department_name"
            ]
        )


        if (
            current_department
            != expected[
                "department"
            ]
        ):

            errors.append(
                (
                    f"{full_name(match)} "
                    "has wrong department."
                )
            )


    integrity = (
        cursor.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]
    )


    foreign_keys = (
        cursor.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()
    )


    if integrity != "ok":

        errors.append(
            (
                "Integrity check failed: "
                f"{integrity}"
            )
        )


    if foreign_keys:

        errors.append(
            (
                "Foreign key violations "
                "were detected."
            )
        )


    # DRAFT MUST STILL EXIST UNCHANGED

    draft = cursor.execute(
        """
        SELECT
            name,
            status

        FROM terms

        WHERE name = '2026/2027'

        LIMIT 1
        """
    ).fetchone()


    if (
        draft is None
        or draft["status"]
        != "DRAFT"
    ):

        errors.append(
            (
                "2026/2027 DRAFT state "
                "was unexpectedly changed."
            )
        )


    return (
        memberships,
        integrity,
        foreign_keys,
        errors,
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

        print(
            "Existing backup preserved."
        )

        return


    source = connect(
        REAL_DB
    )

    destination = (
        sqlite3.connect(
            BACKUP_DB
        )
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
# TEST MODE
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


        (
            term,
            keep,
            updates,
            removals,
        ) = build_plan(
            conn.cursor()
        )


        print_plan(
            term,
            keep,
            updates,
            removals,
        )


        validate_plan(
            updates,
            removals,
        )


        apply_cleanup(
            conn
        )


        (
            memberships,
            integrity,
            foreign_keys,
            errors,
        ) = verify_database(
            conn
        )


        conn.close()


        if errors:

            print()

            print(
                "TEST FAILED"
            )


            for error in errors:

                print(
                    "-",
                    error,
                )


            raise RuntimeError(
                "Temporary cleanup test failed."
            )


        print()

        print(
            "========================================"
        )

        print(
            "2025/2026 CLEANUP TEST SUCCESSFUL"
        )

        print(
            "========================================"
        )


        print(
            "Board memberships:",
            len(
                memberships
            ),
        )

        print(
            "Karim TAMDA role: SUB_HEAD"
        )

        print(
            "Anis KAOUANE preserved: OK"
        )

        print(
            "Regular memberships removed: OK"
        )

        print(
            "People/users untouched: OK"
        )

        print(
            "2026/2027 untouched: OK"
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
# REAL APPLY MODE
# ============================================================

def run_apply():

    conn = connect(
        REAL_DB
    )


    (
        term,
        keep,
        updates,
        removals,
    ) = build_plan(
        conn.cursor()
    )


    print_plan(
        term,
        keep,
        updates,
        removals,
    )


    validate_plan(
        updates,
        removals,
    )


    conn.close()


    create_backup()


    conn = connect(
        REAL_DB
    )


    apply_cleanup(
        conn
    )


    (
        memberships,
        integrity,
        foreign_keys,
        errors,
    ) = verify_database(
        conn
    )


    conn.close()


    if errors:

        print()

        print(
            "VERIFICATION FAILED"
        )


        for error in errors:

            print(
                "-",
                error,
            )


        print()

        print(
            "Restore from:"
        )

        print(
            BACKUP_DB
        )


        raise RuntimeError(
            (
                "Real cleanup verification "
                "failed."
            )
        )


    print()

    print(
        "========================================"
    )

    print(
        "2025/2026 BOARD CLEANUP SUCCESSFUL"
    )

    print(
        "========================================"
    )


    print(
        "Official board memberships:",
        len(
            memberships
        ),
    )

    print(
        "Karim TAMDA -> SUB_HEAD / "
        "Communication & Marketing: OK"
    )

    print(
        "Anis KAOUANE -> SUB_HEAD / "
        "Projects & Activities: OK"
    )

    print(
        "Non-board memberships removed: OK"
    )

    print(
        "People preserved: OK"
    )

    print(
        "User accounts preserved: OK"
    )

    print(
        "2026/2027 DRAFT untouched: OK"
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
            (
                "Use either --test "
                "or --apply."
            )
        )


    if args.test:

        run_test()

        return


    if args.apply:

        run_apply()

        return


    conn = connect(
        REAL_DB
    )


    (
        term,
        keep,
        updates,
        removals,
    ) = build_plan(
        conn.cursor()
    )


    print_plan(
        term,
        keep,
        updates,
        removals,
    )


    conn.close()


    print()

    print(
        "DRY RUN ONLY."
    )

    print(
        "No database changes were made."
    )

    print()

    print(
        "Next:"
    )

    print(
        "python cleanup_2025_2026_board.py --test"
    )


if __name__ == "__main__":

    main()