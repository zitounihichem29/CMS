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


organizations_bp = Blueprint(
    "organizations",
    __name__,
)


# ============================================================
# CONSTANTS
# ============================================================

EXTERNAL_RELATIONS_DEPARTMENT_ID = 3

EXTERNAL_RELATIONS_MANAGEMENT_ROLES = (
    "HEAD",
    "SUB_HEAD",
)

EXTERNAL_RELATIONS_VIEW_ROLES = (
    "MEMBER",
    "SUB_HEAD",
    "HEAD",
)

VALID_ORGANIZATION_TYPES = {
    "company",
    "startup",
    "university",
    "school",
    "association",
    "institution",
    "media",
    "club",
    "other",
}

VALID_RELATION_TYPES = {
    "sponsor",
    "partner",
    "collaboration",
    "other",
}

ALLOWED_LOGO_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


# ============================================================
# HELPERS
# ============================================================

def get_organization_upload_folder():

    folder = os.path.join(
        current_app.root_path,
        "uploads",
        "organizations",
    )

    os.makedirs(
        folder,
        exist_ok=True,
    )

    return folder


def is_valid_logo(file):

    if file is None:
        return False

    if not file.filename:
        return False

    filename = secure_filename(
        file.filename
    )

    if not filename:
        return False

    extension = os.path.splitext(
        filename
    )[1].lower()

    return (
        extension
        in ALLOWED_LOGO_EXTENSIONS
    )


def can_manage_organizations(
    current_user,
):

    return (
        current_user is not None
        and not current_user["is_alumni"]
        and current_user["department_id"]
        == EXTERNAL_RELATIONS_DEPARTMENT_ID
        and current_user["role_name"]
        in EXTERNAL_RELATIONS_MANAGEMENT_ROLES
    )


def can_view_organization_details(
    current_user,
):

    return (
        current_user is not None
        and not current_user["is_alumni"]
        and current_user["department_id"]
        == EXTERNAL_RELATIONS_DEPARTMENT_ID
        and current_user["role_name"]
        in EXTERNAL_RELATIONS_VIEW_ROLES
    )


def get_active_term_row(
    cursor,
):

    active_term_id = (
        get_active_term_id()
    )

    if active_term_id is None:
        return None

    cursor.execute("""
        SELECT
            term_id,
            name,
            start_date,
            end_date,
            status

        FROM terms

        WHERE term_id = ?
          AND status = 'ACTIVE'

        LIMIT 1
    """, (
        active_term_id,
    ))

    return cursor.fetchone()


def organization_has_protected_history(
    cursor,
    organization_id,
):

    cursor.execute("""
        SELECT
            COUNT(*) AS protected_count

        FROM organization_relations

        JOIN terms
            ON organization_relations.term_id =
               terms.term_id

        WHERE organization_relations.organization_id = ?
          AND terms.status != 'ACTIVE'
    """, (
        organization_id,
    ))

    row = cursor.fetchone()

    return (
        row is not None
        and row["protected_count"] > 0
    )


def organization_is_linked_to_events(
    cursor,
    organization_id,
):

    cursor.execute("""
        SELECT
            COUNT(*) AS event_link_count

        FROM event_organizations

        WHERE organization_id = ?
    """, (
        organization_id,
    ))

    row = cursor.fetchone()

    return (
        row is not None
        and row["event_link_count"] > 0
    )


# ============================================================
# ORGANIZATIONS LIST
# ============================================================

@organizations_bp.route(
    "/organizations"
)
@login_required
def organizations():

    current_user = get_current_user()

    if current_user is None:

        return (
            "User not found",
            404,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            organization_id,
            name,
            organization_type,
            logo_path

        FROM organizations

        ORDER BY
            name COLLATE NOCASE ASC
    """)

    all_organizations = (
        cursor.fetchall()
    )

    conn.close()

    return render_template(
        "organizations.html",

        organizations=(
            all_organizations
        ),

        can_view_details=(
            can_view_organization_details(
                current_user
            )
        ),

        can_manage_organizations=(
            can_manage_organizations(
                current_user
            )
        ),
    )


# ============================================================
# ORGANIZATION LOGO
# ============================================================

@organizations_bp.route(
    "/organizations/<int:organization_id>/logo"
)
@login_required
def organization_logo(
    organization_id,
):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            logo_path

        FROM organizations

        WHERE organization_id = ?
    """, (
        organization_id,
    ))

    organization = (
        cursor.fetchone()
    )

    conn.close()

    if organization is None:

        return (
            "Organization not found",
            404,
        )

    if not organization["logo_path"]:

        return (
            "Logo not found",
            404,
        )

    stored_filename = (
        os.path.basename(
            organization["logo_path"]
        )
    )

    return send_from_directory(
        get_organization_upload_folder(),
        stored_filename,
    )


