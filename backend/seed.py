"""Tạo admin mẫu và settings. Chạy: python -m backend.seed"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import bcrypt

from backend.app import create_app
from backend.models import Category, SystemSettings, User


def main():
    app = create_app()
    uri = app.config.get("MONGODB_URI", "")
    if "127.0.0.1" in uri or uri.startswith("mongodb://localhost"):
        print(
            "Cảnh báo: đang trỏ MongoDB local. Thêm MONGODB_URI Atlas vào file .env "
            "(xem .env.example)."
        )
    with app.app_context():
        import backend.models  # noqa: F401

        if not SystemSettings.objects(setting_key="global").first():
            SystemSettings(setting_key="global", site_name="PHIMHAY-GUI").save()
        for name, display in (
            ("hoathinh", "Hoạt Hình"),
            ("series", "Phim bộ"),
            ("single", "Phim lẻ"),
        ):
            if not Category.objects(name=name).first():
                Category(name=name, display_name=display).save()

        email = "admin@local.test"
        user = User.objects(email=email).first()
        if not user:
            pwd = bcrypt.hashpw(b"Admin@123", bcrypt.gensalt(10)).decode()
            user = User(
                email=email,
                display_name="admin",
                password_hash=pwd,
                role="admin",
            )
            user.save()
            print("Created admin: admin@local.test / Admin@123 (display_name: admin)")
        else:
            print("Admin already exists:", email)
        print("Seed done.")


if __name__ == "__main__":
    main()
