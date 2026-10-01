import json
import sqlite3
from pathlib import Path


DATABASE_DIR = (
    Path(__file__).resolve().parent
)

DATABASE_PATH = (
    DATABASE_DIR
    / "rsclub.db"
)

BACKUP_PATH = (
    DATABASE_DIR
    / "rsclub_backup_before_history_2025_2026.db"
)

PENDING_PATH = (
    DATABASE_DIR
    / "history_2025_2026_pending.json"
)

REPORT_PATH = (
    DATABASE_DIR
    / "history_2025_2026_report.txt"
)


ACTIVE_TERM_NAME = "2025/2026"

DRAFT_TERM_NAME = "2026/2027"


# ============================================================
# OBVIOUS TEST DATA
#
# Only rows that are clearly test / gibberish are removed.
#
# We intentionally preserve plausible records such as:
# - python
# - netcom project
# - cutting stock problem
# - optimisation combinatoire
# ============================================================

OBVIOUS_TEST_TRAINING_TITLES = {
    "jhgf",
}


OBVIOUS_TEST_PROJECT_NAMES = {
    "kkf",
    ";hekawjh",
}


OBVIOUS_TEST_ARTICLE_TITLES = {
    "pdf article test",
    "hgfkfm",
    "kejfhkjwfhlgf",
}


# ============================================================
# CONFIRMED ORGANIZATIONS
#
# Important:
# relation_type = "other" is used when we know the
# organization was associated with ORigin but the precise
# sponsor/partner category was not supplied.
#
# This avoids inventing a relationship type.
# ============================================================

CONFIRMED_ORGANIZATIONS = [

    {
        "name":
            "Sonatrach",

        "organization_type":
            "company",

        "relation_type":
            "other",

        "description":
            (
                "Associated with ORSC's ORigin activities "
                "during the 2025/2026 mandate. "
                "The exact sponsor/partner category is "
                "intentionally left unclassified."
            ),
    },


    {
        "name":
            "Air Algérie",

        "organization_type":
            "company",

        "relation_type":
            "other",

        "description":
            (
                "Associated with ORSC's ORigin activities "
                "during the 2025/2026 mandate. "
                "The exact sponsor/partner category is "
                "intentionally left unclassified."
            ),
    },


    {
        "name":
            "Hydrapharm",

        "organization_type":
            "company",

        "relation_type":
            "other",

        "description":
            (
                "Associated with ORSC's ORigin activities "
                "during the 2025/2026 mandate. "
                "The exact sponsor/partner category is "
                "intentionally left unclassified."
            ),
    },


    {
        "name":
            "Algérie Télécom",

        "organization_type":
            "company",

        "relation_type":
            "other",

        "description":
            (
                "Associated with ORSC's ORigin activities "
                "during the 2025/2026 mandate. "
                "The exact sponsor/partner category is "
                "intentionally left unclassified."
            ),
    },


    {
        "name":
            "Setram",

        "organization_type":
            "company",

        "relation_type":
            "other",

        "description":
            (
                "Associated with ORSC's ORigin activities "
                "during the 2025/2026 mandate. "
                "The exact sponsor/partner category is "
                "intentionally left unclassified."
            ),
    },


    {
        "name":
            "Physica",

        "organization_type":
            "club",

        "relation_type":
            "collaboration",

        "description":
            (
                "Scientific-club collaboration around "
                "the 'Mission vers Mars' talk."
            ),
    },


    {
        "name":
            "Axis",

        "organization_type":
            "club",

        "relation_type":
            "collaboration",

        "description":
            (
                "Scientific-club collaboration around "
                "the 'Diabetes Care' talk."
            ),
    },

]


# ============================================================
# REAL HISTORY THAT IS STILL INCOMPLETE
#
# These are real facts that were provided previously,
# but one or more mandatory CMS fields are missing.
#
# We preserve them instead of inventing values.
# ============================================================

