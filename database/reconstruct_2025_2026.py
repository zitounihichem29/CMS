import sqlite3
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

DATABASE_DIR = (
    Path(__file__).resolve().parent
)

DATABASE_PATH = (
    DATABASE_DIR
    / "rsclub.db"
)

BACKUP_PATH = (
    DATABASE_DIR
    / "rsclub_backup_before_real_2025_2026_reconstruction.db"
)


# ============================================================
# TARGET MANDATES
# ============================================================

TARGET_TERM_NAME = "2025/2026"

FUTURE_DRAFT_NAME = "2026/2027"


# ============================================================
# REAL 2025/2026 EXECUTIVE BOARD
#
# This is the authoritative board.
#
# Existing ordinary MEMBER / SUB_HEAD memberships are preserved.
# ============================================================

REAL_BOARD = [

    {
        "key": "president",

        "first_name": "Yasmine",
        "last_name": "HAMMA",

        "username": "hamma_yasmine",
        "email": None,

        "role": "PRESIDENT",
        "department": None,
    },


    {
        "key": "vice_president",

        "first_name": "Nour el Houda",
        "last_name": "AMELLAL",

        "username": None,
        "email": None,

        "role": "VICE_PRESIDENT",
        "department": None,
    },


    {
        "key": "secretary_general",

        "first_name": "Farah",
        "last_name": "DJERMOUNE",

        "username": None,
        "email": None,

        "role": "SECRETARY_GENERAL",
        "department": None,
    },


    {
        "key": "dpa_head",

        "first_name": "Sarah",
        "last_name": "BELHADJ",

        "username": "belhadj_sarah",
        "email":
            "sarahbelhadj.1902@gmail.com",

        "role": "HEAD",

        "department":
            "Projects & Activities",
    },


    {
        "key":
            "external_relations_head",

        "first_name": "Wissal",
        "last_name": "SOUILAH",

        "username":
            "souilah_wissal",

        "email":
            "souilahouisal16@gmail.com",

        "role": "HEAD",

        "department":
            "External Relations",
    },


    {
        "key":
            "communication_head_1",

        "first_name":
            "Abd el Ouadoud",

        "last_name":
            "BENANTAR",

        "username":
            "benantar_wadoud",

        "email": None,

        "role": "HEAD",

        "department":
            "Communication & Marketing",
    },


    {
        "key":
            "communication_head_2",

        "first_name":
            "Karim",

        "last_name":
            "TAMDA",

        "username":
            "tamda_karim",

        "email":
            "karimtamda@gmail.com",

        "role": "HEAD",

        "department":
            "Communication & Marketing",
    },


    {
        "key":
            "hr_head",

        "first_name":
            "Mohamed",

        "last_name":
            "MASMOUDI",

        "username":
            "masmoudi_mohamed",

        "email":
            "mohamedmasmoudi@gmail.com",

        "role":
            "HEAD",

        "department":
            "Human Resources",
    },

]


# ============================================================
# KNOWN DEVELOPMENT / TEST ACCOUNTS
#
# They are NOT deleted.
#
# We only deactivate them so:
# - existing FK references remain valid
# - application history is preserved
# - cleanup stays reversible
# ============================================================

KNOWN_TEST_USERNAMES = {

    "yacine_alumni",

    "belhadj_sarah2",

    "belhadj_sarah3",

    "smith_anais",

}


# ============================================================
# BOARD ROLES
# ============================================================

BOARD_ROLES = {

    "PRESIDENT",

    "VICE_PRESIDENT",

    "SECRETARY_GENERAL",

    "HEAD",

}


# ============================================================
# DATABASE CONNECTION
# ============================================================

def connect(
    db_path,
):

    conn = sqlite3.connect(
        db_path,
        timeout=10,
    )

    conn.row_factory = (
        sqlite3.Row
    )

    conn.execute(
        "PRAGMA foreign_keys = ON"
    )

    return conn


# ============================================================
# BACKUP
# ============================================================

def create_backup(
    source_path,
    backup_path,
):

    source = connect(
        source_path
    )

    destination = (
        sqlite3.connect(
            backup_path
        )
    )


    try:

        source.backup(
            destination
        )


    finally:

        destination.close()

        source.close()


# ============================================================
# TERM
# ============================================================