# ============================================================
# NEW ORGANIZATION
# HEAD / SUB_HEAD EXTERNAL RELATIONS ONLY
# ACTIVE MANDATE ONLY
# ============================================================

@organizations_bp.route(
    "/organizations/new",
    methods=[
        "GET",
        "POST",
    ],
)
@login_required
def new_organization():

    current_user = get_current_user()

    if current_user is None:

        return (
            "User not found",
            404,
        )

    if not can_manage_organizations(
        current_user
    ):

        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term = (
        get_active_term_row(
            cursor
        )
    )

    if active_term is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    active_term_id = (
        active_term["term_id"]
    )

    # Existing template expects a list called terms.
    # Only the ACTIVE mandate is offered.

    terms = [
        active_term
    ]

    if request.method == "POST":

        # ====================================================
        # ORGANIZATION DATA
        # ====================================================

        name = request.form.get(
            "name",
            "",
        ).strip()

        organization_type = (
            request.form.get(
                "organization_type",
                "",
            )
            .strip()
            .lower()
        )

        description = (
            request.form.get(
                "description",
                "",
            ).strip()
            or None
        )

        address = (
            request.form.get(
                "address",
                "",
            ).strip()
            or None
        )

        website = (
            request.form.get(
                "website",
                "",
            ).strip()
            or None
        )

        email = (
            request.form.get(
                "email",
                "",
            ).strip()
            or None
        )

        phone = (
            request.form.get(
                "phone",
                "",
            ).strip()
            or None
        )

        # ====================================================
        # RELATION DATA
        # ====================================================

        relation_type = (
            request.form.get(
                "relation_type",
                "",
            )
            .strip()
            .lower()
        )

        submitted_term_id = (
            request.form.get(
                "term_id"
            )
        )

        relation_description = (
            request.form.get(
                "relation_description",
                "",
            ).strip()
            or None
        )

        start_date = (
            request.form.get(
                "start_date",
                "",
            ).strip()
            or None
        )

        end_date = (
            request.form.get(
                "end_date",
                "",
            ).strip()
            or None
        )

        # ====================================================
        # VALIDATION
        # ====================================================

        if not name:

            conn.close()

            return (
                "Organization name is required",
                400,
            )

        if (
            organization_type
            not in VALID_ORGANIZATION_TYPES
        ):

            conn.close()

            return (
                "Invalid organization type",
                400,
            )

        if (
            relation_type
            not in VALID_RELATION_TYPES
        ):

            conn.close()

            return (
                "Invalid relation type",
                400,
            )

        if not submitted_term_id:

            conn.close()

            return (
                "Academic year is required",
                400,
            )

        try:

            submitted_term_id = int(
                submitted_term_id
            )

        except (
            TypeError,
            ValueError,
        ):

            conn.close()

            return (
                "Invalid academic year",
                400,
            )

        if (
            submitted_term_id
            != active_term_id
        ):

            conn.close()

            return (
                "Organizations can only be linked "
                "to the active mandate from this page",
                403,
            )

        if (
            start_date
            and end_date
            and end_date < start_date
        ):

            conn.close()

            return (
                "End date cannot be before start date",
                400,
            )

        # ====================================================
        # DUPLICATE NAME
        # ====================================================

        cursor.execute("""
            SELECT
                organization_id

            FROM organizations

            WHERE LOWER(name) = LOWER(?)
        """, (
            name,
        ))

        if cursor.fetchone() is not None:

            conn.close()

            return (
                "An organization with this name "
                "already exists",
                400,
            )

        # ====================================================
        # LOGO
        # ====================================================

        logo = request.files.get(
            "logo"
        )

        logo_path = None

        original_logo_filename = None

        physical_logo_path = None

        if (
            logo
            and logo.filename
        ):

            if not is_valid_logo(
                logo
            ):

                conn.close()

                return (
                    "Logo must be PNG, JPG, JPEG or WEBP",
                    400,
                )

            original_logo_filename = (
                secure_filename(
                    logo.filename
                )
            )

            extension = os.path.splitext(
                original_logo_filename
            )[1].lower()

            stored_filename = (
                "organization_"
                + uuid.uuid4().hex
                + extension
            )

            upload_folder = (
                get_organization_upload_folder()
            )

            physical_logo_path = (
                os.path.join(
                    upload_folder,
                    stored_filename,
                )
            )

            logo.save(
                physical_logo_path
            )

            logo_path = os.path.join(
                "uploads",
                "organizations",
                stored_filename,
            ).replace(
                "\\",
                "/",
            )

        # ====================================================
        # INSERT ORGANIZATION + RELATION
        # ====================================================

        try:

            cursor.execute("""
                INSERT INTO organizations (
                    name,
                    organization_type,
                    description,
                    address,
                    website,
                    email,
                    phone,
                    logo_path,
                    original_logo_filename,
                    created_by_membership_id
                )

                VALUES (
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?
                )
            """, (
                name,
                organization_type,
                description,
                address,
                website,
                email,
                phone,
                logo_path,
                original_logo_filename,
                current_user[
                    "membership_id"
                ],
            ))

            organization_id = (
                cursor.lastrowid
            )

            cursor.execute("""
                INSERT INTO organization_relations (
                    organization_id,
                    term_id,
                    relation_type,
                    description,
                    start_date,
                    end_date
                )

                VALUES (
                    ?, ?, ?, ?, ?, ?
                )
            """, (
                organization_id,
                active_term_id,
                relation_type,
                relation_description,
                start_date,
                end_date,
            ))

            conn.commit()

        except Exception:

            conn.rollback()

            if (
                physical_logo_path
                and os.path.exists(
                    physical_logo_path
                )
            ):

                try:

                    os.remove(
                        physical_logo_path
                    )

                except OSError:

                    pass

            conn.close()

            raise

        conn.close()

        return redirect(
            url_for(
                "organizations.organizations"
            )
        )

    conn.close()

    return render_template(
        "new_organization.html",
        terms=terms,
    )


