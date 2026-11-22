import secrets
from datetime import datetime, timedelta

import bcrypt
from flask import Blueprint, g, jsonify, request
from mongoengine.queryset.visitor import Q

from backend.config import Config
from backend.middleware.auth import public_user, require_admin
from backend.models import User
from backend.services.activity_log_service import log_activity
from backend.utils.mongo import parse_object_id

bp = Blueprint("admin_users", __name__, url_prefix="/api/admin/users")


def _user_admin_doc(u: User) -> dict:
    return {
        **public_user(u),
        "phoneNumber": u.phone_number or "",
        "createdAt": u.created_at.isoformat() if u.created_at else None,
        "lastLogin": u.last_login.isoformat() if u.last_login else None,
    }


def _load_user(user_id: str) -> User | None:
    oid = parse_object_id(user_id)
    if not oid:
        return None
    return User.objects(id=oid).first()


@bp.get("/")
@require_admin
def list_users():
    page = max(1, int(request.args.get("page", 1)))
    limit = min(50, max(1, int(request.args.get("limit", 20))))
    q = (request.args.get("search") or "").strip().lower()
    query = User.objects
    if q:
        query = query.filter(Q(email__icontains=q) | Q(display_name__icontains=q))
    total = query.count()
    items = query.order_by("-created_at").skip((page - 1) * limit).limit(limit)
    return jsonify(
        {
            "items": [_user_admin_doc(u) for u in items],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "totalPages": max(1, (total + limit - 1) // limit),
            },
        }
    )


@bp.get("/<user_id>")
@require_admin
def get_user(user_id: str):
    u = _load_user(user_id)
    if not u:
        return jsonify({"error": "Không tìm thấy"}), 404
    return jsonify({"user": _user_admin_doc(u)})


@bp.patch("/<user_id>/ban")
@require_admin
def ban_user(user_id: str):
    u = _load_user(user_id)
    if not u:
        return jsonify({"error": "Không tìm thấy"}), 404
    if u.id == g.user.id:
        return jsonify({"error": "Không thể khóa chính mình"}), 400
    u.banned = True
    u.save()
    log_activity(
        request, action="admin.user.ban", target_type="user", target_id=str(u.id), user=g.user
    )
    return jsonify({"user": _user_admin_doc(u)})


@bp.patch("/<user_id>/unban")
@require_admin
def unban_user(user_id: str):
    u = _load_user(user_id)
    if not u:
        return jsonify({"error": "Không tìm thấy"}), 404
    u.banned = False
    u.save()
    return jsonify({"user": _user_admin_doc(u)})


@bp.delete("/<user_id>")
@require_admin
def delete_user(user_id: str):
    u = _load_user(user_id)
    if not u:
        return jsonify({"error": "Không tìm thấy"}), 404
    if u.id == g.user.id:
        return jsonify({"error": "Không thể xóa chính mình"}), 400
    u.delete()
    return jsonify({"ok": True})


@bp.post("/<user_id>/reset-password")
@require_admin
def reset_password(user_id: str):
    u = _load_user(user_id)
    if not u:
        return jsonify({"error": "Không tìm thấy"}), 404
    temp = secrets.token_urlsafe(8)
    u.password_hash = bcrypt.hashpw(temp.encode(), bcrypt.gensalt(10)).decode()
    u.save()
    return jsonify({"temporaryPassword": temp})


@bp.patch("/<user_id>/role")
@require_admin
def set_role(user_id: str):
    u = _load_user(user_id)
    if not u:
        return jsonify({"error": "Không tìm thấy"}), 404
    role = str((request.get_json(silent=True) or {}).get("role", "")).strip()
    if role not in ("user", "moderator", "admin"):
        return jsonify({"error": "role: user | moderator | admin"}), 400
    u.role = role
    u.save()
    return jsonify({"user": _user_admin_doc(u)})


@bp.patch("/<user_id>/vip")
@require_admin
def set_vip(user_id: str):
    u = _load_user(user_id)
    if not u:
        return jsonify({"error": "Không tìm thấy"}), 404
    data = request.get_json(silent=True) or {}
    is_vip = bool(data.get("isVip", True))
    u.is_vip = is_vip
    u.is_unlimited_vip = bool(data.get("isUnlimitedVip", False))
    days = int(data.get("days", Config.VIP_DURATION_DAYS))
    if is_vip and not u.is_unlimited_vip:
        u.vip_expires_at = datetime.utcnow() + timedelta(days=max(1, days))
    elif not is_vip:
        u.vip_expires_at = None
        u.is_unlimited_vip = False
    u.save()
    return jsonify({"user": _user_admin_doc(u)})
