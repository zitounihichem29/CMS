from permissions import login_required, current_member_required


documents_bp = Blueprint("documents", __name__)


@documents_bp.before_request
@current_member_required
def protect_documents_module():
    pass