def get_term(
    cursor,
    name,
):

    cursor.execute(
        """
        SELECT
            term_id,
            name,
            start_date,
            end_date,
            status

        FROM terms

        WHERE name = ?

        LIMIT 1
        """,
        (
            name,
        ),
    )


    return (
        cursor.fetchone()
    )


# ============================================================
# ROLE
# ============================================================

def get_role_id(
    cursor,
    role_name,
):

    cursor.execute(
        """
        SELECT
            role_id

        FROM roles

        WHERE name = ?

        LIMIT 1
        """,
        (
            role_name,
        ),
    )


    row = (
        cursor.fetchone()
    )


    if row is None:

        raise RuntimeError(
            "Required role not found: "
            f"{role_name}"
        )


    return row[
        "role_id"
    ]


# ============================================================
# DEPARTMENT
# ============================================================

def get_department_id(
    cursor,
    department_name,
):

    if department_name is None:

        return None


    cursor.execute(
        """
        SELECT
            department_id

        FROM departments

        WHERE name = ?

        LIMIT 1
        """,
        (
            department_name,
        ),
    )


    row = (
        cursor.fetchone()
    )


    if row is None:

        raise RuntimeError(
            "Required department "
            "not found: "
            f"{department_name}"
        )


    return row[
        "department_id"
    ]


# ============================================================
# FIND PERSON
#
# Priority:
# 1. username
# 2. email
# 3. exact name
# ============================================================

def find_person(
    cursor,
    member,
):

    username = (
        member.get(
            "username"
        )
    )

    email = (
        member.get(
            "email"
        )
    )


    # ========================================================
    # USERNAME
    # ========================================================

    if username:

        cursor.execute(
            """
            SELECT
                people.person_id

            FROM users

            JOIN people
                ON users.person_id =
                   people.person_id

            WHERE LOWER(
                users.username
            ) = LOWER(?)

            LIMIT 1
            """,
            (
                username,
            ),
        )


        row = (
            cursor.fetchone()
        )


        if row is not None:

            return row[
                "person_id"
            ]


    # ========================================================
    # EMAIL
    # ========================================================

    if email:

        cursor.execute(
            """
            SELECT
                person_id

            FROM people

            WHERE email IS NOT NULL

              AND LOWER(email) =
                  LOWER(?)

            LIMIT 1
            """,
            (
                email,
            ),
        )


        row = (
            cursor.fetchone()
        )


        if row is not None:

            return row[
                "person_id"
            ]


    # ========================================================
    # NAME
    # ========================================================

    cursor.execute(
        """
        SELECT
            person_id

        FROM people

        WHERE LOWER(first_name) =
              LOWER(?)

          AND LOWER(last_name) =
              LOWER(?)

        ORDER BY
            person_id

        LIMIT 1
        """,
        (
            member[
                "first_name"
            ],

            member[
                "last_name"
            ],
        ),
    )


    row = (
        cursor.fetchone()
    )


    if row is not None:

        return row[
            "person_id"
        ]


    return None


# ============================================================
# RESOLVE OR CREATE PERSON
# ============================================================

def resolve_or_create_person(
    cursor,
    member,
):

    person_id = find_person(
        cursor,
        member,
    )


    # ========================================================
    # CREATE
    # ========================================================

    if person_id is None:

        cursor.execute(
            """
            INSERT INTO people (
                first_name,
                last_name,
                email,
                university
            )

            VALUES (?, ?, ?, ?)
            """,
            (
                member[
                    "first_name"
                ],

                member[
                    "last_name"
                ],

                member.get(
                    "email"
                ),

                "USTHB",
            ),
        )


        return (
            cursor.lastrowid,
            True,
        )


    # ========================================================
    # NORMALIZE AUTHORITATIVE NAME
    #
    # We do NOT overwrite:
    # email
    # phone
    # bio
    # social links
    # CV
    # profile photo
    # ========================================================

    cursor.execute(
        """
        UPDATE people

        SET
            first_name = ?,
            last_name = ?

        WHERE person_id = ?
        """,
        (
            member[
                "first_name"
            ],

            member[
                "last_name"
            ],

            person_id,
        ),
    )


    return (
        person_id,
        False,
    )


