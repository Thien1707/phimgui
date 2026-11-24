"""Ứng dụng web Flask của PHIMHAY-GUI."""

import os
from pathlib import Path

from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__)
    project_root = Path(__file__).resolve().parent.parent
    app.config.update(
        SECRET_KEY=os.getenv("WEB_SECRET_KEY", "dev-key-change-before-deploy"),
        SQLALCHEMY_DATABASE_URI=os.getenv(
            "WEB_DATABASE_URL", f"sqlite:///{project_root / 'instance' / 'phimhay_web.db'}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAIL_SERVER=os.getenv("MAIL_SERVER", "localhost"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", "25")),
        MAIL_USE_TLS=os.getenv("MAIL_USE_TLS", "false").lower() == "true",
        MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
        MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
        MAIL_DEFAULT_SENDER=os.getenv("MAIL_DEFAULT_SENDER", "noreply@phimhay.local"),
        PHIMAPI_BASE=os.getenv("PHIMAPI_BASE", "https://phimapi.com").rstrip("/"),
    )
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Vui lòng đăng nhập để tiếp tục."

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.routes import auth, catalog, movies

    app.register_blueprint(auth.bp)
    app.register_blueprint(catalog.bp)
    app.register_blueprint(movies.bp)

    @app.cli.command("init-db")
    def init_db():
        """Tạo các bảng SQLAlchemy cho lần chạy đầu."""
        db.create_all()
        print("Đã khởi tạo cơ sở dữ liệu PHIMHAY web.")

    @app.cli.command("create-admin")
    def create_admin():
        """Tạo tài khoản quản trị mặc định nếu chưa tồn tại."""
        import getpass

        email = input("Email quản trị: ").strip().lower()
        username = input("Tên quản trị: ").strip()
        password = getpass.getpass("Mật khẩu (tối thiểu 8 ký tự): ")
        if not email or not username or len(password) < 8:
            raise SystemExit("Thông tin không hợp lệ; mật khẩu cần tối thiểu 8 ký tự.")
        if User.query.filter((User.email == email) | (User.username == username)).first():
            raise SystemExit("Email hoặc tên tài khoản đã tồn tại.")
        user = User(email=email, username=username, role="admin")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print("Đã tạo tài khoản quản trị.")

    return app
