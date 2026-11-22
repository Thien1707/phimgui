from flask import g, jsonify, request

from backend.services.settings_service import get_settings


def maintenance_check():
    if request.path.startswith("/api/admin") or request.path == "/api/health":
        return None
    try:
        settings = get_settings()
        if settings.maintenance_mode:
            user = getattr(g, "user", None)
            is_admin = user and (user.role == "admin" or user.is_admin)
            if not is_admin:
                return jsonify({"error": "Hệ thống đang bảo trì", "maintenanceMode": True}), 503
    except Exception:
        pass
    return None