# ============================================================
# ORGANIZATION DETAIL
# EXTERNAL RELATIONS ONLY
# ============================================================

@organizations_bp.route(
    "/organizations/<int:organization_id>"
)
@login_required
def organization_detail(
    organization_id,
):

    current_user = get_current_user()

    if current_user is None:

        return (
            "User not found",
            404,
        )

    if not can_view_organization_details(
        current_user
    ):

        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    # ========================================================
    # ORGANIZATION INFORMATION
    # ========================================================

    cursor.execute("""
        SELECT
            organizations.organization_id,
            organizations.name,
            organizations.organization_type,
            organizations.description,
            organizations.address,
            organizations.website,
            organizations.email,
            organizations.phone,
            organizations.logo_path,
            organizations.original_logo_filename,
            organizations.created_at,

            people.first_name
                AS creator_first_name,

            people.last_name
                AS creator_last_name

        FROM organizations

        JOIN memberships
            ON organizations.created_by_membership_id =
               memberships.membership_id

        JOIN people
            ON memberships.person_id =
               people.person_id

        WHERE organizations.organization_id = ?
    """, (
        organization_id,
    ))

    organization = (
        cursor.fetchone()
    )

    if organization is None:

        conn.close()

        return (
            "Organization not found",
            404,
        )

    # ========================================================
    # RELATIONSHIP HISTORY
    #
    # ACTIVE + ARCHIVED visible.
    # DRAFT hidden.
    # ========================================================

    cursor.execute("""
        SELECT
            organization_relations.organization_relation_id,
            organization_relations.relation_type,
            organization_relations.description,
            organization_relations.start_date,
            organization_relations.end_date,
            organization_relations.created_at,

            terms.term_id,
            terms.name AS term_name,
            terms.status AS term_status

        FROM organization_relations

        JOIN terms
            ON organization_relations.term_id =
               terms.term_id

        WHERE organization_relations.organization_id = ?

          AND terms.status IN (
              'ACTIVE',
              'ARCHIVED'
          )

        ORDER BY
            terms.start_date DESC
    """, (
        organization_id,
    ))

    relations = cursor.fetchall()

    conn.close()

    return render_template(
        "organization_detail.html",

        organization=organization,

        relations=relations,

        can_manage_organizations=(
            can_manage_organizations(
                current_user
            )
        ),
    )


