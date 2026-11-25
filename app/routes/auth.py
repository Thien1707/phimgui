from flask import Blueprint, flash, redirect, render_template, session, url_for

from app.forms import LoginForm, RegisterForm
from app.services.internal_api import BackendAPIError, api_call, web_user

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if web_user():
        return redirect(url_for("catalog.index"))
    form = RegisterForm()
    if form.validate_on_submit():
        headers = {}
        if form.admin_secret.data:
            headers["x-admin-secret"] = form.admin_secret.data
        try:
            result = api_call(
                "POST",
                "/api/auth/register",
                data={
                    "email": form.email.data.strip(),
                    "password": form.password.data,
                    "displayName": form.username.data.strip(),
                },
                headers=headers,
            )
            session.clear()
            session["phimhay_token"] = result["token"]
            flash("Tạo tài khoản thành công.", "success")
            return redirect(url_for("catalog.index"))
        except BackendAPIError as exc:
            flash(str(exc), "error")
    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if web_user():
        return redirect(url_for("catalog.index"))
    form = LoginForm()
    if form.validate_on_submit():
        try:
            result = api_call(
                "POST",
                "/api/auth/login",
                data={"identifier": form.identifier.data.strip(), "password": form.password.data},
            )
            session.clear()
            session["phimhay_token"] = result["token"]
            flash("Đăng nhập thành công.", "success")
            return redirect(url_for("catalog.index"))
        except BackendAPIError as exc:
            flash(str(exc), "error")
    return render_template("auth/login.html", form=form)


@bp.post("/logout")
def logout():
    session.pop("phimhay_token", None)
    flash("Bạn đã đăng xuất.", "success")
    return redirect(url_for("catalog.index"))