PENDING_HISTORY = {

    "term":
        ACTIVE_TERM_NAME,


    "purpose":
        (
            "Verified 2025/2026 history that cannot yet "
            "be inserted safely into the native CMS tables "
            "because one or more mandatory fields were not "
            "supplied. These facts are preserved here "
            "instead of inventing dates, coaches, event "
            "leaders or project idea owners."
        ),


    # ========================================================
    # EVENTS
    # ========================================================

    "events": [

        {
            "title":
                "Build It Your Way",

            "event_date":
                "2025-12-16",

            "known_details":
                "UI/UX + HTML/CSS event.",

            "missing_required_fields": [
                "event_leader_membership_id",
            ],
        },


        {
            "title":
                "Ramadan Game Nights",

            "event_date":
                None,

            "known_details":
                "Ramadan game-night activity.",

            "missing_required_fields": [
                "event_date",
                "event_leader_membership_id",
            ],
        },


        {
            "title":
                "Mission vers Mars",

            "event_date":
                None,

            "known_details":
                "ORSC × Physica scientific talk.",

            "organizations": [
                "Physica",
            ],

            "missing_required_fields": [
                "event_date",
                "event_leader_membership_id",
            ],
        },


        {
            "title":
                "Diabetes Care",

            "event_date":
                None,

            "known_details":
                "ORSC × Axis talk.",

            "organizations": [
                "Axis",
            ],

            "missing_required_fields": [
                "event_date",
                "event_leader_membership_id",
            ],
        },


        {
            "title":
                "ORigin",

            "event_date":
                "2026-04",

            "known_details":
                (
                    "ORigin event in April 2026. "
                    "Organizations mentioned: Sonatrach, "
                    "Air Algérie, Hydrapharm, "
                    "Algérie Télécom, Setram and two "
                    "startups whose names are not available."
                ),

            "organizations": [
                "Sonatrach",
                "Air Algérie",
                "Hydrapharm",
                "Algérie Télécom",
                "Setram",
            ],

            "missing_required_fields": [
                "exact_event_date",
                "event_leader_membership_id",
            ],
        },


        {
            "title":
                "ORigin 2.0 – The New Era",

            "event_date":
                "2026-06-27",

            "end_date":
                "2026-06-29",

            "location":
                "USTHB",

            "known_details":
                (
                    "Three-day ORSC event with approximately "
                    "50 participants. ADR was mentioned for gifts, "
                    "Jil FM for communication, BBC School for "
                    "catering, and École Les Aurès for desired "
                    "accommodation/transport support."
                ),

            "missing_required_fields": [
                "event_leader_membership_id",
            ],
        },

    ],


    # ========================================================
    # TRAININGS
    # ========================================================

    "trainings": [

        {
            "title":
                "Python",

            "known_details":
                "Introductory Python training.",

            "missing_required_fields": [
                "coach_person_id",
                "exact_training_date",
            ],
        },


        {
            "title":
                "Graphic Design",

            "known_details":
                "Graphic design training.",

            "missing_required_fields": [
                "coach_person_id",
                "exact_training_date",
            ],
        },


        {
            "title":
                "UI/UX",

            "known_details":
                "UI/UX training.",

            "missing_required_fields": [
                "coach_person_id",
                "exact_training_date",
            ],
        },


        {
            "title":
                "Web Front-end",

            "known_details":
                (
                    "Four sessions of approximately "
                    "1h30 each."
                ),

            "missing_required_fields": [
                "coach_person_id",
                "exact_training_dates",
            ],
        },


        {
            "title":
                "Database",

            "known_details":
                "Database fundamentals training.",

            "missing_required_fields": [
                "coach_person_id",
                "exact_training_date",
            ],
        },

    ],


    # ========================================================
    # PROJECTS
    # ========================================================

    "projects": [

        {
            "name":
                "Knapsack Camp Project",

            "known_details":
                (
                    "Mini-project based on "
                    "the Knapsack Problem."
                ),

            "missing_required_fields": [
                "idea_owner_membership_id",
            ],
        },


        {
            "name":
                "Maze Shortest Path",

            "known_details":
                (
                    "Mini-project on shortest-path "
                    "methods in a maze."
                ),

            "missing_required_fields": [
                "idea_owner_membership_id",
            ],
        },


        {
            "name":
                "Kherrouba Waste TSP",

            "known_details":
                (
                    "TSP mini-project related to "
                    "waste collection in Kherrouba."
                ),

            "missing_required_fields": [
                "idea_owner_membership_id",
            ],
        },


        {
            "name":
                "USTHB Maximum Coverage",

            "known_details":
                (
                    "Maximum coverage mini-project "
                    "with p = 3 at USTHB."
                ),

            "missing_required_fields": [
                "idea_owner_membership_id",
            ],
        },


        {
            "name":
                "Multi-Agent Traffic Simulation",

            "known_details":
                (
                    "Traffic simulation mini-project "
                    "using a multi-agent approach."
                ),

            "missing_required_fields": [
                "idea_owner_membership_id",
            ],
        },


        {
            "name":
                "Netcom Waste Collection VRP",

            "known_details":
                (
                    "Netcom waste-collection collaboration/"
                    "project concept using VRP. "
                    "Agreement was conditional on a DG letter; "
                    "later discussed as a hackathon theme whose "
                    "winning solution could become an ORSC product."
                ),

            "missing_required_fields": [
                "confirmed_idea_owner_membership_id",
                "confirmed_relation_status",
            ],
        },

    ],

}


