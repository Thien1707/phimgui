from functools import wraps
from typing import Callable

import jwt
from flask import Request, current_app, g, jsonify, request

from backend.models import User
from backend.utils.mongo import parse_object_id


def sign_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "isAdmin": user.role == "admin",
        "isVip": user.is_vip,
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET"], algorithm="HS256")


def _bearer_token(req: Request) -> str | None:
    h = req.headers.get("Authorization", "")
    if h.startswith("Bearer "):
        return h[7:].strip()
    return None


def optional_auth():
    token = _bearer_token(request)
    g.user = None
    g.user_payload = None
    if not token:
        return
    try:
        payload = jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
        g.user_payload = payload
        oid = parse_object_id(payload.get("sub"))
        g.user = User.objects(id=oid).first() if oid else None
    except jwt.PyJWTError:
        g.user = None
        g.user_payload = None


def require_auth(f: Callable):
    @wraps(f)
    def wrapped(*args, **kwargs):
        optional_auth()
        if not g.user:
            return jsonify({"error": "Cần đăng nhập"}), 401
        if g.user.banned:
            return jsonify({"error": "Tài khoản đã bị khóa"}), 403
        return f(*args, **kwargs)

    return wrapped


def require_admin(f: Callable):
    @wraps(f)
    def wrapped(*args, **kwargs):
        optional_auth()
        if not g.user:
            return jsonify({"error": "Cần đăng nhập"}), 401
        if g.user.role != "admin" and not g.user.is_admin:
            return jsonify({"error": "Chỉ admin"}), 403
        return f(*args, **kwargs)

    return wrapped


def public_user(u: User) -> dict:
    return {
        "id": str(u.id),
        "email": u.email,
        "displayName": u.display_name,
        "role": u.role,
        "isAdmin": u.role == "admin",
        "isVip": u.is_vip,
        "vipExpiresAt": u.vip_expires_at.isoformat() if u.vip_expires_at else None,
        "isUnlimitedVip": bool(u.is_unlimited_vip),
        "banned": bool(u.banned),
    }
