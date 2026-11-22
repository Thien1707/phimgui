from flask import Blueprint, jsonify, request

from backend.middleware.auth import require_admin
from backend.models import ActivityLog

bp = Blueprint("admin_logs", __name__, url_prefix="/api/admin/logs")


@bp.get("/")
@require_admin
def list_logs():
    page = max(1, int(request.args.get("page", 1)))
    limit = min(100, max(1, int(request.args.get("limit", 30))))
    query = ActivityLog.objects.order_by("-created_at")
    total = query.count()
    rows = query.skip((page - 1) * limit).limit(limit)
    return jsonify(
        {
            "items": [
                {
                    "id": str(r.id),
                    "action": r.action,
                    "actorRole": r.actor_role,
                    "targetType": r.target_type,
                    "targetId": r.target_id,
                    "metadata": r.metadata_json,
                    "ipAddress": r.ip_address,
                    "createdAt": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "totalPages": max(1, (total + limit - 1) // limit),
            },
        }
    )
