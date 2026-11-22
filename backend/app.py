import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from flask import Flask, jsonify
from mongoengine.connection import get_connection

from backend.config import Config
from backend.extensions import init_mongo, limiter
from backend.middleware.auth import optional_auth
from backend.middleware.maintenance import maintenance_check
from backend.routes.admin_dashboard import bp as admin_dashboard_bp
from backend.routes.admin_logs import bp as admin_logs_bp
from backend.routes.admin_movies import bp as admin_movies_bp
from backend.routes.admin_settings import bp as admin_settings_bp
from backend.routes.admin_users import bp as admin_users_bp
from backend.routes.auth import bp as auth_bp
from backend.routes.categories import bp as categories_bp
from backend.routes.comments import bp as comments_bp
from backend.routes.history import bp as history_bp
from backend.routes.movies import bp as movies_bp
from backend.routes.payment import bp as payment_bp
from backend.routes.ratings import bp as ratings_bp
from backend.routes.settings import bp as settings_bp


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.config.from_object(config_class)

    init_mongo(app)
    limiter.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(movies_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(admin_movies_bp)
    app.register_blueprint(admin_users_bp)
    app.register_blueprint(admin_dashboard_bp)
    app.register_blueprint(admin_logs_bp)
    app.register_blueprint(admin_settings_bp)
    app.register_blueprint(comments_bp)
    app.register_blueprint(ratings_bp)
    app.register_blueprint(payment_bp)

    @app.before_request
    def _before():
        optional_auth()
        blocked = maintenance_check()
        if blocked is not None:
            return blocked

    @app.get("/api/health")
    def health():
        ok_db = False
        try:
            get_connection().admin.command("ping")
            ok_db = True
        except Exception:
            ok_db = False
        return jsonify({"ok": True, "db": ok_db})

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not Found"}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Server error"}), 500

    return app


def main():
    app = create_app()
    import backend.models  # noqa: F401 — register models

    app.run(host="127.0.0.1", port=Config.PORT, debug=True, use_reloader=False)


if __name__ == "__main__":
    main()