# ============================================================
# EDIT ORGANIZATION
# HEAD / SUB_HEAD EXTERNAL RELATIONS ONLY
# ============================================================

@organizations_bp.route(
    "/organizations/<int:organization_id>/edit",
    methods=[
        "GET",
        "POST",
    ],
)
@login_required
def edit_organization(
    organization_id,
):

    current_user = get_current_user()

    if current_user is None:

        return (
            "User not found",
            404,
        )

    if not can_manage_organizations(
        current_user
    ):

        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            organization_id,
            name,
            organization_type,
            description,
            address,
            website,
            email,
            phone,
            logo_path,
            original_logo_filename

        FROM organizations

        WHERE organization_id = ?
    """, (
        organization_id,
    ))

    organization = (
        cursor.fetchone()
    )

    if organization is None:

        conn.close()

        return (
            "Organization not found",
            404,
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            "",
        ).strip()

        organization_type = (
            request.form.get(
                "organization_type",
                "",
            )
            .strip()
            .lower()
        )

        description = (
            request.form.get(
                "description",
                "",
            ).strip()
            or None
        )

        address = (
            request.form.get(
                "address",
                "",
            ).strip()
            or None
        )

        website = (
            request.form.get(
                "website",
                "",
            ).strip()
            or None
        )

        email = (
            request.form.get(
                "email",
                "",
            ).strip()
            or None
        )

        phone = (
            request.form.get(
                "phone",
                "",
            ).strip()
            or None
        )

        # ====================================================
        # VALIDATION
        # ====================================================

        if not name:

            conn.close()

            return (
                "Organization name is required",
                400,
            )

        if (
            organization_type
            not in VALID_ORGANIZATION_TYPES
        ):

            conn.close()

            return (
                "Invalid organization type",
                400,
            )

        cursor.execute("""
            SELECT
                organization_id

            FROM organizations

            WHERE LOWER(name) = LOWER(?)

              AND organization_id != ?
        """, (
            name,
            organization_id,
        ))

        if cursor.fetchone() is not None:

            conn.close()

            return (
                "An organization with this name "
                "already exists",
                400,
            )

        # ====================================================
        # LOGO
        # ====================================================

        new_logo = request.files.get(
            "logo"
        )

        logo_path = (
            organization[
                "logo_path"
            ]
        )

        original_logo_filename = (
            organization[
                "original_logo_filename"
            ]
        )

        old_physical_logo_path = None

        new_physical_logo_path = None

        if (
            new_logo
            and new_logo.filename
        ):

            if not is_valid_logo(
                new_logo
            ):

                conn.close()

                return (
                    "Logo must be PNG, JPG, JPEG or WEBP",
                    400,
                )

            new_original_filename = (
                secure_filename(
                    new_logo.filename
                )
            )

            extension = os.path.splitext(
                new_original_filename
            )[1].lower()

            new_stored_filename = (
                "organization_"
                + uuid.uuid4().hex
                + extension
            )

            upload_folder = (
                get_organization_upload_folder()
            )

            new_physical_logo_path = (
                os.path.join(
                    upload_folder,
                    new_stored_filename,
                )
            )

            new_logo.save(
                new_physical_logo_path
            )

            if organization[
                "logo_path"
            ]:

                old_filename = (
                    os.path.basename(
                        organization[
                            "logo_path"
                        ]
                    )
                )

                old_physical_logo_path = (
                    os.path.join(
                        upload_folder,
                        old_filename,
                    )
                )

            logo_path = os.path.join(
                "uploads",
                "organizations",
                new_stored_filename,
            ).replace(
                "\\",
                "/",
            )

            original_logo_filename = (
                new_original_filename
            )

        # ====================================================
        # UPDATE DATABASE
        # ====================================================

        try:

            cursor.execute("""
                UPDATE organizations

                SET
                    name = ?,
                    organization_type = ?,
                    description = ?,
                    address = ?,
                    website = ?,
                    email = ?,
                    phone = ?,
                    logo_path = ?,
                    original_logo_filename = ?

                WHERE organization_id = ?
            """, (
                name,
                organization_type,
                description,
                address,
                website,
                email,
                phone,
                logo_path,
                original_logo_filename,
                organization_id,
            ))

            conn.commit()

        except Exception:

            conn.rollback()

            if (
                new_physical_logo_path
                and os.path.exists(
                    new_physical_logo_path
                )
            ):

                try:

                    os.remove(
                        new_physical_logo_path
                    )

                except OSError:

                    pass

            conn.close()

            raise

        conn.close()

        # Delete old logo only after
        # successful database update.

        if (
            new_physical_logo_path
            and old_physical_logo_path
            and os.path.exists(
                old_physical_logo_path
            )
        ):

            try:

                os.remove(
                    old_physical_logo_path
                )

            except OSError:

                pass

        return redirect(
            url_for(
                "organizations.organization_detail",
                organization_id=organization_id,
            )
        )

    conn.close()

    return render_template(
        "edit_organization.html",
        organization=organization,
    )


# ============================================================
# DELETE ORGANIZATION
# HEAD / SUB_HEAD EXTERNAL RELATIONS ONLY
# ============================================================

@organizations_bp.route(
    "/organizations/<int:organization_id>/delete",
    methods=["POST"],
)
@login_required
def delete_organization(
    organization_id,
):

    current_user = get_current_user()

    if current_user is None:

        return (
            "User not found",
            404,
        )

    if not can_manage_organizations(
        current_user
    ):

        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

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
            organization_id,
            logo_path

        FROM organizations

        WHERE organization_id = ?
    """, (
        organization_id,
    ))

    organization = (
        cursor.fetchone()
    )

    if organization is None:

        conn.close()

        return (
            "Organization not found",
            404,
        )

    # ========================================================
    # PROTECT ARCHIVED / DRAFT HISTORY
    # ========================================================

    if organization_has_protected_history(
        cursor,
        organization_id,
    ):

        conn.close()

        return (
            "This organization has relations "
            "belonging to an archived or draft "
            "mandate and cannot be deleted",
            403,
        )

    # ========================================================
    # PROTECT EVENT HISTORY
    # ========================================================

    if organization_is_linked_to_events(
        cursor,
        organization_id,
    ):

        conn.close()

        return (
            "This organization is linked to "
            "one or more events and cannot "
            "be deleted",
            403,
        )

    # ========================================================
    # DELETE
    # ========================================================

    try:

        cursor.execute("""
            DELETE FROM organization_relations

            WHERE organization_id = ?
              AND term_id = ?
        """, (
            organization_id,
            active_term_id,
        ))

        cursor.execute("""
            DELETE FROM organizations

            WHERE organization_id = ?
        """, (
            organization_id,
        ))

        conn.commit()

    except Exception:

        conn.rollback()

        conn.close()

        raise

    conn.close()

    # ========================================================
    # DELETE LOGO
    # ========================================================

    if organization[
        "logo_path"
    ]:

        stored_filename = (
            os.path.basename(
                organization[
                    "logo_path"
                ]
            )
        )

        physical_path = os.path.join(
            get_organization_upload_folder(),
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
            "organizations.organizations"
        )
    )


