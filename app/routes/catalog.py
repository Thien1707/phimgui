from urllib.parse import urlencode

from flask import Blueprint, flash, render_template, request

from app.services.internal_api import BackendAPIError, api_call, web_user

bp = Blueprint("catalog", __name__)


@bp.get("/")
def index():
    params = {"page": max(1, request.args.get("page", 1, type=int)), "limit": 24}
    query = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip()
    movie_type = (request.args.get("type") or "").strip()
    country = (request.args.get("country") or "").strip()

    if query:
        params["q"] = query
        path = f"/api/movies/search?{urlencode(params)}"
    else:
        if category:
            params["category"] = category
        if movie_type:
            params["type"] = movie_type
        if country:
            params["country"] = country
        path = f"/api/movies/?{urlencode(params)}"

    data = {"items": [], "pagination": {"page": 1, "totalPages": 1, "total": 0}}
    filters = {"types": [], "countries": []}
    categories = []
    continue_watching = []
    error = None
    user = web_user()
    try:
        data = api_call("GET", path)
        filters = api_call("GET", "/api/movies/filters")
        categories = api_call("GET", "/api/categories/").get("items", [])
        if user and not query:
            continue_watching = api_call("GET", "/api/history/continue?limit=6")
    except BackendAPIError as exc:
        error = str(exc)
        if not data["items"]:
            flash(error, "error")

    return render_template(
        "catalog/index.html",
        data=data,
        filters=filters,
        categories=categories,
        continue_watching=continue_watching,
        hero_movies=data.get("items", [])[:5] if not query else [],
        query=query,
        selected_category=category,
        selected_type=movie_type,
        selected_country=country,
        error=error,
    )
