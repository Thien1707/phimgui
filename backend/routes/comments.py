from flask import Blueprint, g, jsonify, request

from backend.middleware.auth import optional_auth, require_auth
from backend.models import Comment, Movie, User
from backend.services.settings_service import get_settings
from backend.utils.mongo import parse_object_id

bp = Blueprint("comments", __name__, url_prefix="/api/comments")


def _comment_doc(c: Comment) -> dict:
    user = User.objects(id=c.user_id).first()
    return {
        "id": str(c.id),
        "movieId": str(c.movie_id),
        "body": c.body,
        "createdAt": c.created_at.isoformat() if c.created_at else None,
        "user": {
            "id": str(user.id) if user else str(c.user_id),
            "displayName": user.display_name if user else "",
            "role": user.role if user else "user",
        },
    }


@bp.get("/movie/<movie_id>")
def list_for_movie(movie_id: str):
    optional_auth()
    mid = parse_object_id(movie_id)
    if not mid or not Movie.objects(id=mid).first():
        return jsonify({"error": "Không tìm thấy phim"}), 404
    rows = Comment.objects(movie_id=mid).order_by("-created_at").limit(100)
    return jsonify({"items": [_comment_doc(c) for c in rows]})


@bp.post("/movie/<movie_id>")
@require_auth
def create(movie_id: str):
    settings = get_settings()
    if not settings.comments_enabled:
        return jsonify({"error": "Bình luận đang tắt"}), 403
    mid = parse_object_id(movie_id)
    movie = Movie.objects(id=mid).first() if mid else None
    if not movie:
        return jsonify({"error": "Không tìm thấy phim"}), 404
    if movie.comment_rating_policy == "members" and not g.user:
        return jsonify({"error": "Chỉ thành viên được bình luận"}), 403
    data = request.get_json(silent=True) or {}
    body = str(data.get("body", "")).strip()
    if not body or len(body) > 2000:
        return jsonify({"error": "Nội dung bình luận không hợp lệ"}), 400
    c = Comment(movie_id=movie.id, user_id=g.user.id, body=body)
    c.save()
    return jsonify({"comment": _comment_doc(c)}), 201


@bp.delete("/<comment_id>")
@require_auth
def delete_comment(comment_id: str):
    cid = parse_object_id(comment_id)
    c = Comment.objects(id=cid).first() if cid else None
    if not c:
        return jsonify({"error": "Không tìm thấy"}), 404
    if c.user_id != g.user.id and g.user.role != "admin":
        return jsonify({"error": "Không có quyền"}), 403
    c.delete()
    return jsonify({"ok": True})
