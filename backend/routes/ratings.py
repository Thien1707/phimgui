from flask import Blueprint, g, jsonify, request

from backend.middleware.auth import optional_auth, require_auth
from backend.models import Movie, Rating
from backend.utils.mongo import parse_object_id

bp = Blueprint("ratings", __name__, url_prefix="/api/ratings")


@bp.before_request
def _auth():
    optional_auth()


@bp.get("/movie/<movie_id>")
def get_movie_ratings(movie_id: str):
    mid = parse_object_id(movie_id)
    if not mid or not Movie.objects(id=mid).first():
        return jsonify({"error": "Không tìm thấy phim"}), 404
    ratings = list(Rating.objects(movie_id=mid).only("stars"))
    count = len(ratings)
    avg = sum(r.stars for r in ratings) / count if count else 0.0
    mine = None
    if g.user:
        r = Rating.objects(movie_id=mid, user_id=g.user.id).first()
        if r:
            mine = r.stars
    return jsonify({"average": round(avg, 2), "count": count, "userStars": mine})


@bp.post("/movie/<movie_id>")
@require_auth
def rate_movie(movie_id: str):
    mid = parse_object_id(movie_id)
    movie = Movie.objects(id=mid).first() if mid else None
    if not movie:
        return jsonify({"error": "Không tìm thấy phim"}), 404
    if movie.comment_rating_policy == "members" and not g.user:
        return jsonify({"error": "Chỉ thành viên được đánh giá"}), 403
    data = request.get_json(silent=True) or {}
    try:
        stars = int(data.get("stars", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "stars phải là số 1-5"}), 400
    if stars < 1 or stars > 5:
        return jsonify({"error": "stars phải là số 1-5"}), 400
    r = Rating.objects(movie_id=mid, user_id=g.user.id).first()
    if r:
        r.stars = stars
        r.save()
    else:
        r = Rating(movie_id=mid, user_id=g.user.id, stars=stars)
        r.save()
    return jsonify({"stars": stars})
