import os
import uuid

from urllib.parse import urlparse

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    current_app,
    send_from_directory
)

from werkzeug.utils import secure_filename

from database import get_db_connection
from permissions import login_required
from context import get_current_user


templates_bp = Blueprint(
    "templates",
    __name__
)


# ============================================================
# CONSTANTS
# ============================================================

RH_DEPARTMENT_ID = 1


FILE_TYPES = {
    "pdf": {".pdf"},
    "word": {".doc", ".docx"},
    "excel": {".xls", ".xlsx"},
    "powerpoint": {".ppt", ".pptx"}
}


LINK_TYPES = {
    "canva",
    "figma"
}


# ============================================================
# HELPERS
# ============================================================

def get_template_upload_folder():

    folder = os.path.join(
        current_app.root_path,
        "uploads",
        "templates"
    )

    os.makedirs(
        folder,
        exist_ok=True
    )

    return folder



def can_manage_templates(current_user):

    if current_user is None:
        return False

    if current_user["is_alumni"]:
        return False

    return (
        current_user["department_id"] == RH_DEPARTMENT_ID
        and current_user["role_name"] in (
            "MEMBER",
            "SUB_HEAD",
            "HEAD"
        )
    )



def is_valid_file_for_type(file, document_type):

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

    allowed_extensions = FILE_TYPES.get(
        document_type
    )

    if allowed_extensions is None:
        return False

    return extension in allowed_extensions



def is_valid_external_url(url, document_type):

    if not url:
        return False

    try:

        parsed = urlparse(
            url.strip()
        )

        if parsed.scheme not in (
            "http",
            "https"
        ):
            return False

        hostname = (
            parsed.hostname or ""
        ).lower()

        if document_type == "canva":

            return (
                hostname == "canva.com"
                or hostname.endswith(".canva.com")
            )

        if document_type == "figma":

            return (
                hostname == "figma.com"
                or hostname.endswith(".figma.com")
            )

        return False

    except Exception:

        return False


# ============================================================
# TEMPLATES LIST
# ============================================================

@templates_bp.route("/templates")
@login_required
def templates():

    conn = get_db_connection()
    cursor = conn.cursor()

    current_user = get_current_user()

    if current_user is None:

        conn.close()

        return "User not found", 404


    cursor.execute("""
        SELECT
            documents.document_id,
            documents.name,
            documents.document_type,
            documents.storage_type,
            documents.file_path,
            documents.original_filename,
            documents.external_url,
            documents.created_at,

            people.first_name
                AS uploader_first_name,

            people.last_name
                AS uploader_last_name

        FROM documents

        JOIN memberships
            ON documents.uploaded_by_membership_id =
               memberships.membership_id

        JOIN people
            ON memberships.person_id =
               people.person_id

        ORDER BY
            documents.name ASC
    """)


    all_templates = cursor.fetchall()

    conn.close()


    return render_template(
        "templates.html",

        templates=all_templates,

        can_manage_templates=
            can_manage_templates(
                current_user
            )
    )


# ============================================================
# ADD NEW TEMPLATE
# RH MEMBER / SUB_HEAD / HEAD ONLY
# ============================================================

