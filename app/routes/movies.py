from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.services.internal_api import BackendAPIError, api_call, admin_required, login_required

bp = Blueprint("movies", __name__)


def _movie(slug):
    return api_call("GET", f"/api/movies/{slug}").get("movie", {})


@bp.get("/movie/<slug>")
def detail(slug):
    try:
        movie = _movie(slug)
        comments = api_call("GET", f"/api/comments/movie/{movie['id']}").get("items", [])
        rating = api_call("GET", f"/api/ratings/movie/{movie['id']}")
    except (BackendAPIError, KeyError) as exc:
        flash(str(exc) or "Không tìm thấy phim.", "error")
        return redirect(url_for("catalog.index"))
    return render_template("catalog/detail.html", movie=movie, comments=comments, rating=rating)


@bp.post("/movie/<slug>/comments")
@login_required
def comment(slug):
    try:
        movie = _movie(slug)
        api_call("POST", f"/api/comments/movie/{movie['id']}", data={"body": request.form.get("body", "")})
        flash("Đã gửi bình luận.", "success")
    except BackendAPIError as exc:
        flash(str(exc), "error")
    return redirect(url_for("movies.detail", slug=slug, _anchor="comments"))


@bp.post("/comments/<comment_id>/delete")
@login_required
def delete_comment(comment_id):
    try:
        api_call("DELETE", f"/api/comments/{comment_id}")
        flash("Đã xóa bình luận.", "success")
    except BackendAPIError as exc:
        flash(str(exc), "error")
    return redirect(request.referrer or url_for("catalog.index"))


@bp.post("/movie/<slug>/rating")
@login_required
def rate(slug):
    try:
        movie = _movie(slug)
        api_call("POST", f"/api/ratings/movie/{movie['id']}", data={"stars": request.form.get("stars")})
        flash("Đã lưu đánh giá.", "success")
    except BackendAPIError as exc:
        flash(str(exc), "error")
    return redirect(url_for("movies.detail", slug=slug, _anchor="reviews"))


@bp.get("/watch/<slug>")
@login_required
def watch(slug):
    try:
        movie = _movie(slug)
        servers = movie.get("episodes", [])
        server_index = max(0, min(request.args.get("server", 0, type=int), len(servers) - 1)) if servers else 0
        server = servers[server_index] if servers else {}
        episodes = server.get("server_data", [])
        episode_index = max(0, min(request.args.get("episode", 0, type=int), len(episodes) - 1)) if episodes else 0
        current = episodes[episode_index] if episodes else {}
        api_call("POST", "/api/history/", data={"movieId": movie["id"], "episode": episode_index + 1, "currentTime": request.args.get("time", 0, type=int)})
        comments = api_call("GET", f"/api/comments/movie/{movie['id']}").get("items", [])
        rating = api_call("GET", f"/api/ratings/movie/{movie['id']}")
    except (BackendAPIError, KeyError) as exc:
        flash(str(exc), "error")
        return redirect(url_for("movies.detail", slug=slug))
    return render_template("catalog/watch.html", movie=movie, servers=servers, server_index=server_index,
                           episodes=episodes, episode_index=episode_index, current=current,
                           comments=comments, rating=rating)


@bp.get("/history")
@login_required
def history():
    try:
        items = api_call("GET", "/api/history/")
    except BackendAPIError as exc:
        items = []
        flash(str(exc), "error")
    return render_template("catalog/history.html", items=items)


@bp.post("/history/<history_id>/delete")
@login_required
def delete_history(history_id):
    try:
        api_call("DELETE", f"/api/history/{history_id}")
    except BackendAPIError as exc:
        flash(str(exc), "error")
    return redirect(url_for("movies.history"))


