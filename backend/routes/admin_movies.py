from flask import Blueprint, g, jsonify, request

from backend.middleware.auth import require_admin
from backend.models import Movie
from backend.models.movie import VIEW_NORMAL, VIEW_VIP
from backend.services.activity_log_service import log_activity
from backend.services.phimapi_client import PhimApiError, fetch_movie_by_slug
from backend.utils.mongo import parse_object_id

bp = Blueprint("admin_movies", __name__, url_prefix="/api/admin")


def _admin_movie_doc(m: Movie) -> dict:
    return {
        "_id": str(m.id),
        "seriesId": str(m.series_id) if m.series_id else None,
        "partNumber": m.part_number,
        "slug": m.slug,
        "title": m.title,
        "viewStatus": m.view_status,
        "commentRatingPolicy": m.comment_rating_policy,
        "isActive": m.is_active,
        "content": m.content or "",
        "categoryIds": [str(category_id) for category_id in (m.category_ids or [])],
    }


@bp.get("/movies")
@require_admin
def list_admin_movies():
    items = Movie.objects.order_by("-updated_at")
    return jsonify({"items": [_admin_movie_doc(m) for m in items]})


@bp.post("/movies/import")
@require_admin
def import_movie():
    data = request.get_json(silent=True) or {}
    slug = str(data.get("slug", "")).strip()
    if not slug:
        return jsonify({"error": "Thiếu slug"}), 400
    if Movie.objects(slug=slug).first():
        return jsonify({"error": "Slug đã có trong hệ thống"}), 409
    try:
        payload = fetch_movie_by_slug(slug)
    except PhimApiError as e:
        return jsonify({"error": str(e)}), e.status
    m = payload.get("movie") or {}
    countries = m.get("country") or []
    country = ", ".join(c.get("name", "") for c in countries if isinstance(c, dict))
    doc = Movie(
        slug=m.get("slug") or slug,
        title=m.get("name") or slug,
        origin_name=m.get("origin_name") or "",
        poster_url=m.get("poster_url") or "",
        thumb_url=m.get("thumb_url") or "",
        year=m.get("year"),
        type=m.get("type") or "",
        content=m.get("content") or "",
        country=country,
        view_status=VIEW_NORMAL,
        comment_rating_policy="public",
        external_id=str(m.get("_id") or ""),
    )
    doc.save()
    log_activity(
        request,
        action="admin.movie.import",
        target_type="movie",
        target_id=str(doc.id),
        metadata={"slug": slug},
        user=g.user,
    )
    return jsonify({"movie": _admin_movie_doc(doc)}), 201


@bp.patch("/movies/<movie_id>")
@require_admin
def patch_movie(movie_id: str):
    oid = parse_object_id(movie_id)
    if not oid:
        return jsonify({"error": "movieId không hợp lệ"}), 400
    movie = Movie.objects(id=oid).first()
    if not movie:
        return jsonify({"error": "Không tìm thấy"}), 404
    data = request.get_json(silent=True) or {}
    if "viewStatus" in data:
        vs = int(data["viewStatus"])
        if vs not in (VIEW_NORMAL, VIEW_VIP):
            return jsonify({"error": "viewStatus không hợp lệ (0 hoặc 1)"}), 400
        movie.view_status = vs
    if "commentRatingPolicy" in data:
        if data["commentRatingPolicy"] not in ("public", "members"):
            return jsonify({"error": "commentRatingPolicy: public | members"}), 400
        movie.comment_rating_policy = data["commentRatingPolicy"]
    if "isActive" in data:
        movie.is_active = bool(data["isActive"])
    if "title" in data:
        movie.title = str(data["title"])
    if "content" in data:
        movie.content = str(data["content"])
    movie.save()
    return jsonify({"movie": _admin_movie_doc(movie)})


@bp.delete("/movies/<movie_id>")
@require_admin
def delete_movie(movie_id: str):
    oid = parse_object_id(movie_id)
    if not oid:
        return jsonify({"error": "movieId không hợp lệ"}), 400
    movie = Movie.objects(id=oid).first()
    if not movie:
        return jsonify({"error": "Không tìm thấy"}), 404
    movie.delete()
    return jsonify({"ok": True})
