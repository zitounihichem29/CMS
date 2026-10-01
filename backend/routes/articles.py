import os
import uuid

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from werkzeug.utils import secure_filename

from context import (
    get_active_term_id,
    get_current_user,
)

from database import get_db_connection
from permissions import login_required


articles_bp = Blueprint(
    "articles",
    __name__,
)


RESEARCH_DEPARTMENT_ID = 5

RESEARCH_ROLES = (
    "MEMBER",
    "HEAD",
    "SUB_HEAD",
)

RESEARCH_MANAGEMENT_ROLES = (
    "HEAD",
    "SUB_HEAD",
)


# ============================================================
# PDF HELPERS
# ============================================================

def get_article_upload_folder():

    folder = os.path.join(
        current_app.root_path,
        "uploads",
        "articles",
    )

    os.makedirs(
        folder,
        exist_ok=True,
    )

    return folder


def is_valid_pdf(file):

    if file is None:
        return False

    if not file.filename:
        return False

    filename = secure_filename(
        file.filename
    )

    if not filename.lower().endswith(
        ".pdf"
    ):
        return False

    # Verify real PDF signature.
    header = file.stream.read(5)

    file.stream.seek(0)

    return header == b"%PDF-"


# ============================================================
# PERMISSION HELPERS
# ============================================================

def is_research_management(user):

    return (
        user is not None

        and not user["is_alumni"]

        and user["department_id"]
        == RESEARCH_DEPARTMENT_ID

        and user["role_name"]
        in RESEARCH_MANAGEMENT_ROLES
    )


def is_head_research(user):

    return (
        user is not None

        and not user["is_alumni"]

        and user["department_id"]
        == RESEARCH_DEPARTMENT_ID

        and user["role_name"]
        == "HEAD"
    )


def is_research_member(user):

    return (
        user is not None

        and not user["is_alumni"]

        and user["department_id"]
        == RESEARCH_DEPARTMENT_ID

        and user["role_name"]
        in RESEARCH_ROLES
    )


# ============================================================
# ARTICLE HELPERS
# ============================================================