@bp.post("/history/clear")
@login_required
def clear_history():
    try:
        api_call("DELETE", "/api/history/")
        flash("Đã xóa toàn bộ lịch sử.", "success")
    except BackendAPIError as exc:
        flash(str(exc), "error")
    return redirect(url_for("movies.history"))


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = api_call("GET", "/api/auth/me")
    if request.method == "POST":
        payload = {key: request.form.get(key, "") for key in ("displayName", "email", "phoneNumber", "gender", "dateOfBirth")}
        if request.form.get("password"):
            payload["password"] = request.form["password"]
        try:
            user = api_call("PUT", "/api/auth/me", data=payload)
            flash("Đã cập nhật hồ sơ.", "success")
        except BackendAPIError as exc:
            flash(str(exc), "error")
    return render_template("catalog/profile.html", user=user)


@bp.get("/vip")
@login_required
def vip():
    return render_template("catalog/vip.html", user=api_call("GET", "/api/auth/me"))


@bp.post("/vip/checkout")
@login_required
def vip_checkout():
    try:
        result = api_call("POST", "/api/payment/vnpay-create", data={})
        return redirect(result.get("payUrl") or result.get("paymentUrl") or result.get("url") or url_for("movies.vip"))
    except BackendAPIError as exc:
        flash(str(exc), "error")
        return redirect(url_for("movies.vip"))


@bp.get("/payment/return")
def payment_return():
    return render_template("catalog/payment_return.html", success=request.args.get("success") == "1",
                           code=request.args.get("code", "—"))


@bp.get("/admin/movies/new")
@admin_required
def create_movie():
    return render_template("admin/movie_import.html")


@bp.post("/admin/movies/new")
@admin_required
def import_movie():
    try:
        result = api_call("POST", "/api/admin/movies/import", data={"slug": request.form.get("slug", "")})
        flash("Đã nhập phim từ slug.", "success")
        return redirect(url_for("movies.admin_movies"))
    except BackendAPIError as exc:
        flash(str(exc), "error")
        return render_template("admin/movie_import.html")


@bp.get("/admin/movies")
@admin_required
def admin_movies():
    items = api_call("GET", "/api/admin/movies").get("items", [])
    categories = api_call("GET", "/api/categories/").get("items", [])
    return render_template("admin/movies.html", items=items, categories=categories)


@bp.post("/admin/movies/<movie_id>/categories")
@admin_required
def admin_movie_categories(movie_id):
    try:
        api_call("PUT", f"/api/movies/{movie_id}/categories", data={"categoryIds": request.form.getlist("categoryIds")})
        flash("Đã cập nhật thể loại phim.", "success")
    except BackendAPIError as exc:
        flash(str(exc), "error")
    return redirect(url_for("movies.admin_movies"))


@bp.route("/admin/categories", methods=["GET", "POST"])
@admin_required
def admin_categories():
    if request.method == "POST":
        try:
            api_call("POST", "/api/categories/", data={"name": request.form.get("name", "").strip()})
            flash("Đã tạo thể loại.", "success")
        except BackendAPIError as exc:
            flash(str(exc), "error")
        return redirect(url_for("movies.admin_categories"))
    categories = api_call("GET", "/api/categories/").get("items", [])
    return render_template("admin/categories.html", categories=categories)


@bp.route("/admin/series", methods=["GET", "POST"])
@admin_required
def admin_series():
    if request.method == "POST":
        movie_ids = request.form.getlist("movieIds")
        if len(movie_ids) < 2:
            flash("Chọn ít nhất hai phim để liên kết thành series.", "error")
        else:
            try:
                api_call("POST", f"/api/movies/{movie_ids[0]}/assign-series", data={"movieIds": movie_ids})
                flash("Đã liên kết phim thành series.", "success")
            except BackendAPIError as exc:
                flash(str(exc), "error")
        return redirect(url_for("movies.admin_series"))
    items = api_call("GET", "/api/admin/movies").get("items", [])
    return render_template("admin/series.html", items=items)


@bp.post("/admin/categories/<category_id>/delete")
@admin_required
def admin_delete_category(category_id):
    try:
        api_call("DELETE", f"/api/categories/{category_id}")
        flash("Đã xóa thể loại.", "success")
    except BackendAPIError as exc:
        flash(str(exc), "error")
    return redirect(url_for("movies.admin_categories"))


