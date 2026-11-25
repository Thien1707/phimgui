from flask import Blueprint, g, jsonify, request
from mongoengine.queryset.visitor import Q

from backend.middleware.auth import optional_auth, require_admin
from backend.models import Category, Movie
from backend.models.movie import VIEW_NORMAL, VIEW_VIP
from backend.services.activity_log_service import log_activity
from backend.services.phimapi_client import PhimApiError, fetch_movie_by_slug, fetch_new_movies
from backend.services.vip_service import playback_access
from backend.utils.mongo import parse_object_id

bp = Blueprint("movies", __name__, url_prefix="/api/movies")


def _movie_list_item(m: Movie) -> dict:
    return {
        "id": str(m.id),
        "slug": m.slug,
        "title": m.title,
        "originName": m.origin_name,
        "posterUrl": m.poster_url or "",
        "thumbUrl": m.thumb_url or "",
        "year": m.year,
        "type": m.type or "",
        "country": m.country or "",
        "viewStatus": m.view_status,
        "commentRatingPolicy": m.comment_rating_policy,
    }


@bp.before_request
def _load_user():
    optional_auth()


@bp.get("/meta/phimapi-new")
@require_admin
def phimapi_new():
    page = max(1, int(request.args.get("page", 1)))
    try:
        return jsonify(fetch_new_movies(page))
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@bp.get("/search")
def search():
    q = (request.args.get("q") or "").strip()
    page = max(1, int(request.args.get("page", 1)))
    limit = min(64, max(1, int(request.args.get("limit", 20))))
    if not q:
        return jsonify(
            {"items": [], "pagination": {"page": 1, "limit": limit, "total": 0, "totalPages": 1}}
        )
    query = Movie.objects(
        is_active=True,
    ).filter(Q(title__icontains=q) | Q(origin_name__icontains=q))
    total = query.count()
    items = query.order_by("-updated_at").skip((page - 1) * limit).limit(limit)
    return jsonify(
        {
            "items": [_movie_list_item(m) for m in items],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "totalPages": max(1, (total + limit - 1) // limit),
            },
        }
    )


@bp.get("/filters")
def filters():
    types = Movie.objects(is_active=True, type__ne="").distinct("type")
    countries_raw = Movie.objects(is_active=True, country__ne="").distinct("country")
    countries = sorted({c.strip() for row in countries_raw for c in row.split(",") if c.strip()})
    return jsonify({"types": types, "countries": countries})


@bp.get("/")
def list_movies():
    page = max(1, int(request.args.get("page", 1)))
    limit = min(64, max(1, int(request.args.get("limit", 20))))
    query = Movie.objects(is_active=True)
    if request.args.get("type"):
        query = query.filter(type=str(request.args.get("type")))
    if request.args.get("country"):
        query = query.filter(country__icontains=str(request.args.get("country")))
    if request.args.get("category"):
        cid = parse_object_id(request.args.get("category"))
        if not cid:
            return jsonify({"error": "category không hợp lệ"}), 400
        query = query.filter(category_ids=cid)
    total = query.count()
    items = query.order_by("-updated_at").skip((page - 1) * limit).limit(limit)
    return jsonify(
        {
            "items": [_movie_list_item(m) for m in items],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "totalPages": max(1, (total + limit - 1) // limit),
            },
        }
    )


@bp.put("/<movie_id>/categories")
@require_admin
def set_movie_categories(movie_id: str):
    oid = parse_object_id(movie_id)
    if not oid:
        return jsonify({"error": "movieId không hợp lệ"}), 400
    movie = Movie.objects(id=oid).first()
    if not movie:
        return jsonify({"error": "Không tìm thấy phim"}), 404
    data = request.get_json(silent=True) or {}
    ids = data.get("categoryIds") or []
    category_oids = []
    for cid in ids:
        coid = parse_object_id(cid)
        if coid and Category.objects(id=coid).first():
            category_oids.append(coid)
    movie.category_ids = category_oids
    movie.save()
    log_activity(
        request,
        action="admin.movie.categories",
        target_type="movie",
        target_id=str(movie.id),
        user=g.user,
    )
    return jsonify({"ok": True, "movieId": str(movie.id)})


