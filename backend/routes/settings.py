from flask import Blueprint

from backend.services.settings_service import get_settings, public_settings_dict

bp = Blueprint("settings", __name__, url_prefix="/api/settings")


@bp.get("/public")
def public_settings():
    doc = get_settings()
    return public_settings_dict(doc)