# ============================================================
# DATABASE
# ============================================================

def connect(
    path,
):

    conn = sqlite3.connect(
        path,
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

    if backup_path.exists():

        backup_path.unlink()


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
            name,
        ),
    ).fetchone()


# ============================================================
# ORGANIZATION RECORD STEWARD
#
# organizations.created_by_membership_id is mandatory.
#
# For historical imports we use the current External
# Relations leadership as technical record steward.
#
# This does NOT mean they historically created or owned
# the external relationship.
# ============================================================

def get_external_relations_steward_membership(
    cursor,
    term_id,
):

    row = cursor.execute(
        """
        SELECT
            memberships.membership_id

        FROM memberships

        JOIN roles

            ON memberships.role_id =
               roles.role_id

        JOIN departments

            ON memberships.department_id =
               departments.department_id

        WHERE memberships.term_id = ?

          AND departments.name =
              'External Relations'

          AND roles.name IN (
              'HEAD',
              'SUB_HEAD'
          )

        ORDER BY

            CASE roles.name

                WHEN 'HEAD'
                    THEN 1

                ELSE 2

            END,

            memberships.membership_id

        LIMIT 1
        """,
        (
            term_id,
        ),
    ).fetchone()


    if row:

        return row[
            "membership_id"
        ]


    # ========================================================
    # FALLBACK
    # ========================================================

    row = cursor.execute(
        """
        SELECT
            memberships.membership_id

        FROM memberships

        JOIN roles

            ON memberships.role_id =
               roles.role_id

        WHERE memberships.term_id = ?

          AND roles.name IN (
              'PRESIDENT',
              'VICE_PRESIDENT',
              'SECRETARY_GENERAL',
              'HEAD',
              'SUB_HEAD',
              'MEMBER'
          )

        ORDER BY
            memberships.membership_id

        LIMIT 1
        """,
        (
            term_id,
        ),
    ).fetchone()


    if row:

        return row[
            "membership_id"
        ]


    raise RuntimeError(
        "No active 2025/2026 membership "
        "is available to own imported "
        "organization records."
    )


# ============================================================
# DELETE OBVIOUS FAKE TRAININGS
# ============================================================

def delete_fake_training_records(
    cursor,
):

    removed = []


    titles = {

        value.lower()

        for value
        in OBVIOUS_TEST_TRAINING_TITLES

    }


    rows = cursor.execute(
        """
        SELECT
            training_id,
            title

        FROM trainings
        """
    ).fetchall()


    for row in rows:

        title = (
            row[
                "title"
            ]
            or ""
        ).strip().lower()


        if title not in titles:

            continue


        training_id = (
            row[
                "training_id"
            ]
        )


        cursor.execute(
            """
            DELETE FROM training_attendance

            WHERE training_id = ?
            """,
            (
                training_id,
            ),
        )


        cursor.execute(
            """
            DELETE FROM training_media

            WHERE training_id = ?
            """,
            (
                training_id,
            ),
        )


        cursor.execute(
            """
            DELETE FROM training_terms

            WHERE training_id = ?
            """,
            (
                training_id,
            ),
        )


        cursor.execute(
            """
            DELETE FROM trainings

            WHERE training_id = ?
            """,
            (
                training_id,
            ),
        )


        removed.append(
            row[
                "title"
            ]
        )


    return removed


# ============================================================
# DELETE OBVIOUS FAKE PROJECTS
# ============================================================

