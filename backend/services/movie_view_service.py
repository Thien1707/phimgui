from flask import Request

from backend.models import Movie, MovieView
from backend.services.activity_log_service import client_ip


def record_movie_view(req: Request, movie_id, user_id) -> None:
    try:
        MovieView(user_id=user_id, movie_id=movie_id, ip_address=client_ip(req)).save()
        movie = Movie.objects(id=movie_id).first()
        if movie:
            movie.view_count = (movie.view_count or 0) + 1
            movie.save()
    except Exception:
        pass
