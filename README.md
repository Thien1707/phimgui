# PHIMHAY-GUI

Dự án desktop **Python + Flask + MongoDB + CustomTkinter**, tái hiện nghiệp vụ từ [`D:\PHIMHAY`](../PHIMHAY).

## Cài đặt nhanh (Windows)

1. Tạo cluster **MongoDB Atlas** (hoặc chạy MongoDB local), tạo user DB và whitelist IP.
2. Copy `.env.example` → `.env`, điền `MONGODB_URI` (user/password cluster — password đặc biệt cần URL-encode).
3. Trong thư mục dự án:

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m backend.seed
python run_desktop.py
```

Hoặc double-click `start.bat` (sau khi đã cấu hình MongoDB).

**Tài khoản admin mẫu** (sau seed): `admin@local.test` / `Admin@123` (display_name: `admin`).

## Tính năng app (GUI)

- Trang chủ: tìm kiếm, lọc loại / quốc gia / thể loại, phân trang
- Trang chủ: poster hover (hand cursor), nhấp vào poster → chi tiết
- Chi tiết: nút **Xem phim** → trang xem trong cùng cửa sổ (sidebar ẩn, nút ← / Esc quay lại chi tiết)
- Trình phát nhúng: **VLC** cho `.m3u8` (cài [VLC](https://www.videolan.org/) trên Windows) hoặc **tkinterweb** cho link embed
- Lưu lịch sử, bình luận, đánh giá sao
- Lịch sử xem / xem tiếp, hồ sơ cá nhân, mua VIP (VNPay nếu cấu hình `.env`)
- **Quản trị** (admin): dashboard, import phim theo slug, VIP/free, users, cài đặt hệ thống, nhật ký

Mật khẩu MongoDB có ký tự `@` trong `.env` phải URL-encode (`@` → `%40`).

## Chạy tách backend / GUI

```bat
venv\Scripts\activate
python -m backend.app
python -m gui.main
```

## Tài liệu

| File | Mô tả |
|------|--------|
| [docs/PROJECT_ANALYSIS.md](docs/PROJECT_ANALYSIS.md) | Phân tích PHIMHAY gốc |
| [docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md) | Kế hoạch tổng thể + feature mapping |
| [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) | Yêu cầu chức năng / phi chức năng |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Kiến trúc Flask + GUI |
| [docs/DATABASE_DESIGN.md](docs/DATABASE_DESIGN.md) | Thiết kế MySQL |
| [docs/API_SPECIFICATION.md](docs/API_SPECIFICATION.md) | API dự kiến |
| [docs/GUI_DESIGN.md](docs/GUI_DESIGN.md) | Màn hình desktop |
| [docs/DEVELOPMENT_ROADMAP.md](docs/DEVELOPMENT_ROADMAP.md) | Lộ trình & kiểm thử |

SQL khởi tạo (chưa thực thi): [database/init.sql](database/init.sql)
