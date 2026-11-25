"""Ứng dụng web Flask của PHIMHAY-GUI."""

from pathlib import Path

from flask import Flask, jsonify, request, session
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

db = SQLAlchemy()
mail = Mail()
csrf = CSRFProtect()


def create_app(test_config=None):
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env")
    from backend.config import Config as BackendConfig

    app = Flask(__name__)
    app.config.from_object(BackendConfig)
    app.config.update(
        SECRET_KEY=BackendConfig.SECRET_KEY,
        JWT_SECRET=BackendConfig.JWT_SECRET,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{project_root / 'instance' / 'phimhay_web.db'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        PHIMAPI_BASE=BackendConfig.PHIMAPI_BASE,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    from backend.extensions import init_mongo, limiter
    init_mongo(app)
    limiter.init_app(app)

    from backend.middleware.auth import optional_auth
    from backend.middleware.maintenance import maintenance_check
    from backend.routes.admin_dashboard import bp as api_dashboard_bp
    from backend.routes.admin_logs import bp as api_logs_bp
    from backend.routes.admin_movies import bp as api_admin_movies_bp
    from backend.routes.admin_settings import bp as api_admin_settings_bp
    from backend.routes.admin_users import bp as api_admin_users_bp
    from backend.routes.auth import bp as api_auth_bp
    from backend.routes.categories import bp as api_categories_bp
    from backend.routes.comments import bp as api_comments_bp
    from backend.routes.history import bp as api_history_bp
    from backend.routes.movies import bp as api_movies_bp
    from backend.routes.payment import bp as api_payment_bp
    from backend.routes.ratings import bp as api_ratings_bp
    from backend.routes.settings import bp as api_settings_bp

    api_blueprints = [
        (api_auth_bp, "api_auth"), (api_settings_bp, None), (api_movies_bp, "api_movies"),
        (api_categories_bp, None), (api_history_bp, None), (api_admin_movies_bp, None),
        (api_admin_users_bp, None), (api_dashboard_bp, None), (api_logs_bp, None),
        (api_admin_settings_bp, None), (api_comments_bp, None), (api_ratings_bp, None),
        (api_payment_bp, None),
    ]
    for blueprint, name in api_blueprints:
        options = {"name": name} if name else {}
        app.register_blueprint(blueprint, **options)
        csrf.exempt(blueprint)

    from app.routes import auth, catalog, movies

    app.register_blueprint(auth.bp)
    app.register_blueprint(catalog.bp)
    app.register_blueprint(movies.bp)

    @app.before_request
    def api_auth_and_maintenance():
        if not request.headers.get("Authorization") and session.get("phimhay_token"):
            request.environ["HTTP_AUTHORIZATION"] = f"Bearer {session['phimhay_token']}"
        optional_auth()
        return maintenance_check()

    @app.context_processor
    def inject_web_user():
        from app.services.internal_api import web_user
        return {"web_user": web_user()}

    @app.get("/api/health")
    def health():
        from mongoengine.connection import get_connection
        try:
            get_connection().admin.command("ping")
            return jsonify({"ok": True, "db": True})
        except Exception:
            return jsonify({"ok": False, "db": False}), 503

    @app.cli.command("init-db")
    def init_db():
        """Tạo các bảng SQLAlchemy cho lần chạy đầu."""
        db.create_all()
        print("Đã khởi tạo cơ sở dữ liệu PHIMHAY web.")

    @app.cli.command("sync-desktop-movies")
    def sync_desktop_movies_command():
        """Chép danh mục phim MongoDB desktop sang database của web."""
        from app.services.catalog_sync import sync_desktop_movies

        try:
            created, updated = sync_desktop_movies()
        except Exception as exc:
            raise SystemExit(
                "Không đồng bộ được phim. Kiểm tra MONGODB_URI trong .env và kết nối MongoDB."
            ) from exc
        print(f"Synced movies: added {created}, updated {updated}.")

    return app