# ============================================================
# MEMBERSHIP REFERENCES
#
# Before deleting a wrong membership,
# verify that no other table depends on it.
# ============================================================

def membership_references(
    cursor,
    membership_id,
):

    references = []


    tables = [

        row[0]

        for row in cursor.execute(
            """
            SELECT
                name

            FROM sqlite_master

            WHERE type = 'table'

              AND name NOT LIKE
                  'sqlite_%'

            ORDER BY
                name
            """
        ).fetchall()

    ]


    for table in tables:

        foreign_keys = (
            cursor.execute(
                f'PRAGMA foreign_key_list("{table}")'
            ).fetchall()
        )


        for fk in foreign_keys:

            if (
                fk["table"]
                != "memberships"
            ):

                continue


            column = (
                fk["from"]
            )


            count = (
                cursor.execute(
                    f'''
                    SELECT COUNT(*)

                    FROM "{table}"

                    WHERE "{column}" = ?
                    ''',
                    (
                        membership_id,
                    ),
                ).fetchone()[0]
            )


            if count:

                references.append(
                    f"{table}.{column} "
                    f"({count})"
                )


    return references


# ============================================================
# UPSERT BOARD MEMBERSHIP
# ============================================================

def upsert_board_membership(
    cursor,
    term_id,
    person_id,
    role_name,
    department_name,
):

    role_id = get_role_id(
        cursor,
        role_name,
    )


    department_id = (
        get_department_id(
            cursor,
            department_name,
        )
    )


    cursor.execute(
        """
        INSERT INTO memberships (
            person_id,
            term_id,
            role_id,
            department_id
        )

        VALUES (?, ?, ?, ?)


        ON CONFLICT(
            person_id,
            term_id
        )

        DO UPDATE SET

            role_id =
                excluded.role_id,

            department_id =
                excluded.department_id
        """,
        (
            person_id,

            term_id,

            role_id,

            department_id,
        ),
    )


# ============================================================
# MAIN RECONSTRUCTION
# ============================================================