def delete_fake_project_records(
    cursor,
):

    removed = []


    names = {

        value.lower()

        for value
        in OBVIOUS_TEST_PROJECT_NAMES

    }


    rows = cursor.execute(
        """
        SELECT
            project_id,
            name

        FROM projects
        """
    ).fetchall()


    for row in rows:

        name = (
            row[
                "name"
            ]
            or ""
        ).strip().lower()


        if name not in names:

            continue


        project_id = (
            row[
                "project_id"
            ]
        )


        cursor.execute(
            """
            DELETE FROM project_members

            WHERE project_id = ?
            """,
            (
                project_id,
            ),
        )


        cursor.execute(
            """
            DELETE FROM project_volunteers

            WHERE project_id = ?
            """,
            (
                project_id,
            ),
        )


        cursor.execute(
            """
            DELETE FROM project_terms

            WHERE project_id = ?
            """,
            (
                project_id,
            ),
        )


        cursor.execute(
            """
            DELETE FROM projects

            WHERE project_id = ?
            """,
            (
                project_id,
            ),
        )


        removed.append(
            row[
                "name"
            ]
        )


    return removed


# ============================================================
# DELETE OBVIOUS FAKE ARTICLES
# ============================================================

def delete_fake_article_records(
    cursor,
):

    removed = []


    titles = {

        value.lower()

        for value
        in OBVIOUS_TEST_ARTICLE_TITLES

    }


    rows = cursor.execute(
        """
        SELECT
            scientific_article_id,
            title

        FROM scientific_articles
        """
    ).fetchall()


    for row in rows:

        title = (
            row[
                "title"
            ]
            or ""
        ).strip().lower()


        if title not in titles:

            continue


        article_id = (
            row[
                "scientific_article_id"
            ]
        )


        cursor.execute(
            """
            DELETE FROM article_authors

            WHERE scientific_article_id = ?
            """,
            (
                article_id,
            ),
        )


        cursor.execute(
            """
            DELETE FROM article_source_references

            WHERE scientific_article_id = ?
            """,
            (
                article_id,
            ),
        )


        cursor.execute(
            """
            DELETE FROM article_volunteers

            WHERE scientific_article_id = ?
            """,
            (
                article_id,
            ),
        )


        cursor.execute(
            """
            DELETE FROM article_terms

            WHERE scientific_article_id = ?
            """,
            (
                article_id,
            ),
        )


        cursor.execute(
            """
            DELETE FROM scientific_articles

            WHERE scientific_article_id = ?
            """,
            (
                article_id,
            ),
        )


        removed.append(
            row[
                "title"
            ]
        )


    return removed


# ============================================================
# ORGANIZATION
# ============================================================

def ensure_organization(
    cursor,
    item,
    steward_membership_id,
    term_id,
):

    # ========================================================
    # CASE-INSENSITIVE LOOKUP
    # ========================================================

    row = cursor.execute(
        """
        SELECT
            organization_id

        FROM organizations

        WHERE LOWER(name) =
              LOWER(?)

        ORDER BY
            organization_id

        LIMIT 1
        """,
        (
            item[
                "name"
            ],
        ),
    ).fetchone()


    created = False


    if row is None:

        cursor.execute(
            """
            INSERT INTO organizations (

                name,

                organization_type,

                description,

                created_by_membership_id
            )

            VALUES (?, ?, ?, ?)
            """,
            (
                item[
                    "name"
                ],

                item[
                    "organization_type"
                ],

                item[
                    "description"
                ],

                steward_membership_id,
            ),
        )


        organization_id = (
            cursor.lastrowid
        )


        created = True


    else:

        organization_id = (
            row[
                "organization_id"
            ]
        )


    # ========================================================
    # RELATIONSHIP WITH 2025/2026
    #
    # Existing relation is preserved unchanged.
    # ========================================================

    existing_relation = (
        cursor.execute(
            """
            SELECT
                organization_relation_id

            FROM organization_relations

            WHERE organization_id = ?

              AND term_id = ?

            LIMIT 1
            """,
            (
                organization_id,

                term_id,
            ),
        ).fetchone()
    )


    relation_created = False


    if existing_relation is None:

        cursor.execute(
            """
            INSERT INTO organization_relations (

                organization_id,

                term_id,

                relation_type,

                description,

                start_date,

                end_date
            )

            VALUES (
                ?,
                ?,
                ?,
                ?,
                NULL,
                NULL
            )
            """,
            (
                organization_id,

                term_id,

                item[
                    "relation_type"
                ],

                item[
                    "description"
                ],
            ),
        )


        relation_created = True


    return (
        organization_id,
        created,
        relation_created,
    )