def get_article_for_action(
    cursor,
    article_id,
    active_term_id,
):

    # --------------------------------------------------------
    # IMPORTANT:
    # Any action that changes an article must go through
    # the ACTIVE mandate.
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            scientific_articles.scientific_article_id,

            scientific_articles.article_owner_membership_id,

            scientific_articles.title,

            scientific_articles.abstract,

            scientific_articles.publication_date,

            scientific_articles.file_path,

            scientific_articles.original_filename,

            scientific_articles.uploaded_by_membership_id,

            scientific_articles.uploaded_at,

            scientific_articles.is_public,

            scientific_articles.status,

            scientific_articles.created_at,

            owner_membership.person_id
                AS owner_person_id


        FROM scientific_articles


        JOIN memberships AS owner_membership

            ON scientific_articles.article_owner_membership_id =
               owner_membership.membership_id


        JOIN article_terms

            ON scientific_articles.scientific_article_id =
               article_terms.scientific_article_id


        WHERE scientific_articles.scientific_article_id = ?

          AND article_terms.term_id = ?


        LIMIT 1
    """, (
        article_id,
        active_term_id,
    ))

    return cursor.fetchone()


def article_has_archived_term(
    cursor,
    article_id,
):

    cursor.execute("""
        SELECT

            EXISTS (

                SELECT 1

                FROM article_terms

                JOIN terms

                    ON article_terms.term_id =
                       terms.term_id

                WHERE article_terms.scientific_article_id = ?

                  AND terms.status = 'ARCHIVED'

            ) AS has_archived_term
    """, (
        article_id,
    ))

    row = cursor.fetchone()

    return bool(
        row
        and row["has_archived_term"]
    )


# ============================================================
# ARTICLES LIST
# ============================================================

@articles_bp.route(
    "/articles"
)
@login_required
def articles():

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    active_term_id = (
        get_active_term_id()
    )


    can_create_article = (

        active_term_id is not None

        and is_head_research(
            current_user
        )
    )


    # ========================================================
    # ALUMNI
    # COMPLETED ARTICLES ONLY
    # ========================================================

    if current_user["is_alumni"]:

        cursor.execute("""
            SELECT

                scientific_articles.scientific_article_id,

                scientific_articles.title,

                scientific_articles.abstract,

                scientific_articles.status,

                scientific_articles.created_at,

                people.first_name
                    AS owner_first_name,

                people.last_name
                    AS owner_last_name


            FROM scientific_articles


            JOIN memberships

                ON scientific_articles.article_owner_membership_id =
                   memberships.membership_id


            JOIN people

                ON memberships.person_id =
                   people.person_id


            WHERE scientific_articles.status = 'completed'

              AND scientific_articles.file_path IS NOT NULL

              AND EXISTS (

                    SELECT 1

                    FROM article_terms

                    JOIN terms

                        ON article_terms.term_id =
                           terms.term_id

                    WHERE article_terms.scientific_article_id =
                          scientific_articles.scientific_article_id

                      AND terms.status IN (
                          'ACTIVE',
                          'ARCHIVED'
                      )
              )


            ORDER BY

                scientific_articles.created_at DESC
        """)


    # ========================================================
    # CURRENT MEMBERS
    # ACTIVE + ARCHIVED ARTICLES
    # ========================================================

    else:

        cursor.execute("""
            SELECT

                scientific_articles.scientific_article_id,

                scientific_articles.title,

                scientific_articles.abstract,

                scientific_articles.status,

                scientific_articles.created_at,

                people.first_name
                    AS owner_first_name,

                people.last_name
                    AS owner_last_name


            FROM scientific_articles


            JOIN memberships

                ON scientific_articles.article_owner_membership_id =
                   memberships.membership_id


            JOIN people

                ON memberships.person_id =
                   people.person_id


            WHERE EXISTS (

                SELECT 1

                FROM article_terms

                JOIN terms

                    ON article_terms.term_id =
                       terms.term_id

                WHERE article_terms.scientific_article_id =
                      scientific_articles.scientific_article_id

                  AND terms.status IN (
                      'ACTIVE',
                      'ARCHIVED'
                  )
            )


            ORDER BY

                scientific_articles.created_at DESC
        """)


    all_articles = (
        cursor.fetchall()
    )


    conn.close()


    return render_template(

        "articles.html",

        articles=all_articles,

        can_create_article=(
            can_create_article
        ),

        is_alumni=(
            current_user[
                "is_alumni"
            ]
        ),
    )


# ============================================================
# NEW ARTICLE
# HEAD / SUB_HEAD RESEARCH ONLY
# ============================================================

@articles_bp.route(
    "/articles/new",
    methods=[
        "GET",
        "POST",
    ],
)
@login_required
def new_article():

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    active_term_id = (
        get_active_term_id()
    )


    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    if not is_head_research(
        current_user
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )


    # ========================================================
    # IDEA OWNERS
    # ANY ACTIVE CURRENT MEMBER
    # ========================================================

    cursor.execute("""
        SELECT

            memberships.membership_id,

            people.first_name,

            people.last_name,

            departments.name
                AS department_name,

            roles.name
                AS role_name


        FROM memberships


        JOIN people

            ON memberships.person_id =
               people.person_id


        JOIN users

            ON people.person_id =
               users.person_id


        LEFT JOIN departments

            ON memberships.department_id =
               departments.department_id


        JOIN roles

            ON memberships.role_id =
               roles.role_id


        WHERE memberships.term_id = ?

          AND users.is_active = 1


        ORDER BY

            people.first_name,

            people.last_name
    """, (
        active_term_id,
    ))


    idea_owners = (
        cursor.fetchall()
    )


    # ========================================================
    # CREATE
    # ========================================================

    if request.method == "POST":


        title = request.form.get(
            "title",
            "",
        ).strip()


        description = request.form.get(
            "description",
            "",
        ).strip()


        publication_date = (
            request.form.get(
                "publication_date",
                "",
            ).strip()
        )


        idea_owner_membership_id = (
            request.form.get(
                "article_owner_membership_id",
                "",
            ).strip()
        )


        # ====================================================
        # REQUIRED
        # ====================================================

        if not title:

            conn.close()

            return (
                "Article title is required",
                400,
            )


        if not description:

            conn.close()

            return (
                "Article description is required",
                400,
            )


        if not idea_owner_membership_id:

            conn.close()

            return (
                "Idea Owner is required",
                400,
            )


        # ====================================================
        # VERIFY IDEA OWNER
        # ACTIVE MANDATE ONLY
        # ====================================================

        cursor.execute("""
            SELECT

                memberships.membership_id


            FROM memberships


            JOIN users

                ON memberships.person_id =
                   users.person_id


            WHERE memberships.membership_id = ?

              AND memberships.term_id = ?

              AND users.is_active = 1
        """, (

            idea_owner_membership_id,

            active_term_id,
        ))


        if cursor.fetchone() is None:

            conn.close()

            return (
                "Invalid Idea Owner",
                400,
            )


        # ====================================================
        # CREATE ARTICLE
        # ====================================================

        cursor.execute("""
            INSERT INTO scientific_articles (

                article_owner_membership_id,

                title,

                abstract,

                publication_date,

                status
            )

            VALUES (
                ?,
                ?,
                ?,
                ?,
                'active'
            )
        """, (

            idea_owner_membership_id,

            title,

            description,

            publication_date
            or None,
        ))


        article_id = (
            cursor.lastrowid
        )


        # ====================================================
        # LINK ACTIVE TERM
        # ====================================================

        cursor.execute("""
            INSERT INTO article_terms (

                scientific_article_id,

                term_id
            )

            VALUES (?, ?)
        """, (
            article_id,
            active_term_id,
        ))


        conn.commit()

        conn.close()


        return redirect(

            url_for(

                "articles.article_detail",

                article_id=article_id,
            )
        )


    conn.close()


    return render_template(

        "new_article.html",

        idea_owners=(
            idea_owners
        ),
    )


# ============================================================
# ARTICLE DETAIL
# CURRENT MEMBERS ONLY
# ACTIVE + ARCHIVED
# ============================================================

@articles_bp.route(
    "/articles/<int:article_id>"
)
@login_required
def article_detail(article_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    if current_user["is_alumni"]:

        conn.close()

        return (
            "Access denied",
            403,
        )


    active_term_id = (
        get_active_term_id()
    )


    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    cursor.execute("""
        SELECT

            scientific_articles.scientific_article_id,

            scientific_articles.article_owner_membership_id,

            scientific_articles.title,

            scientific_articles.abstract,

            scientific_articles.publication_date,

            scientific_articles.file_path,

            scientific_articles.original_filename,

            scientific_articles.uploaded_by_membership_id,

            scientific_articles.uploaded_at,

            scientific_articles.is_public,

            scientific_articles.status,

            scientific_articles.created_at,

            owner_membership.person_id
                AS owner_person_id,

            people.first_name
                AS owner_first_name,

            people.last_name
                AS owner_last_name,

            departments.name
                AS owner_department_name,

            roles.name
                AS owner_role_name,

            GROUP_CONCAT(
                DISTINCT terms.name
            ) AS term_names,

            MAX(
                CASE

                    WHEN terms.status = 'ACTIVE'
                    THEN 1

                    ELSE 0

                END
            ) AS is_active_term_article


        FROM scientific_articles


        JOIN memberships
            AS owner_membership

            ON scientific_articles.article_owner_membership_id =
               owner_membership.membership_id


        JOIN people

            ON owner_membership.person_id =
               people.person_id


        LEFT JOIN departments

            ON owner_membership.department_id =
               departments.department_id


        JOIN roles

            ON owner_membership.role_id =
               roles.role_id


        JOIN article_terms

            ON scientific_articles.scientific_article_id =
               article_terms.scientific_article_id


        JOIN terms

            ON article_terms.term_id =
               terms.term_id


        WHERE scientific_articles.scientific_article_id = ?

          AND terms.status IN (
              'ACTIVE',
              'ARCHIVED'
          )


        GROUP BY

            scientific_articles.scientific_article_id
    """, (
        article_id,
    ))


    article = cursor.fetchone()


    if article is None:

        conn.close()

        return (
            "Article not found",
            404,
        )


    is_active_term_article = bool(

        article[
            "is_active_term_article"
        ]
    )


    # ========================================================
    # USER TYPE
    #
    # Compare person_id instead of membership_id.
    # The membership changes between mandates.
    # ========================================================

    is_idea_owner = (

        current_user[
            "person_id"
        ]

        ==

        article[
            "owner_person_id"
        ]
    )


    research_management = (

        is_research_management(
            current_user
        )
    )


    head_research = (

        is_active_term_article

        and is_head_research(
            current_user
        )
    )


    research_member = (

        is_research_member(
            current_user
        )
    )


    # ========================================================
    # PERMISSIONS
    # ARCHIVED-ONLY ARTICLES = READ ONLY
    # ========================================================

    can_edit_article = (

        is_active_term_article

        and (

            is_idea_owner

            or research_management
        )
    )


    can_delete_article = (

        is_active_term_article

        and research_management
    )


    # Only Idea Owner selects final team.

    can_manage_team = (

        is_active_term_article

        and article["status"]
        == "active"

        and article["file_path"]
        is None

        and is_idea_owner
    )


    # Research members can participate.

    can_participate = (

        is_active_term_article

        and article["status"]
        == "active"

        and article["file_path"]
        is None

        and research_member
    )


    # ========================================================
    # VOLUNTEERS
    # ========================================================

    cursor.execute("""
        SELECT

            article_volunteers.article_volunteer_id,

            article_volunteers.membership_id,

            article_volunteers.volunteered_at,

            people.first_name,

            people.last_name,

            departments.name
                AS department_name,

            roles.name
                AS role_name


        FROM article_volunteers


        JOIN memberships

            ON article_volunteers.membership_id =
               memberships.membership_id


        JOIN people

            ON memberships.person_id =
               people.person_id


        LEFT JOIN departments

            ON memberships.department_id =
               departments.department_id


        JOIN roles

            ON memberships.role_id =
               roles.role_id


        WHERE article_volunteers.scientific_article_id = ?


        ORDER BY

            people.first_name,

            people.last_name
    """, (
        article_id,
    ))


    volunteers = cursor.fetchall()


    # ========================================================
    # FINAL TEAM
    # ========================================================

    cursor.execute("""
        SELECT

            article_authors.article_author_id,

            article_authors.membership_id,

            people.first_name,

            people.last_name,

            departments.name
                AS department_name,

            roles.name
                AS role_name


        FROM article_authors


        JOIN memberships

            ON article_authors.membership_id =
               memberships.membership_id


        JOIN people

            ON memberships.person_id =
               people.person_id


        LEFT JOIN departments

            ON memberships.department_id =
               departments.department_id


        JOIN roles

            ON memberships.role_id =
               roles.role_id


        WHERE article_authors.scientific_article_id = ?


        ORDER BY

            people.first_name,

            people.last_name
    """, (
        article_id,
    ))


    authors = cursor.fetchall()


    author_membership_ids = [

        author[
            "membership_id"
        ]

        for author
        in authors
    ]


    has_final_team = (

        len(authors) > 0
    )


    # ========================================================
    # PDF / PUBLICATION
    # ========================================================

    is_published = (

        article["status"]
        == "completed"

        and article["file_path"]
        is not None
    )


    can_upload_pdf = (

        is_active_term_article

        and article["file_path"]
        is None

        and has_final_team

        and (

            is_idea_owner

            or research_management
        )
    )


    # Before publication, regular members only see
    # title and description.

    can_view_internal_details = (

        is_published

        or is_idea_owner

        or research_management
    )


    # ========================================================
    # CURRENT USER PARTICIPATION
    # ========================================================

    cursor.execute("""
        SELECT

            article_volunteer_id


        FROM article_volunteers


        WHERE scientific_article_id = ?

          AND membership_id = ?
    """, (

        article_id,

        current_user[
            "membership_id"
        ],
    ))


    has_volunteered = (

        cursor.fetchone()
        is not None
    )


    is_article_author = (

        current_user[
            "membership_id"
        ]

        in author_membership_ids
    )


    conn.close()


    return render_template(

        "article_detail.html",

        article=article,

        volunteers=volunteers,

        authors=authors,

        author_membership_ids=(
            author_membership_ids
        ),

        has_final_team=(
            has_final_team
        ),

        is_idea_owner=(
            is_idea_owner
        ),

        is_research_management=(
            research_management
        ),

        is_head_research=(
            head_research
        ),

        can_edit_article=(
            can_edit_article
        ),

        can_delete_article=(
            can_delete_article
        ),

        can_manage_team=(
            can_manage_team
        ),

        can_participate=(
            can_participate
        ),

        can_upload_pdf=(
            can_upload_pdf
        ),

        can_view_internal_details=(
            can_view_internal_details
        ),

        has_volunteered=(
            has_volunteered
        ),

        is_article_author=(
            is_article_author
        ),

        is_published=(
            is_published
        ),
    )


# ============================================================
# PARTICIPATE
# RESEARCH MEMBERS ONLY
# ACTIVE MANDATE ONLY
# ============================================================

@articles_bp.route(
    "/articles/<int:article_id>/participate",
    methods=["POST"],
)
@login_required
def participate_article(article_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    if current_user["is_alumni"]:

        conn.close()

        return (
            "Access denied",
            403,
        )


    active_term_id = (
        get_active_term_id()
    )


    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    article = get_article_for_action(

        cursor,

        article_id,

        active_term_id,
    )


    if article is None:

        conn.close()

        return (
            "Article not found",
            404,
        )


    if (

        article["status"]
        != "active"

        or article["file_path"]
        is not None
    ):

        conn.close()

        return (
            "Participation is closed",
            403,
        )


    if not is_research_member(
        current_user
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )


    # ========================================================
    # ALREADY IN FINAL TEAM
    # ========================================================

    cursor.execute("""
        SELECT

            article_author_id


        FROM article_authors


        WHERE scientific_article_id = ?

          AND membership_id = ?
    """, (

        article_id,

        current_user[
            "membership_id"
        ],
    ))


    if cursor.fetchone() is not None:

        conn.close()

        return (
            "You are already in the final team",
            400,
        )


    # ========================================================
    # ADD VOLUNTEER
    # ========================================================

    cursor.execute("""
        INSERT OR IGNORE
        INTO article_volunteers (

            scientific_article_id,

            membership_id
        )

        VALUES (?, ?)
    """, (

        article_id,

        current_user[
            "membership_id"
        ],
    ))


    conn.commit()

    conn.close()


    return redirect(

        url_for(

            "articles.article_detail",

            article_id=article_id,
        )
    )


# ============================================================
# CANCEL PARTICIPATION
# ACTIVE MANDATE ONLY
# ============================================================

@articles_bp.route(
    "/articles/<int:article_id>/cancel-participation",
    methods=["POST"],
)
@login_required
def cancel_article_participation(
    article_id
):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    if current_user["is_alumni"]:

        conn.close()

        return (
            "Access denied",
            403,
        )


    active_term_id = (
        get_active_term_id()
    )


    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    article = get_article_for_action(

        cursor,

        article_id,

        active_term_id,
    )


    if article is None:

        conn.close()

        return (
            "Article not found",
            404,
        )


    if (

        article["status"]
        != "active"

        or article["file_path"]
        is not None
    ):

        conn.close()

        return (
            "Participation is closed",
            403,
        )


    if not is_research_member(
        current_user
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )


    # ========================================================
    # FINAL TEAM CHECK
    # ========================================================

    cursor.execute("""
        SELECT

            article_author_id


        FROM article_authors


        WHERE scientific_article_id = ?

          AND membership_id = ?
    """, (

        article_id,

        current_user[
            "membership_id"
        ],
    ))


    if cursor.fetchone() is not None:

        conn.close()

        return (
            "You are already in the final team",
            400,
        )


    # ========================================================
    # DELETE VOLUNTEER
    # ========================================================

    cursor.execute("""
        DELETE FROM article_volunteers

        WHERE scientific_article_id = ?

          AND membership_id = ?
    """, (

        article_id,

        current_user[
            "membership_id"
        ],
    ))


    conn.commit()

    conn.close()


    return redirect(

        url_for(

            "articles.article_detail",

            article_id=article_id,
        )
    )


# ============================================================
# SELECT FINAL TEAM
# IDEA OWNER ONLY
# ACTIVE MANDATE ONLY
# ============================================================

@articles_bp.route(
    "/articles/<int:article_id>/select-authors",
    methods=["POST"],
)
@login_required
def select_article_authors(
    article_id
):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    if current_user["is_alumni"]:

        conn.close()

        return (
            "Access denied",
            403,
        )


    active_term_id = (
        get_active_term_id()
    )


    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    article = get_article_for_action(

        cursor,

        article_id,

        active_term_id,
    )


    if article is None:

        conn.close()

        return (
            "Article not found",
            404,
        )


    if (

        article["status"]
        != "active"

        or article["file_path"]
        is not None
    ):

        conn.close()

        return (
            "Team selection is closed",
            403,
        )


    is_idea_owner = (

        current_user[
            "person_id"
        ]

        ==

        article[
            "owner_person_id"
        ]
    )


    if not is_idea_owner:

        conn.close()

        return (
            "Access denied",
            403,
        )


    # ========================================================
    # SELECTED IDS
    # ========================================================

    selected_ids = (

        request.form.getlist(
            "author_membership_ids"
        )
    )


    if not selected_ids:

        conn.close()

        return (
            "Select at least one team member",
            400,
        )


    selected_ids = list(

        dict.fromkeys(
            selected_ids
        )
    )


    # ========================================================
    # CURRENT VALID VOLUNTEERS
    # ========================================================

    cursor.execute("""
        SELECT

            article_volunteers.membership_id


        FROM article_volunteers


        JOIN memberships

            ON article_volunteers.membership_id =
               memberships.membership_id


        JOIN users

            ON memberships.person_id =
               users.person_id


        WHERE article_volunteers.scientific_article_id = ?

          AND memberships.term_id = ?

          AND users.is_active = 1
    """, (
        article_id,
        active_term_id,
    ))


    volunteer_ids = {

        str(
            row["membership_id"]
        )

        for row in cursor.fetchall()
    }


    # ========================================================
    # SECURITY CHECK
    # ========================================================

    for membership_id in selected_ids:

        if membership_id not in (
            volunteer_ids
        ):

            conn.close()

            return (
                "Invalid team selection",
                400,
            )


    # ========================================================
    # REPLACE FINAL TEAM
    # ========================================================

    cursor.execute("""
        DELETE FROM article_authors

        WHERE scientific_article_id = ?
    """, (
        article_id,
    ))


    for membership_id in selected_ids:

        cursor.execute("""
            INSERT INTO article_authors (

                scientific_article_id,

                membership_id
            )

            VALUES (?, ?)
        """, (
            article_id,
            membership_id,
        ))


    conn.commit()

    conn.close()


    return redirect(

        url_for(

            "articles.article_detail",

            article_id=article_id,
        )
    )


# ============================================================
# UPLOAD FINAL PDF + PUBLISH ARTICLE
#
# IDEA OWNER
# HEAD RESEARCH
# SUB_HEAD RESEARCH
#
# ACTIVE MANDATE ONLY
# ============================================================

@articles_bp.route(
    "/articles/<int:article_id>/publish",
    methods=["POST"],
)
@login_required
def publish_article(article_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    if current_user["is_alumni"]:

        conn.close()

        return (
            "Access denied",
            403,
        )


    active_term_id = (
        get_active_term_id()
    )


    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    article = get_article_for_action(

        cursor,

        article_id,

        active_term_id,
    )


    if article is None:

        conn.close()

        return (
            "Article not found",
            404,
        )


    # ========================================================
    # ALREADY PUBLISHED
    # ========================================================

    if article["file_path"] is not None:

        conn.close()

        return (
            "Article is already published",
            400,
        )


    # ========================================================
    # PERMISSION
    # ========================================================

    is_idea_owner = (

        current_user[
            "person_id"
        ]

        ==

        article[
            "owner_person_id"
        ]
    )


    research_management = (

        is_research_management(
            current_user
        )
    )


    if not (

        is_idea_owner

        or research_management
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )


    # ========================================================
    # FINAL TEAM REQUIRED
    # ========================================================

    cursor.execute("""
        SELECT

            COUNT(*) AS team_count


        FROM article_authors


        WHERE scientific_article_id = ?
    """, (
        article_id,
    ))


    team_count = (

        cursor.fetchone()[
            "team_count"
        ]
    )


    if team_count == 0:

        conn.close()

        return (
            "Final team must be selected first",
            400,
        )


    # ========================================================
    # GET PDF
    # ========================================================

    pdf_file = request.files.get(
        "article_pdf"
    )


    if (

        pdf_file is None

        or pdf_file.filename == ""
    ):

        conn.close()

        return (
            "PDF file is required",
            400,
        )


    if not is_valid_pdf(
        pdf_file
    ):

        conn.close()

        return (
            "Only valid PDF files are accepted",
            400,
        )


    original_filename = (
        secure_filename(
            pdf_file.filename
        )
    )


    # ========================================================
    # UNIQUE STORED NAME
    # ========================================================

    stored_filename = (

        "article_"

        + str(article_id)

        + "_"

        + uuid.uuid4().hex

        + ".pdf"
    )


    upload_folder = (
        get_article_upload_folder()
    )


    save_path = os.path.join(

        upload_folder,

        stored_filename,
    )


    # ========================================================
    # SAVE + DATABASE UPDATE
    # ========================================================

    try:

        pdf_file.save(
            save_path
        )


        relative_path = os.path.join(

            "uploads",

            "articles",

            stored_filename,

        ).replace(
            "\\",
            "/",
        )


        cursor.execute("""
            UPDATE scientific_articles


            SET

                file_path = ?,

                original_filename = ?,

                uploaded_by_membership_id = ?,

                uploaded_at =
                    CURRENT_TIMESTAMP,

                status = 'completed'


            WHERE scientific_article_id = ?

              AND scientific_article_id IN (

                    SELECT
                        scientific_article_id

                    FROM article_terms

                    WHERE term_id = ?
              )
        """, (

            relative_path,

            original_filename,

            current_user[
                "membership_id"
            ],

            article_id,

            active_term_id,
        ))


        conn.commit()


    except Exception:

        conn.rollback()


        if os.path.exists(
            save_path
        ):

            try:

                os.remove(
                    save_path
                )

            except OSError:

                pass


        conn.close()

        raise


    conn.close()


    return redirect(

        url_for(

            "articles.article_detail",

            article_id=article_id,
        )
    )


# ============================================================
# READ ARTICLE PDF
# CURRENT MEMBERS ONLY
# ACTIVE + ARCHIVED
# ============================================================

@articles_bp.route(
    "/articles/<int:article_id>/pdf"
)
@login_required
def view_article_pdf(article_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    if current_user["is_alumni"]:

        conn.close()

        return (
            "Access denied",
            403,
        )


    cursor.execute("""
        SELECT

            scientific_articles.file_path,

            scientific_articles.original_filename,

            scientific_articles.status


        FROM scientific_articles


        WHERE scientific_articles.scientific_article_id = ?

          AND EXISTS (

                SELECT 1

                FROM article_terms

                JOIN terms

                    ON article_terms.term_id =
                       terms.term_id

                WHERE article_terms.scientific_article_id =
                      scientific_articles.scientific_article_id

                  AND terms.status IN (
                      'ACTIVE',
                      'ARCHIVED'
                  )
          )
    """, (
        article_id,
    ))


    article = cursor.fetchone()

    conn.close()


    if article is None:

        return (
            "Article not found",
            404,
        )


    if (

        article["status"]
        != "completed"

        or not article[
            "file_path"
        ]
    ):

        return (
            "Article PDF is not available",
            404,
        )


    stored_filename = os.path.basename(

        article[
            "file_path"
        ]
    )


    upload_folder = (
        get_article_upload_folder()
    )


    return send_from_directory(

        upload_folder,

        stored_filename,

        mimetype="application/pdf",

        as_attachment=False,

        download_name=(
            article[
                "original_filename"
            ]
        ),
    )


# ============================================================
# TOGGLE ARTICLE PUBLICATION
# HEAD RESEARCH ONLY
# ACTIVE MANDATE ONLY
# ============================================================

@articles_bp.route(
    "/articles/<int:article_id>/publication/toggle",
    methods=["POST"],
)
@login_required
def toggle_article_publication(
    article_id
):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    if not is_head_research(
        current_user
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )


    active_term_id = (
        get_active_term_id()
    )


    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    # ========================================================
    # ACTIVE ARTICLE ONLY
    # ========================================================

    article = get_article_for_action(

        cursor,

        article_id,

        active_term_id,
    )


    if article is None:

        conn.close()

        return (
            "Article not found",
            404,
        )


    # ========================================================
    # PUBLISHING ON WEBSITE
    #
    # Article must already be completed
    # and have a PDF.
    # ========================================================

    if not article["is_public"]:

        if (

            article["status"]
            != "completed"

            or not article[
                "file_path"
            ]
        ):

            conn.close()

            return (
                "The final article PDF must be "
                "published in the CMS before the "
                "article can be published on "
                "the website.",
                400,
            )


    # ========================================================
    # TOGGLE
    # ========================================================

    new_public_status = (

        0

        if article[
            "is_public"
        ]

        else 1
    )


    cursor.execute("""
        UPDATE scientific_articles


        SET is_public = ?


        WHERE scientific_article_id = ?

          AND scientific_article_id IN (

                SELECT
                    scientific_article_id

                FROM article_terms

                WHERE term_id = ?
          )
    """, (

        new_public_status,

        article_id,

        active_term_id,
    ))


    conn.commit()

    conn.close()


    return redirect(

        url_for(

            "articles.article_detail",

            article_id=article_id,
        )
    )


# ============================================================
# EDIT ARTICLE
#
# IDEA OWNER
# HEAD / SUB_HEAD RESEARCH
#
# ACTIVE MANDATE ONLY
# ============================================================

@articles_bp.route(
    "/articles/<int:article_id>/edit",
    methods=[
        "GET",
        "POST",
    ],
)
@login_required
def edit_article(article_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    if current_user["is_alumni"]:

        conn.close()

        return (
            "Access denied",
            403,
        )


    active_term_id = (
        get_active_term_id()
    )


    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    # ========================================================
    # ACTIVE ARTICLE
    # ========================================================

    article = get_article_for_action(

        cursor,

        article_id,

        active_term_id,
    )


    if article is None:

        conn.close()

        return (
            "Article not found",
            404,
        )


    # ========================================================
    # PERMISSION
    # ========================================================

    is_idea_owner = (

        current_user[
            "person_id"
        ]

        ==

        article[
            "owner_person_id"
        ]
    )


    research_management = (

        is_research_management(
            current_user
        )
    )


    if not (

        is_idea_owner

        or research_management
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )


    # ========================================================
    # UPDATE
    # ========================================================

    if request.method == "POST":


        title = request.form.get(
            "title",
            "",
        ).strip()


        description = request.form.get(
            "description",
            "",
        ).strip()


        publication_date = (
            request.form.get(
                "publication_date",
                "",
            ).strip()
        )


        if not title:

            conn.close()

            return (
                "Article title is required",
                400,
            )


        if not description:

            conn.close()

            return (
                "Article description is required",
                400,
            )


        cursor.execute("""
            UPDATE scientific_articles


            SET

                title = ?,

                abstract = ?,

                publication_date = ?


            WHERE scientific_article_id = ?

              AND scientific_article_id IN (

                    SELECT
                        scientific_article_id

                    FROM article_terms

                    WHERE term_id = ?
              )
        """, (

            title,

            description,

            publication_date
            or None,

            article_id,

            active_term_id,
        ))


        conn.commit()

        conn.close()


        return redirect(

            url_for(

                "articles.article_detail",

                article_id=article_id,
            )
        )


    conn.close()


    return render_template(

        "edit_article.html",

        article=article,
    )


# ============================================================
# DELETE ARTICLE
#
# HEAD / SUB_HEAD RESEARCH ONLY
# ACTIVE MANDATE ONLY
# ============================================================

@articles_bp.route(
    "/articles/<int:article_id>/delete",
    methods=["POST"],
)
@login_required
def delete_article(article_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()


    if current_user is None:

        conn.close()

        return (
            "User not found",
            404,
        )


    if current_user["is_alumni"]:

        conn.close()

        return (
            "Access denied",
            403,
        )


    if not is_research_management(
        current_user
    ):

        conn.close()

        return (
            "Access denied",
            403,
        )


    active_term_id = (
        get_active_term_id()
    )


    if active_term_id is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )


    # ========================================================
    # VERIFY ACTIVE ARTICLE
    # ========================================================

    article = get_article_for_action(

        cursor,

        article_id,

        active_term_id,
    )


    if article is None:

        conn.close()

        return (
            "Article not found",
            404,
        )


    # ========================================================
    # PROTECT HISTORICAL ARCHIVE
    #
    # If this article is also linked to an archived mandate,
    # deleting the article row would destroy that history.
    # ========================================================

    if article_has_archived_term(

        cursor,

        article_id,
    ):

        conn.close()

        return (
            "This article belongs to an "
            "archived mandate and cannot "
            "be deleted.",
            403,
        )


    file_path = (
        article[
            "file_path"
        ]
    )


    # ========================================================
    # DELETE VOLUNTEERS
    # ========================================================

    cursor.execute("""
        DELETE FROM article_volunteers

        WHERE scientific_article_id = ?
    """, (
        article_id,
    ))


    # ========================================================
    # DELETE AUTHORS
    # ========================================================

    cursor.execute("""
        DELETE FROM article_authors

        WHERE scientific_article_id = ?
    """, (
        article_id,
    ))


    # ========================================================
    # DELETE SOURCE REFERENCES
    # ========================================================

    cursor.execute("""
        DELETE FROM article_source_references

        WHERE scientific_article_id = ?
    """, (
        article_id,
    ))


    # ========================================================
    # DELETE ACTIVE TERM LINK
    # ========================================================

    cursor.execute("""
        DELETE FROM article_terms

        WHERE scientific_article_id = ?

          AND term_id = ?
    """, (
        article_id,
        active_term_id,
    ))


    # ========================================================
    # DELETE ARTICLE
    # ========================================================

    cursor.execute("""
        DELETE FROM scientific_articles

        WHERE scientific_article_id = ?
    """, (
        article_id,
    ))


    conn.commit()

    conn.close()


    # ========================================================
    # DELETE PHYSICAL PDF
    # ========================================================

    if file_path:

        stored_filename = (
            os.path.basename(
                file_path
            )
        )


        physical_path = os.path.join(

            get_article_upload_folder(),

            stored_filename,
        )


        if os.path.exists(
            physical_path
        ):

            try:

                os.remove(
                    physical_path
                )

            except OSError:

                pass


    return redirect(

        url_for(
            "articles.articles"
        )
    )