# ============================================================
# ADD ORGANIZATION RELATION
# ACTIVE MANDATE ONLY
# ============================================================

@organizations_bp.route(
    "/organizations/<int:organization_id>/relations/new",
    methods=[
        "GET",
        "POST",
    ],
)
@login_required
def new_organization_relation(
    organization_id,
):

    current_user = get_current_user()

    if current_user is None:

        return (
            "User not found",
            404,
        )

    if not can_manage_organizations(
        current_user
    ):

        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term = (
        get_active_term_row(
            cursor
        )
    )

    if active_term is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    active_term_id = (
        active_term[
            "term_id"
        ]
    )

    # ========================================================
    # ORGANIZATION
    # ========================================================

    cursor.execute("""
        SELECT
            organization_id,
            name

        FROM organizations

        WHERE organization_id = ?
    """, (
        organization_id,
    ))

    organization = (
        cursor.fetchone()
    )

    if organization is None:

        conn.close()

        return (
            "Organization not found",
            404,
        )

    # Existing template expects "terms".
    # Only ACTIVE term is available.

    terms = [
        active_term
    ]

    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        submitted_term_id = (
            request.form.get(
                "term_id"
            )
        )

        relation_type = (
            request.form.get(
                "relation_type",
                "",
            )
            .strip()
            .lower()
        )

        description = (
            request.form.get(
                "description",
                "",
            ).strip()
            or None
        )

        start_date = (
            request.form.get(
                "start_date",
                "",
            ).strip()
            or None
        )

        end_date = (
            request.form.get(
                "end_date",
                "",
            ).strip()
            or None
        )

        if not submitted_term_id:

            conn.close()

            return (
                "Academic year is required",
                400,
            )

        try:

            submitted_term_id = int(
                submitted_term_id
            )

        except (
            TypeError,
            ValueError,
        ):

            conn.close()

            return (
                "Invalid academic year",
                400,
            )

        if (
            submitted_term_id
            != active_term_id
        ):

            conn.close()

            return (
                "Relationships can only be "
                "created for the active mandate",
                403,
            )

        if (
            relation_type
            not in VALID_RELATION_TYPES
        ):

            conn.close()

            return (
                "Invalid relation type",
                400,
            )

        if (
            start_date
            and end_date
            and end_date < start_date
        ):

            conn.close()

            return (
                "End date cannot be before start date",
                400,
            )

        # ====================================================
        # ONE RELATION PER TERM
        # ====================================================

        cursor.execute("""
            SELECT
                organization_relation_id

            FROM organization_relations

            WHERE organization_id = ?
              AND term_id = ?
        """, (
            organization_id,
            active_term_id,
        ))

        if cursor.fetchone() is not None:

            conn.close()

            return (
                "A relationship already exists "
                "for this academic year",
                400,
            )

        # ====================================================
        # INSERT
        # ====================================================

        cursor.execute("""
            INSERT INTO organization_relations (
                organization_id,
                term_id,
                relation_type,
                description,
                start_date,
                end_date
            )

            VALUES (
                ?, ?, ?, ?, ?, ?
            )
        """, (
            organization_id,
            active_term_id,
            relation_type,
            description,
            start_date,
            end_date,
        ))

        conn.commit()

        conn.close()

        return redirect(
            url_for(
                "organizations.organization_detail",
                organization_id=organization_id,
            )
        )

    conn.close()

    return render_template(
        "new_organization_relation.html",
        organization=organization,
        terms=terms,
    )