# ============================================================
# PENDING HISTORY FILE
# ============================================================

def write_pending_history(
    path,
):

    path = Path(
        path
    )


    path.write_text(

        json.dumps(
            PENDING_HISTORY,

            ensure_ascii=False,

            indent=2,
        ),

        encoding="utf-8",
    )


# ============================================================
# REPORT
# ============================================================

def write_report(
    path,
    result,
):

    lines = [

        "ORSC 2025/2026 HISTORY RECONSTRUCTION REPORT",

        "=" * 48,

        "",

        f"Active mandate: {ACTIVE_TERM_NAME}",

        f"Future draft preserved: {DRAFT_TERM_NAME}",

        "",

        (
            "Fake trainings removed: "
            f"{len(result['removed_trainings'])}"
        ),

    ]


    for item in result[
        "removed_trainings"
    ]:

        lines.append(
            f"  - {item}"
        )


    lines.extend(
        [
            "",

            (
                "Fake projects removed: "
                f"{len(result['removed_projects'])}"
            ),
        ]
    )


    for item in result[
        "removed_projects"
    ]:

        lines.append(
            f"  - {item}"
        )


    lines.extend(
        [
            "",

            (
                "Fake articles removed: "
                f"{len(result['removed_articles'])}"
            ),
        ]
    )


    for item in result[
        "removed_articles"
    ]:

        lines.append(
            f"  - {item}"
        )


    lines.extend(
        [
            "",

            (
                "Confirmed organizations available: "
                f"{len(result['organizations'])}"
            ),
        ]
    )


    for item in result[
        "organizations"
    ]:

        lines.append(
            f"  - {item}"
        )


    lines.extend(
        [
            "",

            (
                "Organization relations created this run: "
                f"{result['relations_created']}"
            ),

            "",

            (
                "Incomplete historical activities "
                "were NOT fabricated."
            ),

            (
                "They are preserved in: "
                f"{Path(result['pending_path']).name}"
            ),

            "",

            (
                "Integrity check: "
                f"{result['integrity']}"
            ),

            (
                "Foreign key check: "
                f"{result['foreign_keys']}"
            ),
        ]
    )


    Path(
        path
    ).write_text(

        "\n".join(
            lines
        )
        + "\n",

        encoding="utf-8",
    )


# ============================================================
# MAIN
# ============================================================

