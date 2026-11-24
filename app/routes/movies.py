import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.forms import CommentForm, MovieForm
from app.models import Comment, Movie, WatchHistory

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
    form = MovieForm()
    if form.validate_on_submit():
        movie = Movie(slug=form.slug.data.strip(), title=form.title.data.strip(),
                      origin_name=form.origin_name.data or "", year=form.year.data,
                      category=form.category.data or "", poster_url=form.poster_url.data or "",
                      description=form.description.data or "", is_vip=form.is_vip.data)
        db.session.add(movie)
        try:
            db.session.commit()
            flash("Đã thêm phim.", "success")
            return redirect(url_for("catalog.index"))
        except IntegrityError:
            db.session.rollback()
            flash("Slug phim đã tồn tại.", "error")
    return render_template("admin/movie_form.html", form=form, title="Thêm phim")


@bp.route("/admin/movies/<int:movie_id>/edit", methods=["GET", "POST"])
@login_required
def edit_movie(movie_id):
    admin_required()
    movie = db.get_or_404(Movie, movie_id)
    form = MovieForm(obj=movie)
    if form.validate_on_submit():
        form.populate_obj(movie)
        db.session.commit()
        flash("Đã cập nhật phim.", "success")
        return redirect(url_for("movies.detail", movie_id=movie.id))
    return render_template("admin/movie_form.html", form=form, title="Sửa phim")


@bp.post("/admin/movies/<int:movie_id>/delete")
@login_required
def delete_movie(movie_id):
    admin_required()
    movie = db.get_or_404(Movie, movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash("Đã xóa phim.", "success")
    return redirect(url_for("catalog.index"))