def reconstruct_database(
    db_path=DATABASE_PATH,
    create_backup_file=True,
    verbose=True,
):

    db_path = Path(
        db_path
    )


    if not db_path.exists():

        raise FileNotFoundError(
            "Database not found: "
            f"{db_path}"
        )


    # ========================================================
    # BACKUP
    # ========================================================

    if create_backup_file:

        if BACKUP_PATH.exists():

            BACKUP_PATH.unlink()


        create_backup(
            db_path,
            BACKUP_PATH,
        )


        if verbose:

            print(
                "Backup created:",
                BACKUP_PATH.name,
            )


    # ========================================================
    # DATABASE
    # ========================================================

    conn = connect(
        db_path
    )

    cursor = (
        conn.cursor()
    )


    try:

        # ====================================================
        # TERMS
        # ====================================================

        target_term = get_term(
            cursor,
            TARGET_TERM_NAME,
        )


        future_draft = get_term(
            cursor,
            FUTURE_DRAFT_NAME,
        )


        if target_term is None:

            raise RuntimeError(
                "Target mandate not found: "
                f"{TARGET_TERM_NAME}"
            )


        if (
            target_term[
                "status"
            ]
            != "ACTIVE"
        ):

            raise RuntimeError(
                f"{TARGET_TERM_NAME} "
                "must be ACTIVE during "
                "reconstruction. "
                "Current status: "
                f"{target_term['status']}"
            )


        if (
            future_draft is None
            or future_draft[
                "status"
            ]
            != "DRAFT"
        ):

            raise RuntimeError(
                f"{FUTURE_DRAFT_NAME} "
                "must remain the "
                "DRAFT mandate."
            )


        term_id = (
            target_term[
                "term_id"
            ]
        )


        # ====================================================
        # RESOLVE REAL BOARD
        # ====================================================

        resolved_board = []

        created_people = []


        for member in REAL_BOARD:

            (
                person_id,
                created,
            ) = (
                resolve_or_create_person(
                    cursor,
                    member,
                )
            )


            upsert_board_membership(
                cursor=cursor,

                term_id=term_id,

                person_id=person_id,

                role_name=member[
                    "role"
                ],

                department_name=member[
                    "department"
                ],
            )


            resolved_board.append(
                {
                    **member,

                    "person_id":
                        person_id,
                }
            )


            if created:

                created_people.append(
                    f"{member['first_name']} "
                    f"{member['last_name']}"
                )


        authoritative_board_person_ids = {

            member[
                "person_id"
            ]

            for member
            in resolved_board

        }


        # ====================================================
        # CURRENT 2025/2026 MEMBERSHIPS
        # ====================================================

        cursor.execute(
            """
            SELECT
                memberships.membership_id,
                memberships.person_id,

                people.first_name,
                people.last_name,

                roles.name
                    AS role_name,

                departments.name
                    AS department_name

            FROM memberships


            JOIN people

                ON memberships.person_id =
                   people.person_id


            JOIN roles

                ON memberships.role_id =
                   roles.role_id


            LEFT JOIN departments

                ON memberships.department_id =
                   departments.department_id


            WHERE memberships.term_id = ?


            ORDER BY

                memberships.membership_id
            """,
            (
                term_id,
            ),
        )


        current_memberships = (
            cursor.fetchall()
        )


        removed_memberships = []


        # ====================================================
        # REMOVE WRONG MEMBERSHIPS
        #
        # We remove:
        #
        # - ALUMNI from active 2025/2026 roster
        # - obsolete / wrong executive-board assignments
        #
        # We preserve ordinary MEMBER and SUB_HEAD rows.
        # ====================================================

        for row in current_memberships:

            should_remove = False


            # =================================================
            # NO ALUMNI INSIDE ACTIVE ROSTER
            # =================================================

            if (
                row[
                    "role_name"
                ]
                == "ALUMNI"
            ):

                should_remove = True


            # =================================================
            # OLD / WRONG BOARD MEMBER
            # =================================================

            elif (

                row[
                    "role_name"
                ]
                in BOARD_ROLES

                and

                row[
                    "person_id"
                ]
                not in
                authoritative_board_person_ids

            ):

                should_remove = True


            if not should_remove:

                continue


            # =================================================
            # FK SAFETY
            # =================================================

            refs = (
                membership_references(
                    cursor,
                    row[
                        "membership_id"
                    ],
                )
            )


            if refs:

                raise RuntimeError(
                    "Cannot safely remove "
                    "stale membership "
                    f"#{row['membership_id']} "
                    "for "
                    f"{row['first_name']} "
                    f"{row['last_name']}; "
                    "it is referenced by: "
                    + ", ".join(
                        refs
                    )
                )


            cursor.execute(
                """
                DELETE FROM memberships

                WHERE membership_id = ?
                """,
                (
                    row[
                        "membership_id"
                    ],
                ),
            )


            removed_memberships.append(
                f"{row['first_name']} "
                f"{row['last_name']} "
                f"({row['role_name']})"
            )


        # ====================================================
        # DEACTIVATE KNOWN TEST ACCOUNTS
        #
        # We DO NOT delete users or people here.
        # ====================================================

        deactivated_test_users = []


        for username in sorted(
            KNOWN_TEST_USERNAMES
        ):

            cursor.execute(
                """
                SELECT
                    user_id,
                    is_active

                FROM users

                WHERE LOWER(username) =
                      LOWER(?)

                LIMIT 1
                """,
                (
                    username,
                ),
            )


            user = (
                cursor.fetchone()
            )


            if user is None:

                continue


            if (
                user[
                    "is_active"
                ]
                != 0
            ):

                cursor.execute(
                    """
                    UPDATE users

                    SET is_active = 0

                    WHERE user_id = ?
                    """,
                    (
                        user[
                            "user_id"
                        ],
                    ),
                )


                deactivated_test_users.append(
                    username
                )


        # ====================================================
        # VALIDATE EXECUTIVE ROLES
        # ====================================================

        cursor.execute(
            """
            SELECT
                roles.name
                    AS role_name,

                COUNT(*)
                    AS total

            FROM memberships


            JOIN roles

                ON memberships.role_id =
                   roles.role_id


            WHERE memberships.term_id = ?

              AND roles.name IN (
                  'PRESIDENT',
                  'VICE_PRESIDENT',
                  'SECRETARY_GENERAL'
              )


            GROUP BY

                roles.name
            """,
            (
                term_id,
            ),
        )


        executive_counts = {

            row[
                "role_name"
            ]:
                row[
                    "total"
                ]

            for row
            in cursor.fetchall()

        }


        for role_name in (

            "PRESIDENT",

            "VICE_PRESIDENT",

            "SECRETARY_GENERAL",

        ):

            if (
                executive_counts.get(
                    role_name,
                    0,
                )
                != 1
            ):

                raise RuntimeError(
                    "Reconstruction "
                    "produced an invalid "
                    f"{role_name} count."
                )


        # ====================================================
        # VERIFY NO ALUMNI MEMBERSHIP
        # ====================================================

        cursor.execute(
            """
            SELECT
                COUNT(*)

            FROM memberships


            JOIN roles

                ON memberships.role_id =
                   roles.role_id


            WHERE memberships.term_id = ?

              AND roles.name = 'ALUMNI'
            """,
            (
                term_id,
            ),
        )


        if (
            cursor.fetchone()[0]
            != 0
        ):

            raise RuntimeError(
                "ALUMNI memberships still "
                "exist in the active "
                "2025/2026 roster."
            )


        # ====================================================
        # VERIFY EVERY REAL BOARD MEMBER
        # ====================================================

        for member in resolved_board:

            cursor.execute(
                """
                SELECT
                    roles.name
                        AS role_name,

                    departments.name
                        AS department_name

                FROM memberships


                JOIN roles

                    ON memberships.role_id =
                       roles.role_id


                LEFT JOIN departments

                    ON memberships.department_id =
                       departments.department_id


                WHERE memberships.term_id = ?

                  AND memberships.person_id = ?


                LIMIT 1
                """,
                (
                    term_id,

                    member[
                        "person_id"
                    ],
                ),
            )


            row = (
                cursor.fetchone()
            )


            if row is None:

                raise RuntimeError(
                    "Missing reconstructed "
                    "board member: "
                    f"{member['key']}"
                )


            if (
                row[
                    "role_name"
                ]
                != member[
                    "role"
                ]
            ):

                raise RuntimeError(
                    "Wrong role after "
                    "reconstruction: "
                    f"{member['key']}"
                )


            if (
                row[
                    "department_name"
                ]
                != member[
                    "department"
                ]
            ):

                raise RuntimeError(
                    "Wrong department "
                    "after reconstruction: "
                    f"{member['key']}"
                )


        # ====================================================
        # DATABASE HEALTH
        # ====================================================

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

            raise RuntimeError(
                "Integrity check failed: "
                f"{integrity}"
            )


        if foreign_keys:

            raise RuntimeError(
                "Foreign key check failed: "
                f"{foreign_keys}"
            )


        # ====================================================
        # COMMIT
        # ====================================================

        conn.commit()


        # ====================================================
        # REPORT
        # ====================================================

        if verbose:

            print()

            print(
                "========================================"
            )

            print(
                "2025/2026 RECONSTRUCTION SUCCESSFUL"
            )

            print(
                "========================================"
            )


            print(
                "Target mandate:",
                TARGET_TERM_NAME,
                "ACTIVE",
            )


            print(
                "Future mandate:",
                FUTURE_DRAFT_NAME,
                "DRAFT (unchanged)",
            )


            print(
                "Authoritative board members:",
                len(
                    resolved_board
                ),
            )


            print(
                "New people created:",
                len(
                    created_people
                ),
            )


            for name in created_people:

                print(
                    "  +",
                    name,
                )


            print(
                "Stale memberships removed:",
                len(
                    removed_memberships
                ),
            )


            for name in removed_memberships:

                print(
                    "  -",
                    name,
                )


            print(
                "Known test users deactivated:",
                len(
                    deactivated_test_users
                ),
            )


            for username in (
                deactivated_test_users
            ):

                print(
                    "  -",
                    username,
                )


            print(
                "Integrity check:",
                integrity,
            )


            print(
                "Foreign key check:",
                foreign_keys,
            )


        return {

            "term_id":
                term_id,

            "resolved_board":
                resolved_board,

            "created_people":
                created_people,

            "removed_memberships":
                removed_memberships,

            "deactivated_test_users":
                deactivated_test_users,

            "integrity":
                integrity,

            "foreign_keys":
                foreign_keys,

        }


    except Exception:

        conn.rollback()

        raise


    finally:

        conn.close()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    reconstruct_database()