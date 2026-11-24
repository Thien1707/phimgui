from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_user, logout_user
from flask_mail import Message
from sqlalchemy import or_

from app import db, mail
from app.forms import LoginForm, RegisterForm
from app.models import User

bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("catalog.index"))
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        username = form.username.data.strip()
        exists = User.query.filter(or_(User.email == email, User.username == username)).first()
        if exists:
            flash("Email hoặc tên tài khoản đã được sử dụng.", "error")
        else:
            user = User(username=username, email=email)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            try:
                mail.send(Message("Chào mừng đến PHIMHAY", recipients=[user.email],
                                  body=f"Xin chào {user.username}, tài khoản của bạn đã được tạo."))
                flash("Đăng ký thành công. Email chào mừng đã được gửi.", "success")
            except Exception:
                flash("Đăng ký thành công. SMTP chưa cấu hình nên email chưa được gửi.", "success")
            login_user(user)
            return redirect(url_for("catalog.index"))
    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("catalog.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("catalog.index"))
        flash("Email hoặc mật khẩu không chính xác.", "error")
    return render_template("auth/login.html", form=form)


@bp.post("/logout")
def logout():
    logout_user()
    return redirect(url_for("catalog.index"))
