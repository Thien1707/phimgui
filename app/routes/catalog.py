from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user

from app.forms import SearchForm
from app.models import Movie

bp = Blueprint("catalog", __name__)


@bp.get("/")
def index():
    form = SearchForm(request.args)
    query = Movie.query.filter_by(is_active=True)
    text = (request.args.get("q") or "").strip()
    if text:
        query = query.filter(Movie.title.ilike(f"%{text}%") | Movie.origin_name.ilike(f"%{text}%"))
    page = query.order_by(Movie.created_at.desc()).paginate(page=max(1, request.args.get("page", 1, type=int)),
                                                              per_page=12, error_out=False)
    return render_template("catalog/index.html", page=page, form=form)


@bp.get("/api/movies")
def movies_json():
    """REST endpoint returning paginated movie data as JSON."""
    text = (request.args.get("q") or "").strip()
    query = Movie.query.filter_by(is_active=True)
    if text:
        query = query.filter(Movie.title.ilike(f"%{text}%") | Movie.origin_name.ilike(f"%{text}%"))
    page = query.order_by(Movie.created_at.desc()).paginate(page=max(1, request.args.get("page", 1, type=int)),
                                                              per_page=min(50, max(1, request.args.get("limit", 12, type=int))),
                                                              error_out=False)
    return jsonify({"items": [{"id": m.id, "slug": m.slug, "title": m.title,
                               "originName": m.origin_name, "year": m.year,
                               "posterUrl": m.poster_url} for m in page.items],
                    "pagination": {"page": page.page, "pages": page.pages,
                                   "total": page.total, "perPage": page.per_page}})
