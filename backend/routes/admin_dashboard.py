from flask import Blueprint, jsonify, request

from backend.middleware.auth import require_admin
from backend.services.dashboard_service import charts, overview

bp = Blueprint("admin_dashboard", __name__, url_prefix="/api/admin/dashboard")


@bp.get("/overview")
@require_admin
def dashboard_overview():
    return jsonify(overview())


@bp.get("/charts")
@require_admin
def dashboard_charts():
    days = int(request.args.get("days", 14))
    return jsonify(charts(days))