@templates_bp.route(
    "/templates/new",
    methods=["GET", "POST"]
)
@login_required
def new_template():

    current_user = get_current_user()

    if current_user is None:
        return "User not found", 404


    if not can_manage_templates(
        current_user
    ):
        return "Access denied", 403


    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        document_type = request.form.get(
            "document_type",
            ""
        ).strip().lower()


        # ========================================
        # BASIC VALIDATION
        # ========================================

        if not name:

            return (
                "Template name is required",
                400
            )


        valid_types = (
            set(FILE_TYPES.keys())
            | LINK_TYPES
        )


        if document_type not in valid_types:

            return (
                "Invalid template type",
                400
            )


        # ========================================
        # CURRENT RH MEMBERSHIP
        # ========================================

        uploaded_by_membership_id = (
            current_user["membership_id"]
        )


        if uploaded_by_membership_id is None:

            return (
                "Current membership not found",
                404
            )


        # ========================================
        # FILE TEMPLATE
        # PDF / WORD / EXCEL / POWERPOINT
        # ========================================

        if document_type in FILE_TYPES:

            file = request.files.get(
                "template_file"
            )


            if not is_valid_file_for_type(
                file,
                document_type
            ):

                return (
                    "Invalid file for selected template type",
                    400
                )


            original_filename = (
                secure_filename(
                    file.filename
                )
            )


            extension = os.path.splitext(
                original_filename
            )[1].lower()


            stored_filename = (
                "template_"
                + uuid.uuid4().hex
                + extension
            )


            upload_folder = (
                get_template_upload_folder()
            )


            file.save(
                os.path.join(
                    upload_folder,
                    stored_filename
                )
            )


            relative_path = os.path.join(
                "uploads",
                "templates",
                stored_filename
            ).replace(
                "\\",
                "/"
            )


            conn = get_db_connection()
            cursor = conn.cursor()


            try:

                cursor.execute("""
                    INSERT INTO documents (
                        name,
                        document_type,
                        storage_type,
                        file_path,
                        original_filename,
                        external_url,
                        uploaded_by_membership_id
                    )
                    VALUES (?, ?, 'file', ?, ?, NULL, ?)
                """, (
                    name,
                    document_type,
                    relative_path,
                    original_filename,
                    uploaded_by_membership_id
                ))

                conn.commit()


            except Exception:

                conn.rollback()

                saved_path = os.path.join(
                    upload_folder,
                    stored_filename
                )

                if os.path.exists(
                    saved_path
                ):

                    os.remove(
                        saved_path
                    )

                conn.close()

                raise


            conn.close()


        # ========================================
        # EXTERNAL TEMPLATE
        # CANVA / FIGMA
        # ========================================

        else:

            external_url = request.form.get(
                "external_url",
                ""
            ).strip()


            if not is_valid_external_url(
                external_url,
                document_type
            ):

                return (
                    "Please enter a valid Canva or Figma link",
                    400
                )


            conn = get_db_connection()
            cursor = conn.cursor()


            cursor.execute("""
                INSERT INTO documents (
                    name,
                    document_type,
                    storage_type,
                    file_path,
                    original_filename,
                    external_url,
                    uploaded_by_membership_id
                )
                VALUES (?, ?, 'link', NULL, NULL, ?, ?)
            """, (
                name,
                document_type,
                external_url,
                uploaded_by_membership_id
            ))


            conn.commit()
            conn.close()


        return redirect(
            url_for(
                "templates.templates"
            )
        )


    return render_template(
        "new_template.html"
    )


# ============================================================
# DOWNLOAD TEMPLATE FILE
# ============================================================

@templates_bp.route(
    "/templates/<int:document_id>/download"
)
@login_required
def download_template(document_id):

    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            document_id,
            storage_type,
            file_path,
            original_filename

        FROM documents

        WHERE document_id = ?
    """, (
        document_id,
    ))


    template = cursor.fetchone()

    conn.close()


    if template is None:

        return "Template not found", 404


    if (
        template["storage_type"] != "file"
        or not template["file_path"]
    ):

        return "This template is not a downloadable file", 400


    stored_filename = os.path.basename(
        template["file_path"]
    )


    upload_folder = (
        get_template_upload_folder()
    )


    return send_from_directory(
        upload_folder,
        stored_filename,

        as_attachment=True,

        download_name=(
            template["original_filename"]
            or stored_filename
        )
    )


# ============================================================
# OPEN CANVA / FIGMA TEMPLATE
# ============================================================

@templates_bp.route(
    "/templates/<int:document_id>/open"
)
@login_required
def open_template(document_id):

    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            storage_type,
            document_type,
            external_url

        FROM documents

        WHERE document_id = ?
    """, (
        document_id,
    ))


    template = cursor.fetchone()

    conn.close()


    if template is None:

        return "Template not found", 404


    if (
        template["storage_type"] != "link"
        or not template["external_url"]
    ):

        return "This template does not contain an external link", 400


    if not is_valid_external_url(
        template["external_url"],
        template["document_type"]
    ):

        return "Invalid template link", 400


    return redirect(
        template["external_url"]
    )


# ============================================================
# DELETE TEMPLATE
# RH MEMBER / SUB_HEAD / HEAD ONLY
# ============================================================

@templates_bp.route(
    "/templates/<int:document_id>/delete",
    methods=["POST"]
)
@login_required
def delete_template(document_id):

    current_user = get_current_user()

    if current_user is None:
        return "User not found", 404


    if not can_manage_templates(
        current_user
    ):
        return "Access denied", 403


    conn = get_db_connection()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            document_id,
            storage_type,
            file_path

        FROM documents

        WHERE document_id = ?
    """, (
        document_id,
    ))


    template = cursor.fetchone()


    if template is None:

        conn.close()

        return "Template not found", 404


    cursor.execute("""
        DELETE FROM documents

        WHERE document_id = ?
    """, (
        document_id,
    ))


    conn.commit()
    conn.close()


    # ========================================
    # DELETE PHYSICAL FILE
    # ========================================

    if (
        template["storage_type"] == "file"
        and template["file_path"]
    ):

        stored_filename = os.path.basename(
            template["file_path"]
        )


        physical_path = os.path.join(
            get_template_upload_folder(),
            stored_filename
        )


        if os.path.exists(
            physical_path
        ):

            os.remove(
                physical_path
            )


    return redirect(
        url_for(
            "templates.templates"
        )
    )