@bp.post("/<movie_id>/assign-series")
@require_admin
def assign_series(movie_id: str):
    main_id = parse_object_id(movie_id)
    data = request.get_json(silent=True) or {}
    ids = data.get("movieIds") or []
    movie_ids = [parse_object_id(value) for value in ids]
    if not main_id or len(movie_ids) < 2 or any(value is None for value in movie_ids):
        return jsonify({"error": "Chọn ít nhất hai phim hợp lệ"}), 400
    if movie_ids[0] != main_id:
        return jsonify({"error": "Phim đầu tiên phải là phim chính của series"}), 400
    movies = [Movie.objects(id=value, is_active=True).first() for value in movie_ids]
    if any(movie is None for movie in movies):
        return jsonify({"error": "Không tìm thấy một hoặc nhiều phim"}), 404
    if any(movie.series_id and movie.series_id != main_id for movie in movies):
        return jsonify({"error": "Hãy hủy liên kết series hiện tại trước khi ghép lại phim này"}), 409
    for part, movie in enumerate(movies, start=1):
        movie.series_id = main_id
        movie.part_number = part
        movie.save()
    return jsonify({"ok": True, "seriesId": str(main_id), "movieIds": [str(value) for value in movie_ids]})


@bp.post("/<movie_id>/unassign-series")
@require_admin
def unassign_series(movie_id: str):
    oid = parse_object_id(movie_id)
    movie = Movie.objects(id=oid).first() if oid else None
    if not movie or not movie.series_id:
        return jsonify({"error": "Phim này chưa thuộc series nào"}), 404
    series_id = movie.series_id
    parts = list(Movie.objects(series_id=series_id).order_by("part_number", "title"))
    remaining = [part for part in parts if part.id != movie.id]
    movie.series_id = None
    movie.part_number = None
    movie.save()

    # A series needs at least two films. When its main film is removed,
    # promote the first remaining part and update the series reference.
    if len(remaining) == 1:
        remaining[0].series_id = None
        remaining[0].part_number = None
        remaining[0].save()
    elif remaining:
        new_main_id = remaining[0].id
        for part_number, part in enumerate(remaining, start=1):
            part.series_id = new_main_id
            part.part_number = part_number
            part.save()
    log_activity(
        request,
        action="admin.movie.unassign_series",
        target_type="movie",
        target_id=str(movie.id),
        metadata={"seriesId": str(series_id), "remainingCount": len(remaining)},
        user=g.user,
    )
    return jsonify({"ok": True, "seriesId": str(series_id), "remainingCount": len(remaining)})


@bp.get("/<slug>")
def movie_detail(slug: str):
    movie = Movie.objects(slug=slug, is_active=True).first()
    if not movie:
        return jsonify({"error": "Không có phim trong hệ thống"}), 404

    user = getattr(g, "user", None)
    access = playback_access(user, movie)

    series_parts = []
    if movie.series_id:
        parts = Movie.objects(series_id=movie.series_id, is_active=True).order_by(
            "year", "created_at"
        )
        series_parts = [
            {
                "id": str(p.id),
                "title": p.title,
                "slug": p.slug,
                "year": p.year,
                "posterUrl": p.poster_url or "",
            }
            for p in parts
        ]

    base = {
        "id": str(movie.id),
        "slug": movie.slug,
        "title": movie.title,
        "originName": movie.origin_name,
        "posterUrl": movie.poster_url or "",
        "thumbUrl": movie.thumb_url or "",
        "year": movie.year,
        "type": movie.type or "",
        "content": movie.content or "",
        "viewStatus": movie.view_status,
        "commentRatingPolicy": movie.comment_rating_policy,
        "canWatch": access["canWatch"],
        "accessReason": access["reason"],
        "series": series_parts,
    }

    if not access["canWatch"]:
        return jsonify({"movie": {**base, "trailer_url": "", "episodes": []}})

    try:
        phimapi_data = fetch_movie_by_slug(movie.slug)
    except PhimApiError as e:
        return jsonify({"error": "Không lấy được nguồn phát. Thử lại sau."}), e.status

    m = phimapi_data.get("movie") or {}
    return jsonify(
        {
            "movie": {
                **base,
                "trailer_url": m.get("trailer_url") or "",
                "episode_current": m.get("episode_current"),
                "episode_total": m.get("episode_total"),
                "quality": m.get("quality"),
                "lang": m.get("lang"),
                "time": m.get("time"),
                "category": m.get("category"),
                "country": m.get("country"),
                "episodes": phimapi_data.get("episodes") or [],
            }
        }
    )