# ============================================================
# EDIT ORGANIZATION RELATION
# ACTIVE MANDATE ONLY
# ============================================================

@organizations_bp.route(
    "/organizations/<int:organization_id>/relations/<int:relation_id>/edit",
    methods=[
        "GET",
        "POST",
    ],
)
@login_required
def edit_organization_relation(
    organization_id,
    relation_id,
):

    current_user = get_current_user()

    if current_user is None:

        return (
            "User not found",
            404,
        )

    if not can_manage_organizations(
        current_user
    ):

        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

    active_term = (
        get_active_term_row(
            cursor
        )
    )

    if active_term is None:

        conn.close()

        return (
            "No active mandate configured.",
            503,
        )

    active_term_id = (
        active_term[
            "term_id"
        ]
    )

    # ========================================================
    # ORGANIZATION
    # ========================================================

    cursor.execute("""
        SELECT
            organization_id,
            name

        FROM organizations

        WHERE organization_id = ?
    """, (
        organization_id,
    ))

    organization = (
        cursor.fetchone()
    )

    if organization is None:

        conn.close()

        return (
            "Organization not found",
            404,
        )

    # ========================================================
    # RELATION
    # ========================================================

    cursor.execute("""
        SELECT
            organization_relations.organization_relation_id,
            organization_relations.organization_id,
            organization_relations.term_id,
            organization_relations.relation_type,
            organization_relations.description,
            organization_relations.start_date,
            organization_relations.end_date,

            terms.name AS term_name,
            terms.status AS term_status

        FROM organization_relations

        JOIN terms
            ON organization_relations.term_id =
               terms.term_id

        WHERE organization_relations.organization_relation_id = ?
          AND organization_relations.organization_id = ?
    """, (
        relation_id,
        organization_id,
    ))

    relation = cursor.fetchone()

    if relation is None:

        conn.close()

        return (
            "Relationship not found",
            404,
        )

    # Archived and DRAFT relations are read-only.

    if (
        relation["term_id"]
        != active_term_id

        or relation[
            "term_status"
        ]
        != "ACTIVE"
    ):

        conn.close()

        return (
            "Archived or draft relationships "
            "are read-only",
            403,
        )

    terms = [
        active_term
    ]

    # ========================================================
    # POST
    # ========================================================

    if request.method == "POST":

        submitted_term_id = (
            request.form.get(
                "term_id"
            )
        )

        relation_type = (
            request.form.get(
                "relation_type",
                "",
            )
            .strip()
            .lower()
        )

        description = (
            request.form.get(
                "description",
                "",
            ).strip()
            or None
        )

        start_date = (
            request.form.get(
                "start_date",
                "",
            ).strip()
            or None
        )

        end_date = (
            request.form.get(
                "end_date",
                "",
            ).strip()
            or None
        )

        if not submitted_term_id:

            conn.close()

            return (
                "Academic year is required",
                400,
            )

        try:

            submitted_term_id = int(
                submitted_term_id
            )

        except (
            TypeError,
            ValueError,
        ):

            conn.close()

            return (
                "Invalid academic year",
                400,
            )

        if (
            submitted_term_id
            != active_term_id
        ):

            conn.close()

            return (
                "The academic year of an active "
                "relationship cannot be changed "
                "to another mandate",
                403,
            )

        if (
            relation_type
            not in VALID_RELATION_TYPES
        ):

            conn.close()

            return (
                "Invalid relation type",
                400,
            )

        if (
            start_date
            and end_date
            and end_date < start_date
        ):

            conn.close()

            return (
                "End date cannot be before start date",
                400,
            )

        cursor.execute("""
            UPDATE organization_relations

            SET
                relation_type = ?,
                description = ?,
                start_date = ?,
                end_date = ?

            WHERE organization_relation_id = ?
              AND organization_id = ?
              AND term_id = ?
        """, (
            relation_type,
            description,
            start_date,
            end_date,
            relation_id,
            organization_id,
            active_term_id,
        ))

        conn.commit()

        conn.close()

        return redirect(
            url_for(
                "organizations.organization_detail",
                organization_id=organization_id,
            )
        )

    conn.close()

    return render_template(
        "edit_organization_relation.html",
        organization=organization,
        relation=relation,
        terms=terms,
    )


