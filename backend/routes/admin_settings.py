from flask import Blueprint, jsonify, request

from backend.middleware.auth import require_admin
from backend.services.settings_service import admin_settings_dict, get_settings, public_settings_dict

bp = Blueprint("admin_settings", __name__, url_prefix="/api/admin/settings")


@bp.get("/")
@require_admin
def get_admin_settings():
    return jsonify(admin_settings_dict(get_settings()))


@bp.put("/")
@require_admin
def update_admin_settings():
    doc = get_settings()
    data = request.get_json(silent=True) or {}
    if "siteName" in data:
        doc.site_name = str(data["siteName"]).strip() or doc.site_name
    if "maintenanceMode" in data:
        doc.maintenance_mode = bool(data["maintenanceMode"])
    if "registrationEnabled" in data:
        doc.registration_enabled = bool(data["registrationEnabled"])
    if "commentsEnabled" in data:
        doc.comments_enabled = bool(data["commentsEnabled"])
    if "logo" in data:
        doc.logo = str(data["logo"]) if data["logo"] else ""
    doc.save()
    return jsonify(admin_settings_dict(doc))