def reconstruct_history(

    db_path=DATABASE_PATH,

    create_backup_file=True,

    backup_path=BACKUP_PATH,

    pending_path=PENDING_PATH,

    report_path=REPORT_PATH,

    verbose=True,

):

    db_path = Path(
        db_path
    )


    backup_path = Path(
        backup_path
    )


    pending_path = Path(
        pending_path
    )


    report_path = Path(
        report_path
    )


    if not db_path.exists():

        raise FileNotFoundError(
            f"Database not found: {db_path}"
        )


    # ========================================================
    # BACKUP
    # ========================================================

    if create_backup_file:

        create_backup(
            db_path,
            backup_path,
        )


        if verbose:

            print(
                "Backup created:",
                backup_path.name,
            )


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

        active_term = (
            get_term(
                cursor,
                ACTIVE_TERM_NAME,
            )
        )


        draft_term = (
            get_term(
                cursor,
                DRAFT_TERM_NAME,
            )
        )


        if (

            active_term is None

            or

            active_term[
                "status"
            ]
            != "ACTIVE"

        ):

            raise RuntimeError(
                f"{ACTIVE_TERM_NAME} must "
                "be ACTIVE before historical "
                "reconstruction."
            )


        if (

            draft_term is None

            or

            draft_term[
                "status"
            ]
            != "DRAFT"

        ):

            raise RuntimeError(
                f"{DRAFT_TERM_NAME} must "
                "remain DRAFT during "
                "historical reconstruction."
            )


        # ====================================================
        # SNAPSHOT FUTURE MEMBERSHIPS
        # ====================================================

        draft_membership_count_before = (

            cursor.execute(
                """
                SELECT
                    COUNT(*)

                FROM memberships

                WHERE term_id = ?
                """,
                (
                    draft_term[
                        "term_id"
                    ],
                ),
            ).fetchone()[0]

        )


        # ====================================================
        # BEGIN
        # ====================================================

        conn.execute(
            "BEGIN IMMEDIATE"
        )


        # ====================================================
        # CLEAN OBVIOUS TEST DATA
        # ====================================================

        removed_trainings = (
            delete_fake_training_records(
                cursor
            )
        )


        removed_projects = (
            delete_fake_project_records(
                cursor
            )
        )


        removed_articles = (
            delete_fake_article_records(
                cursor
            )
        )


        # ====================================================
        # ORGANIZATIONS
        # ====================================================

        steward_membership_id = (
            get_external_relations_steward_membership(
                cursor,
                active_term[
                    "term_id"
                ],
            )
        )


        organization_names = []

        relations_created = 0


        for item in (
            CONFIRMED_ORGANIZATIONS
        ):

            (
                organization_id,
                organization_created,
                relation_created,
            ) = ensure_organization(

                cursor,

                item,

                steward_membership_id,

                active_term[
                    "term_id"
                ],
            )


            organization_names.append(
                item[
                    "name"
                ]
            )


            relations_created += int(
                relation_created
            )


        # ====================================================
        # FUTURE DRAFT MEMBERSHIPS MUST NOT CHANGE
        # ====================================================

        draft_membership_count_after = (

            cursor.execute(
                """
                SELECT
                    COUNT(*)

                FROM memberships

                WHERE term_id = ?
                """,
                (
                    draft_term[
                        "term_id"
                    ],
                ),
            ).fetchone()[0]

        )


        if (

            draft_membership_count_after

            !=

            draft_membership_count_before

        ):

            raise RuntimeError(
                "Task 8 unexpectedly modified "
                "2026/2027 DRAFT memberships."
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
        # WRITE VERIFIED PENDING HISTORY
        # ====================================================

        write_pending_history(
            pending_path
        )


        result = {

            "removed_trainings":
                removed_trainings,

            "removed_projects":
                removed_projects,

            "removed_articles":
                removed_articles,

            "organizations":
                organization_names,

            "relations_created":
                relations_created,

            "integrity":
                integrity,

            "foreign_keys":
                [],

            "pending_path":
                str(
                    pending_path
                ),
        }


        write_report(
            report_path,
            result,
        )


        # ====================================================
        # OUTPUT
        # ====================================================

        if verbose:

            print()

            print(
                "========================================"
            )

            print(
                "2025/2026 HISTORY RECONSTRUCTION SUCCESSFUL"
            )

            print(
                "========================================"
            )


            print(
                "Active mandate:",
                ACTIVE_TERM_NAME,
            )


            print(
                "Future DRAFT preserved:",
                DRAFT_TERM_NAME,
            )


            print(
                "Obvious fake trainings removed:",
                len(
                    removed_trainings
                ),
            )


            for name in (
                removed_trainings
            ):

                print(
                    "  -",
                    name,
                )


            print(
                "Obvious fake projects removed:",
                len(
                    removed_projects
                ),
            )


            for name in (
                removed_projects
            ):

                print(
                    "  -",
                    name,
                )


            print(
                "Obvious fake articles removed:",
                len(
                    removed_articles
                ),
            )


            for name in (
                removed_articles
            ):

                print(
                    "  -",
                    name,
                )


            print(
                "Confirmed organizations linked to 2025/2026:",
                len(
                    organization_names
                ),
            )


            for name in (
                organization_names
            ):

                print(
                    "  +",
                    name,
                )


            print(
                "New organization relations this run:",
                relations_created,
            )


            print(
                "Pending verified history file:",
                pending_path.name,
            )


            print(
                "Reconstruction report:",
                report_path.name,
            )


            print(
                "Integrity check:",
                integrity,
            )


            print(
                "Foreign key check: []"
            )


        return result


    except Exception:

        conn.rollback()

        raise


    finally:

        conn.close()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    reconstruct_history()