@bp.post("/admin/movies/<movie_id>/update")
@admin_required
def admin_update_movie(movie_id):
    data = {"title": request.form.get("title", ""), "content": request.form.get("content", ""),
            "viewStatus": int(request.form.get("viewStatus", 0)), "commentRatingPolicy": request.form.get("commentRatingPolicy", "public"),
            "isActive": request.form.get("isActive") == "1"}
    try:
        api_call("PATCH", f"/api/admin/movies/{movie_id}", data=data)
        flash("Đã cập nhật phim.", "success")
    except BackendAPIError as exc:
        flash(str(exc), "error")
    return redirect(url_for("movies.admin_movies"))


@bp.post("/admin/movies/<movie_id>/delete")
@admin_required
def admin_delete_movie(movie_id):
    try:
        api_call("DELETE", f"/api/admin/movies/{movie_id}")
    except BackendAPIError as exc:
        flash(str(exc), "error")
    return redirect(url_for("movies.admin_movies"))


@bp.get("/admin")
@admin_required
def admin_dashboard():
    dashboard = api_call("GET", "/api/admin/dashboard/overview")
    charts = api_call("GET", "/api/admin/dashboard/charts?days=14")
    return render_template("admin/dashboard.html", dashboard=dashboard, charts=charts)


@bp.get("/admin/users")
@admin_required
def admin_users():
    data = api_call("GET", "/api/admin/users/")
    return render_template("admin/users.html", data=data)


@bp.post("/admin/users/<user_id>/<action>")
@admin_required
def admin_user_action(user_id, action):
    try:
        if action == "ban":
            api_call("PATCH", f"/api/admin/users/{user_id}/ban")
        elif action == "unban":
            api_call("PATCH", f"/api/admin/users/{user_id}/unban")
        elif action == "vip":
            api_call("PATCH", f"/api/admin/users/{user_id}/vip", data={"isVip": True, "days": 30})
        elif action == "revoke-vip":
            api_call("PATCH", f"/api/admin/users/{user_id}/vip", data={"isVip": False})
        elif action == "reset-password":
            result = api_call("POST", f"/api/admin/users/{user_id}/reset-password")
            flash(f"Mật khẩu tạm thời: {result.get('temporaryPassword', '')}", "success")
        elif action == "delete":
            api_call("DELETE", f"/api/admin/users/{user_id}")
        else:
            flash("Thao tác không hợp lệ.", "error")
            return redirect(url_for("movies.admin_users"))
        flash("Đã thực hiện thao tác.", "success")
    except BackendAPIError as exc:
        flash(str(exc), "error")
    return redirect(url_for("movies.admin_users"))


@bp.post("/admin/users/<user_id>/role")
@admin_required
def admin_user_role(user_id):
    try:
        api_call("PATCH", f"/api/admin/users/{user_id}/role", data={"role": request.form.get("role", "user")})
        flash("Đã cập nhật vai trò.", "success")
    except BackendAPIError as exc:
        flash(str(exc), "error")
    return redirect(url_for("movies.admin_users"))


@bp.get("/admin/logs")
@admin_required
def admin_logs():
    data = api_call("GET", "/api/admin/logs/")
    return render_template("admin/logs.html", data=data)


@bp.get("/admin/settings")
@admin_required
def admin_settings():
    settings = api_call("GET", "/api/admin/settings/")
    return render_template("admin/settings.html", settings=settings)


@bp.post("/admin/settings")
@admin_required
def save_admin_settings():
    try:
        api_call("PUT", "/api/admin/settings/", data={
            "siteName": request.form.get("siteName", "PHIMHAY"),
            "registrationEnabled": request.form.get("registrationEnabled") == "1",
            "commentsEnabled": request.form.get("commentsEnabled") == "1",
            "maintenanceMode": request.form.get("maintenanceMode") == "1",
        })
        flash("Đã lưu cài đặt.", "success")
    except BackendAPIError as exc:
        flash(str(exc), "error")
    return redirect(url_for("movies.admin_settings"))