# ============================================================
# DELETE ORGANIZATION RELATION
# ACTIVE MANDATE ONLY
# ============================================================

@organizations_bp.route(
    "/organizations/<int:organization_id>/relations/<int:relation_id>/delete",
    methods=["POST"],
)
@login_required
def delete_organization_relation(
    organization_id,
    relation_id,
):

    current_user = get_current_user()

    if current_user is None:

        return (
            "User not found",
            404,
        )

    if not can_manage_organizations(
        current_user
    ):

        return (
            "Access denied",
            403,
        )

    conn = get_db_connection()
    cursor = conn.cursor()

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
    # ORGANIZATION
    # ========================================================

    cursor.execute("""
        SELECT
            organization_id

        FROM organizations

        WHERE organization_id = ?
    """, (
        organization_id,
    ))

    if cursor.fetchone() is None:

        conn.close()

        return (
            "Organization not found",
            404,
        )

    # ========================================================
    # ACTIVE RELATION ONLY
    # ========================================================

    cursor.execute("""
        SELECT
            organization_relation_id

        FROM organization_relations

        WHERE organization_relation_id = ?
          AND organization_id = ?
          AND term_id = ?
    """, (
        relation_id,
        organization_id,
        active_term_id,
    ))

    relation = cursor.fetchone()

    if relation is None:

        conn.close()

        return (
            "Relationship not found or archived "
            "relationships are read-only",
            404,
        )

    # ========================================================
    # DELETE
    # ========================================================

    cursor.execute("""
        DELETE FROM organization_relations

        WHERE organization_relation_id = ?
          AND organization_id = ?
          AND term_id = ?
    """, (
        relation_id,
        organization_id,
        active_term_id,
    ))

    conn.commit()

    conn.close()

    return redirect(
        url_for(
            "organizations.organization_detail",
            organization_id=organization_id,
        )
    )