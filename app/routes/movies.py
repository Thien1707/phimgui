import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from app import db
from app.forms import CommentForm, MovieForm, MovieSlugForm
from app.models import Comment, Movie, WatchHistory
from app.services.catalog_sync import deactivate_shared_movie, save_web_movie_to_desktop

bp = Blueprint("movies", __name__)


def fetch_phimapi(slug):
    """Đọc dữ liệu JSON từ phimapi.com bằng urllib, timeout 8 giây."""
    url = f"{current_app.config['PHIMAPI_BASE']}/phim/{slug}"
    req = Request(url, headers={"Accept": "application/json", "User-Agent": "PHIMHAY-GUI/1.0"})
    try:
        with urlopen(req, timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError):
        return None


@bp.get("/movies/<int:movie_id>")
def detail(movie_id):
    movie = db.get_or_404(Movie, movie_id)
    if not movie.is_active:
        abort(404)
    comments = Comment.query.filter_by(movie_id=movie.id).order_by(Comment.created_at.desc()).all()
    return render_template("catalog/detail.html", movie=movie, comments=comments, form=CommentForm())


@bp.post("/movies/<int:movie_id>/comments")
@login_required
def comment(movie_id):
    movie = db.get_or_404(Movie, movie_id)
    form = CommentForm()
    if form.validate_on_submit():
        db.session.add(Comment(body=form.body.data.strip(), user=current_user, movie=movie))
        db.session.commit()
        flash("Đã đăng bình luận.", "success")
    return redirect(url_for("movies.detail", movie_id=movie.id))


@bp.post("/movies/<int:movie_id>/watch")
@login_required
def watch(movie_id):
    movie = db.get_or_404(Movie, movie_id)
    payload = fetch_phimapi(movie.slug)
    if not payload or not payload.get("status"):
        flash("Không lấy được dữ liệu phát phim từ phimapi.com.", "error")
        return redirect(url_for("movies.detail", movie_id=movie.id))
    db.session.add(WatchHistory(user_id=current_user.id, movie_id=movie.id))
    db.session.commit()
    movie_data = payload.get("movie") or {}
    episodes = payload.get("episodes") or []
    stream = ""
    if episodes and episodes[0].get("server_data"):
        stream = episodes[0]["server_data"][0].get("link_embed", "")
    return render_template("catalog/watch.html", movie=movie, stream=stream,
                           origin_name=movie_data.get("origin_name", ""))


@bp.get("/history")
@login_required
def history():
    items = WatchHistory.query.filter_by(user_id=current_user.id).order_by(WatchHistory.watched_at.desc()).limit(100).all()
    return render_template("catalog/history.html", items=items)


def admin_required():
    if not current_user.is_authenticated or current_user.role != "admin":
        abort(403)


@bp.route("/admin/movies/new", methods=["GET", "POST"])
@login_required
def create_movie():
    admin_required()
    form = MovieSlugForm()
    if form.validate_on_submit():
        slug = form.slug.data.strip()
        payload = fetch_phimapi(slug)
        if not payload or not payload.get("status") or not payload.get("movie"):
            flash("Không tìm thấy phim từ slug này hoặc phimapi đang lỗi.", "error")
            return render_template("admin/movie_import.html", form=form)

        data = payload["movie"]
        slug = (data.get("slug") or slug).strip()
        movie = Movie.query.filter_by(slug=slug).first()
        if movie is None:
            movie = Movie(slug=slug, title=data.get("name") or slug)
            db.session.add(movie)
        category_items = data.get("category") or []
        category = ", ".join(
            item.get("name", "") for item in category_items if isinstance(item, dict)
        ) if isinstance(category_items, list) else str(category_items)
        try:
            movie.title = (data.get("name") or slug)[:255]
            movie.origin_name = (data.get("origin_name") or "")[:255]
            movie.description = data.get("content") or ""
            movie.poster_url = data.get("poster_url") or data.get("thumb_url") or ""
            try:
                movie.year = int(data.get("year")) if data.get("year") else None
            except (TypeError, ValueError):
                movie.year = None
            movie.category = category[:100]
            movie.is_active = True
            save_web_movie_to_desktop(movie, api_data=data)
            db.session.commit()
            flash("Đã tải metadata và lưu phim. Bạn có thể chỉnh sửa các trường bên dưới.", "success")
            return redirect(url_for("movies.edit_movie", movie_id=movie.id))
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Movie import failed.")
            flash("Không lưu được phim vào MongoDB/SQLite. Kiểm tra kết nối MongoDB.", "error")
    return render_template("admin/movie_import.html", form=form)


@bp.route("/admin/movies/<int:movie_id>/edit", methods=["GET", "POST"])
@login_required
def edit_movie(movie_id):
    admin_required()
    movie = db.get_or_404(Movie, movie_id)
    form = MovieForm(obj=movie)
    form.slug.render_kw = {"readonly": True}
    if form.validate_on_submit():
        original_slug = movie.slug
        form.populate_obj(movie)
        movie.slug = original_slug
        try:
            save_web_movie_to_desktop(movie)
            db.session.commit()
            flash("Đã cập nhật phim trên web và MongoDB dùng chung với desktop.", "success")
            return redirect(url_for("movies.detail", movie_id=movie.id))
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Movie update failed.")
            flash("Không cập nhật được catalog MongoDB. Kiểm tra kết nối MongoDB.", "error")
    return render_template("admin/movie_form.html", form=form, title="Sửa phim")


@bp.post("/admin/movies/<int:movie_id>/delete")
@login_required
def delete_movie(movie_id):
    admin_required()
    movie = db.get_or_404(Movie, movie_id)
    try:
        deactivate_shared_movie(movie.slug)
        movie.is_active = False
        db.session.commit()
        flash("Đã ẩn phim trên web và desktop.", "success")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Movie deletion failed.")
        flash("Không ẩn được phim trong MongoDB. Kiểm tra kết nối MongoDB.", "error")
    return redirect(url_for("catalog.index"))
