from datetime import datetime

import bcrypt
from flask import Blueprint, g, jsonify, request
from mongoengine.queryset.visitor import Q

from backend.config import Config
from backend.extensions import limiter
from backend.middleware.auth import public_user, require_auth, sign_token
from backend.models import User
from backend.services.activity_log_service import log_activity
from backend.services.settings_service import get_settings

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
@limiter.limit("10 per minute")
def register():
    settings = get_settings()
    admin_secret = request.headers.get("x-admin-secret")
    is_bootstrap = (
        Config.INITIAL_ADMIN_SECRET
        and admin_secret
        and str(admin_secret) == str(Config.INITIAL_ADMIN_SECRET)
    )
    if not settings.registration_enabled and not is_bootstrap:
        return jsonify({"error": "Đăng ký tạm đóng"}), 403

    data = request.get_json(silent=True) or {}
    email = str(data.get("email", "")).lower().strip()
    password = data.get("password", "")
    display_name = str(data.get("displayName", "")).lower().strip()
    if not email or not password or not display_name:
        return jsonify({"error": "Email, mật khẩu và tên đăng nhập là bắt buộc"}), 400
    if User.objects(email=email).first():
        return jsonify({"error": "Email đã được dùng"}), 409
    if User.objects(display_name=display_name).first():
        return jsonify({"error": "Tên đăng nhập đã được dùng"}), 409

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=10)).decode()
    user = User(
        email=email,
        password_hash=password_hash,
        display_name=display_name,
        role="admin" if is_bootstrap else "user",
    )
    user.save()
    log_activity(
        request, action="user.register", target_type="user", target_id=str(user.id), user=user
    )
    token = sign_token(user)
    return jsonify({"token": token, "user": public_user(user)}), 201


@bp.post("/login")
@limiter.limit("20 per minute")
def login():
    data = request.get_json(silent=True) or {}
    identifier = str(data.get("identifier", "")).lower().strip()
    password = data.get("password", "") or ""
    user = User.objects(Q(email=identifier) | Q(display_name=identifier)).first()
    if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return jsonify({"error": "Sai tên đăng nhập hoặc mật khẩu"}), 401
    if user.banned:
        return jsonify({"error": "Tài khoản đã bị khóa"}), 403
    user.last_login = datetime.utcnow()
    user.save()
    log_activity(
        request, action="user.login", target_type="user", target_id=str(user.id), user=user
    )
    return jsonify({"token": sign_token(user), "user": public_user(user)})


@bp.get("/me")
@require_auth
def me():
    u = g.user
    return jsonify(
        {
            **public_user(u),
            "phoneNumber": u.phone_number or "",
            "dateOfBirth": u.date_of_birth.isoformat() if u.date_of_birth else None,
            "gender": u.gender or "",
        }
    )


@bp.put("/me")
@require_auth
def update_me():
    u = g.user
    data = request.get_json(silent=True) or {}

    if "email" in data:
        lower = str(data["email"]).lower().strip()
        exists = User.objects(email=lower, id__ne=u.id).first()
        if exists:
            return jsonify({"error": "Email đã được dùng"}), 409
        u.email = lower
    if "displayName" in data:
        lower = str(data["displayName"]).lower().strip()
        exists = User.objects(display_name=lower, id__ne=u.id).first()
        if exists:
            return jsonify({"error": "Tên đăng nhập đã được dùng"}), 409
        u.display_name = lower
    if "phoneNumber" in data:
        u.phone_number = str(data["phoneNumber"]).strip() if data["phoneNumber"] else ""
    if "gender" in data:
        u.gender = str(data["gender"]).strip() if data["gender"] else ""
    if "dateOfBirth" in data:
        dob = data["dateOfBirth"]
        u.date_of_birth = datetime.strptime(dob, "%Y-%m-%d").date() if dob else None
    if data.get("password"):
        u.password_hash = bcrypt.hashpw(
            str(data["password"]).encode(), bcrypt.gensalt(rounds=10)
        ).decode()

    u.save()
    return jsonify(
        {
            **public_user(u),
            "phoneNumber": u.phone_number or "",
            "dateOfBirth": u.date_of_birth.isoformat() if u.date_of_birth else None,
            "gender": u.gender or "",
        }
    )
