# PHIMHAY-GUI

Đồ án xem phim trực tuyến gồm hai giao diện cùng đề tài: desktop Python/CustomTkinter và web Flask/Jinja2. Cả hai dùng chung MongoDB cho catalog phim. Web dùng thêm Flask-SQLAlchemy cho tài khoản, bình luận, lịch sử và bản chiếu catalog; SQLite là database mặc định cho các dữ liệu SQL này. Cấu hình `WEB_DATABASE_URL` có thể chuyển phần SQL sang một database SQLAlchemy khác.

## Cài đặt

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### Khởi chạy phiên bản web

Trong `.env`, đặt `WEB_SECRET_KEY` thành giá trị ngẫu nhiên riêng. Khởi tạo cơ sở dữ liệu và tạo tài khoản quản trị:

```bat
flask --app run_web.py init-db
flask --app run_web.py create-admin
flask --app run_web.py sync-desktop-movies
python run_web.py
```

Mở `http://127.0.0.1:5001`. Web và desktop dùng MongoDB chung làm nguồn catalog. Web đọc thay đổi từ desktop khi có request; trang danh mục và chi tiết đang mở kiểm tra cập nhật khoảng mỗi 15 giây. Admin web chỉ cần nhập slug để lấy metadata từ phimapi, rồi có thể sửa trường phim. Thao tác web được ghi ngược vào MongoDB để desktop nhận thay đổi. Lệnh `sync-desktop-movies` vẫn có thể dùng để đồng bộ ngay. Cần có `MONGODB_URI` kết nối được trong `.env`. Khi cấu hình SMTP, ứng dụng gửi email chào mừng sau đăng ký; nếu chưa cấu hình SMTP, tài khoản vẫn được tạo và ứng dụng báo rõ email chưa gửi.

Endpoint JSON có phân trang: `GET /api/movies?q=batman&page=1&limit=12`. Chi tiết/phát phim yêu cầu kết nối `phimapi.com`; tính năng còn lại dùng dữ liệu trong cơ sở dữ liệu cục bộ.

### Ứng dụng desktop/API hiện có

Ứng dụng desktop tiếp tục dùng MongoDB và chạy như trước:

```bat
python -m backend.seed
python run_desktop.py
```

Thiết lập `MONGODB_URI` trong `.env` trước khi chạy. API desktop mặc định tại `http://127.0.0.1:5000`.

## Tính năng phiên bản web

- Đăng ký, đăng nhập, đăng xuất; mật khẩu được băm bằng Werkzeug và biểu mẫu được bảo vệ CSRF.
- Danh sách phim, tìm theo tên tiếng Việt/tên gốc và phân trang.
- CRUD phim dành cho tài khoản quản trị.
- Chi tiết phim, bình luận có đăng nhập, lưu lịch sử khi bắt đầu xem.
- Tích hợp phimapi bằng `urllib`, phân tích JSON và nhúng trình phát từ API ngoài.
- REST endpoint trả danh sách phim JSON có phân trang.
- Gửi email chào mừng bằng Flask-Mail khi SMTP được cấu hình.

## Cấu trúc liên quan

```text
app/                 Flask app factory, models, forms, routes, templates, static
backend/             REST API và nghiệp vụ desktop hiện có
gui/                 Giao diện CustomTkinter
docs/                Phân tích, thiết kế và báo cáo đồ án
run_web.py           Chạy phiên bản web trên localhost:5001
run_desktop.py       Chạy backend desktop và GUI
```

## Báo cáo

Nội dung và bản DOCX báo cáo được lưu trong `docs/`. Thông tin nhóm, MSSV và ảnh chụp chạy thực tế cần được bổ sung trước khi nộp chính thức.
