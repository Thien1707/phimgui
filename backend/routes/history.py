from flask import Blueprint, g, jsonify, request

from backend.middleware.auth import require_auth
from backend.models import Movie, WatchHistory
from backend.services.activity_log_service import log_activity
from backend.services.movie_view_service import record_movie_view
from backend.utils.mongo import parse_object_id

bp = Blueprint("history", __name__, url_prefix="/api/history")


def _serialize_history(h: WatchHistory, movie: Movie | None = None) -> dict:
    m = movie or Movie.objects(id=h.movie_id).first()
    movie_block = {
        "_id": str(m.id) if m else str(h.movie_id),
        "title": m.title if m else "",
        "slug": m.slug if m else "",
        "posterUrl": (m.poster_url or "") if m else "",
        "thumbUrl": (m.thumb_url or "") if m else "",
        "seriesId": str(m.series_id) if m and m.series_id else None,
    }
    return {
        "_id": str(h.id),
        "userId": str(h.user_id),
        "movieId": movie_block,
        "episode": h.episode,
        "currentTime": h.current_time_sec,
        "createdAt": h.created_at.isoformat() if h.created_at else None,
        "updatedAt": h.updated_at.isoformat() if h.updated_at else None,
    }


def _group_key(item: WatchHistory, movie: Movie | None = None) -> str | None:
    m = movie or Movie.objects(id=item.movie_id).first()
    if not m:
        return None
    if m.series_id:
        return f"series:{m.series_id}"
    return f"movie:{m.id}"


@bp.post("/")
@require_auth
def update_history():
    data = request.get_json(silent=True) or {}
    movie_id = data.get("movieId")
    episode = int(data.get("episode", 1))
    current_time = int(data.get("currentTime", 0))
    if not movie_id:
        return jsonify({"error": "movieId is required"}), 400
    mid = parse_object_id(movie_id)
    if not mid:
        return jsonify({"error": "movieId invalid"}), 400

    movie = Movie.objects(id=mid).first()
    if not movie:
        return jsonify({"error": "Movie not found"}), 404

    history = WatchHistory.objects(user_id=g.user.id, movie_id=mid, episode=episode).first()
    if history:
        history.current_time_sec = current_time
        history.save()
    else:
        history = WatchHistory(
            user_id=g.user.id,
            movie_id=mid,
            episode=episode,
            current_time_sec=current_time,
        )
        history.save()

    record_movie_view(request, mid, g.user.id)
    if current_time > 0:
        log_activity(
            request,
            action="user.watched_movie",
            target_type="movie",
            target_id=str(mid),
            metadata={"episode": episode, "currentTime": current_time, "title": movie.title},
            user=g.user,
        )
    return jsonify({"message": "History updated", "data": _serialize_history(history, movie)})


@bp.get("/continue")
@require_auth
def continue_watching():
    limit = min(20, max(1, int(request.args.get("limit", 6))))
    rows = WatchHistory.objects(user_id=g.user.id).order_by("-updated_at")
    seen = {}
    for item in rows:
        key = _group_key(item)
        if not key or key in seen:
            continue
        seen[key] = item
    items = sorted(seen.values(), key=lambda x: x.updated_at, reverse=True)[:limit]
    return jsonify([_serialize_history(i) for i in items])


@bp.get("/")
@require_auth
def get_history():
    rows = WatchHistory.objects(user_id=g.user.id).order_by("-updated_at").limit(50)
    return jsonify([_serialize_history(h) for h in rows])


@bp.delete("/<history_id>")
@require_auth
def delete_one(history_id: str):
    hid = parse_object_id(history_id)
    if not hid:
        return jsonify({"error": "History id invalid"}), 400
    h = WatchHistory.objects(id=hid, user_id=g.user.id).first()
    if not h:
        return jsonify({"error": "History not found"}), 404
    h.delete()
    return jsonify({"message": "History deleted"})


@bp.delete("/")
@require_auth
def clear_all():
    WatchHistory.objects(user_id=g.user.id).delete()
    return jsonify({"message": "All history cleared"})
