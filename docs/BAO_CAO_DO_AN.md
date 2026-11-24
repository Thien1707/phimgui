# BÁO CÁO ĐỒ ÁN MÔN HỌC
## Lập trình Python nâng cao

**Đề tài:** Xây dựng ứng dụng xem phim PHIMHAY bằng Flask  
**Mã học phần:** 71ITSE31003 · **Nhóm lớp:** 253_71ITSE31003_01  
**Giảng viên hướng dẫn:** Ths Nguyễn Thị Mỹ Linh  
**Nhóm thực hiện:** Nhóm [điền số nhóm] · tối đa 3 sinh viên  
**Thành viên:** [điền MSSV, họ tên và nhiệm vụ]  
**Địa điểm, thời gian:** TP. Hồ Chí Minh, tháng [..] năm 20[..]

> Báo cáo mô tả phiên bản web Flask được bổ sung cho đề tài xem phim PHIMHAY-GUI. Thông tin thành viên và ảnh chụp chạy ứng dụng cần được nhóm bổ sung. Tình trạng kiểm thử được ghi theo những gì đã thực hiện; chưa chạy kiểm thử trong lần cập nhật này.

## 1. Giới thiệu đề tài

### 1.1 Mô tả bài toán

Người xem phim trực tuyến cần một nơi tập trung để tra cứu tên phim, xem thông tin nội dung, mở nguồn phát và ghi nhớ những phim đã xem. Quản trị viên cần thêm, cập nhật và xóa thông tin phim mà không thao tác trực tiếp trên cơ sở dữ liệu. Đề tài xây dựng PHIMHAY, một ứng dụng web tiếng Việt dùng Flask. Khách có thể tìm kiếm danh mục; thành viên có thể đăng ký, đăng nhập, bình luận và bắt đầu xem; quản trị viên có thể quản lý phim. Ứng dụng lấy dữ liệu tập phim và đường dẫn nhúng từ phimapi.com.

Repo ban đầu đã có REST API Flask, MongoDB và giao diện desktop CustomTkinter. Để đáp ứng mẫu học phần yêu cầu trình bày ứng dụng Flask web, nhóm bổ sung phiên bản web có Jinja2, Flask-WTF, Flask-SQLAlchemy và Flask-Mail. Hai giao diện dùng chung MongoDB làm nguồn catalog. SQLAlchemy duy trì bản chiếu dữ liệu phục vụ các truy vấn web và các bảng tài khoản/bình luận/lịch sử. Web cập nhật bản chiếu khi có request; trang danh mục kiểm tra thay đổi định kỳ.

### 1.2 Mục tiêu và phạm vi

Mục tiêu là triển khai một ứng dụng web có đăng ký/đăng nhập, CRUD nội dung phim, tìm kiếm, phân trang, form có xác thực dữ liệu, lưu dữ liệu quan hệ, gửi email khi cấu hình SMTP và trao đổi JSON với API ngoài. Phạm vi hiện tại gồm tài khoản cơ bản, danh mục phim, bình luận, lịch sử bắt đầu xem và một endpoint REST phân trang. Admin nhập slug phimapi để tự lấy metadata, rồi có thể sửa thông tin; CRUD web ghi ngược catalog MongoDB dùng chung. Chức năng VNPay, đánh giá sao và cấu hình hệ thống hiện có trong desktop chưa được gộp vào giao diện web.

### 1.3 Công nghệ sử dụng

| Thành phần | Công nghệ / vai trò |
|---|---|
| Ngôn ngữ, web | Python 3, Flask app factory và blueprints |
| Giao diện | Jinja2, HTML và CSS responsive |
| Form, bảo mật | Flask-WTF, WTForms, CSRFProtect, Werkzeug password hash, Flask-Login |
| Dữ liệu web | MongoDB chung cho catalog phim; SQLAlchemy cho bản chiếu truy vấn web, tài khoản, bình luận và lịch sử |
| Email | Flask-Mail; SMTP lấy từ biến môi trường |
| Lập trình mạng | urllib.request, JSON, phimapi.com; endpoint REST trả JSON |
| Ứng dụng hiện hữu | CustomTkinter, Flask REST API, MongoEngine/MongoDB, httpx, VLC/webview |

### 1.4 Phân công công việc

| Thành viên | Nhiệm vụ | Đóng góp |
|---|---|---:|
| [MSSV – Họ tên] | [Phân tích, mô hình dữ liệu, backend] | [..]% |
| [MSSV – Họ tên] | [Giao diện, form, tích hợp API] | [..]% |
| [MSSV – Họ tên] | [Kiểm thử, tài liệu, triển khai] | [..]% |

Nhóm cập nhật thông tin thật và tổng mức đóng góp 100% trước khi nộp.

## 2. Phân tích và thiết kế hệ thống

### 2.1 Chức năng của hệ thống

| Vai trò | Chức năng |
|---|---|
| Khách | Xem danh sách phim, tìm kiếm, chuyển trang, xem chi tiết; đăng ký và đăng nhập |
| Thành viên | Đăng xuất, bình luận, gọi nguồn phim và lưu lịch sử bắt đầu xem |
| Quản trị | Thêm, sửa, xóa phim; đánh dấu nội dung VIP; xem danh mục như người dùng |
| Tích hợp | Đọc JSON từ phimapi.com; cung cấp `/api/movies` với tìm kiếm và phân trang |

Luồng chính: khách mở danh mục → tìm phim hoặc chuyển trang → mở chi tiết → đăng nhập → gọi dữ liệu tập phim từ phimapi → xem nội dung nhúng. Quản trị viên đăng nhập → tạo hoặc sửa thông tin phim → dữ liệu được ghi vào cơ sở dữ liệu SQLAlchemy. Các thao tác thay đổi trạng thái dùng POST và form có CSRF.

### 2.2 Thiết kế cơ sở dữ liệu

Phiên bản web có bốn model chính trong `app/models.py`.

| Model | Cột chính | Khóa và quan hệ |
|---|---|---|
| User | id, username, email, password_hash, role, created_at | id PK; username và email unique; 1–n Comment, WatchHistory |
| Movie | id, slug, title, origin_name, description, poster_url, year, category, is_vip, is_active | id PK; slug unique; 1–n Comment, WatchHistory |
| Comment | id, body, created_at, user_id, movie_id | id PK; FK tới User và Movie |
| WatchHistory | id, watched_at, user_id, movie_id | id PK; FK tới User và Movie |

Quan hệ khái quát: `User 1—n Comment`, `Movie 1—n Comment`, `User 1—n WatchHistory`, `Movie 1—n WatchHistory`. Mật khẩu không được lưu dạng văn bản; model User dùng hàm băm và kiểm tra mật khẩu của Werkzeug. SQLite tạo file `instance/phimhay_web.db` khi khởi tạo. `WEB_DATABASE_URL` cho phép cấu hình cơ sở dữ liệu khác tương thích SQLAlchemy.

### 2.3 Thiết kế giao diện

Các trang dùng chung `base.html` làm khung điều hướng và nạp stylesheet dùng chung. Danh mục có thanh tìm kiếm, thẻ phim và điều hướng phân trang. Trang chi tiết có thông tin phim, nút xem, khu vực bình luận và thao tác sửa/xóa dành cho admin. Trang đăng nhập/đăng ký và form quản trị dùng cùng thành phần trường nhập, thông báo lỗi và nút thao tác. Trang xem dùng iframe cho URL embed nhận từ API ngoài. CSS co giãn cho màn hình nhỏ.

**Hình 2.1.** Luồng màn hình: Danh mục → Chi tiết → Đăng nhập (nếu cần) → Xem phim; Admin → Thêm/Sửa phim.  
**Hình 2.2.** Sơ đồ quan hệ: User 1–n Comment; Movie 1–n Comment; User 1–n WatchHistory; Movie 1–n WatchHistory.

## 3. Xây dựng ứng dụng với Flask

### 3.1 Môi trường và cấu trúc dự án

Ứng dụng web khởi tạo qua `create_app()` trong `app/__init__.py`; extensions được khởi tạo riêng và route đăng ký theo blueprint. Cấu trúc chính:

```text
app/
  __init__.py             app factory, extension, CLI
  models.py               User, Movie, Comment, WatchHistory
  forms.py                form đăng nhập, đăng ký, phim, tìm kiếm, bình luận
  routes/
    auth.py               đăng ký, đăng nhập, đăng xuất
    catalog.py            danh mục, tìm kiếm, phân trang, API JSON
    movies.py              chi tiết, bình luận, xem, lịch sử, admin CRUD
  templates/              base, auth, catalog, admin
  static/style.css        giao diện responsive
run_web.py                entry point của ứng dụng web
backend/, gui/            API và ứng dụng desktop hiện có
```

Chạy trên Windows: tạo virtual environment, cài `pip install -r requirements.txt`, sao chép `.env.example` thành `.env`, cấu hình `WEB_SECRET_KEY`; sau đó chạy `flask --app run_web.py init-db`, `flask --app run_web.py create-admin` và `python run_web.py`. Web mặc định ở `127.0.0.1:5001`. SQLite dùng cho khởi chạy mẫu; MySQL cần được cài và đặt URL driver phù hợp trong `WEB_DATABASE_URL`.

### 3.2 Routes và xử lý nghiệp vụ

`auth` tiếp nhận GET để hiển thị form và POST để kiểm tra dữ liệu. Sau đăng nhập thành công, Flask-Login quản lý phiên và nạp User từ database. Route quản trị kiểm tra role trước các thao tác CRUD. `catalog.index` lọc `title` hoặc `origin_name`, sau đó dùng phân trang SQLAlchemy với 12 bản ghi mỗi trang. Route `/api/movies` trả `items` cùng thông tin trang dưới dạng JSON. Các thay đổi dữ liệu đi qua POST; CSRFProtect được bật cho form.

`movies.detail` tải Movie và Comment liên quan. `movies.watch` yêu cầu đăng nhập, gọi phimapi, ghi WatchHistory và hiển thị URL embed nếu API trả về. Route tạo, sửa, xóa phim giới hạn cho role admin. Trường `is_vip` được lưu và hiển thị nhãn; kiểm soát quyền VIP chưa được áp dụng cho phiên bản web.

### 3.3 Templates với Jinja2

`base.html` cung cấp HTML chung, điều hướng theo trạng thái đăng nhập, thông báo flash và liên kết tới API. Các trang con dùng `{% extends 'base.html' %}` và các block nội dung. Danh mục lặp qua `page.items`; nhánh `{% else %}` thông báo khi không có kết quả. Form dùng `hidden_tag()` để đưa CSRF token vào request. Giá trị từ người dùng được đưa qua cơ chế autoescape mặc định của Jinja2.

### 3.4 Web Forms với Flask-WTF

`RegisterForm`, `LoginForm`, `MovieForm`, `SearchForm` và `CommentForm` được khai báo trong `app/forms.py`. Validator kiểm tra trường bắt buộc, định dạng email, độ dài, xác nhận mật khẩu và khoảng năm hợp lệ. Route chỉ ghi dữ liệu khi `validate_on_submit()` trả về đúng; lỗi hiển thị cạnh trường. CSRFProtect áp dụng cho form POST, gồm đăng xuất và thao tác admin.

### 3.5 Cơ sở dữ liệu với Flask-SQLAlchemy

Model khai báo cột và khóa ngoại bằng SQLAlchemy ORM. Route tạo/sửa/xóa cập nhật MongoDB catalog trước, sau đó lưu bản chiếu SQL qua `db.session`; request danh mục lấy thay đổi mới từ MongoDB để desktop và web hội tụ. Tài khoản, bình luận và lịch sử tiếp tục lưu SQL. Lệnh Flask `init-db` tạo bảng cho môi trường mới. Dự án chưa cấu hình Flask-Migrate, do đó thay đổi schema cần có quy trình migration trước khi triển khai dữ liệu lâu dài.

### 3.6 Gửi email với Flask-Mail

Sau khi tạo tài khoản, route đăng ký gửi email chào mừng qua Flask-Mail. Máy chủ, cổng, TLS, username và password được đọc từ biến môi trường `MAIL_*`, không ghi trực tiếp vào mã nguồn. Nếu SMTP chưa cấu hình hoặc không kết nối được, tài khoản vẫn được tạo và giao diện báo email chưa gửi. Chức năng hiện tại chưa có xác minh email hay email đặt lại mật khẩu.

### 3.7 Lập trình mạng và tích hợp API

Hàm `fetch_phimapi()` tạo HTTP Request bằng `urllib.request`, đặt header JSON và timeout 8 giây, đọc response UTF-8 rồi phân tích bằng `json.loads`. Route xem phim dùng slug của Movie để gọi endpoint `/phim/{slug}` tại phimapi.com. Lỗi HTTP, mạng, timeout hoặc JSON không hợp lệ được bắt và trả thông báo thân thiện. Không cần API key cho endpoint được dùng. Endpoint nội bộ `GET /api/movies` cũng trả JSON phân trang để client khác sử dụng.

### 3.8 Chức năng mở rộng

Ứng dụng lưu lịch sử bắt đầu xem, bình luận, gắn nhãn VIP, nhúng trình phát và có REST API. Catalog dùng MongoDB chung; web đồng bộ thay đổi từ desktop trong các lần tải dữ liệu và tự kiểm tra trang danh mục định kỳ. Import bằng slug lấy metadata tự động; sửa/xóa ở web được ghi vào MongoDB để desktop thấy thay đổi. Repo còn có bản desktop với VNPay, đánh giá sao, lịch sử chi tiết và quản trị users/settings/logs. Hướng phát triển web gồm kiểm soát quyền VIP, đánh giá sao, dashboard và migration.

## 4. Kết quả và kiểm thử

### 4.1 Kết quả giao diện

Các màn hình được triển khai trong template gồm danh mục/tìm kiếm, đăng nhập, đăng ký, chi tiết/bình luận, xem phim, lịch sử và biểu mẫu thêm/sửa phim. Trước khi nộp, chèn ảnh chụp thực tế từ ứng dụng đang chạy, không dùng ảnh minh họa thay cho ảnh kết quả.

| Vị trí ảnh cần bổ sung | Nội dung cần chụp |
|---|---|
| Hình 4.1 | Danh mục phim và thanh tìm kiếm |
| Hình 4.2 | Trang đăng nhập hoặc đăng ký |
| Hình 4.3 | Chi tiết phim và bình luận |
| Hình 4.4 | Biểu mẫu admin thêm/sửa phim |
| Hình 4.5 | Danh sách có phân trang hoặc trang xem phim |

### 4.2 Kiểm thử chức năng

Chưa chạy kiểm thử tự động hoặc kiểm thử end-to-end trên trình duyệt. Đã chạy lệnh đồng bộ catalog với MongoDB hiện cấu hình và xác nhận 6 phim hoạt động trong bản chiếu SQLAlchemy. Các luồng còn lại trong bảng vẫn cần nhóm thực thi.

| Kịch bản | Dữ liệu thử | Kết quả mong đợi | Kết quả thực tế |
|---|---|---|---|
| Đăng ký hợp lệ | Email mới, mật khẩu ≥ 8 ký tự | User được tạo, chuyển về danh mục; gửi mail nếu SMTP hoạt động | Chưa chạy |
| Đăng ký trùng | Email hoặc username đã có | Báo lỗi, không tạo bản ghi trùng | Chưa chạy |
| Đăng nhập sai/đúng | Email và mật khẩu | Sai: báo lỗi; đúng: tạo phiên | Chưa chạy |
| Tìm kiếm và phân trang | Nhiều phim, q và page | Chỉ hiện kết quả phù hợp, chuyển trang đúng | Chưa chạy |
| CRUD phim | Admin thêm/sửa/xóa | Dữ liệu lưu SQL và hiển thị lại | Chưa chạy |
| Phân quyền CRUD | User thường gọi route admin | Trả 403 | Chưa chạy |
| Bình luận có CSRF | Thành viên gửi nội dung; request thiếu token | Lưu bình luận hợp lệ; request thiếu token bị từ chối | Chưa chạy |
| Tích hợp phimapi | Slug tồn tại và mạng lỗi | Nhúng URL nếu có; báo lỗi thân thiện khi API lỗi | Chưa chạy |
| API JSON | `/api/movies?page=1&limit=12` | JSON gồm items và pagination | Chưa chạy |
| Đồng bộ catalog | MongoDB desktop hiện có | Bản chiếu SQL web nhận đủ phim theo slug | Đã đồng bộ 6 phim |

## 5. Kết luận và hướng phát triển

Đề tài giữ nguyên chủ đề xem phim và hiện có hai trải nghiệm: ứng dụng desktop/API cũ và web app Flask đáp ứng cấu trúc của mẫu học phần. Web app đã có app factory, blueprints, Jinja2, Flask-WTF, SQLAlchemy, Flask-Login, Flask-Mail, CRUD phim, tìm kiếm, phân trang, bình luận, lịch sử và tích hợp JSON/API ngoài. Do chưa chạy kiểm thử trong lần chỉnh sửa này, báo cáo không kết luận các luồng đã đạt; nhóm cần cài gói, chạy ứng dụng, bổ sung ảnh chụp và ghi kết quả thật vào bảng kiểm thử.

Hạn chế hiện tại là email cần SMTP, phát phim phụ thuộc khả năng truy cập phimapi.com, kiểm soát VIP chưa nối vào web và chưa có migration schema. Hướng phát triển gồm thêm xác minh email/reset mật khẩu, quyền xem VIP và đánh giá sao, import phim bằng slug, migration Alembic, triển khai HTTPS và kiểm thử API/UI trên môi trường độc lập.

## Tài liệu tham khảo

[1] M. Grinberg, *Flask Web Development: Developing Web Applications with Python*, 2nd ed. Sebastopol, CA: O'Reilly Media, 2018.  
[2] Pallets Projects, “Flask Documentation.” [Truy cập: 24-11-2026].  
[3] Flask-SQLAlchemy, “Flask-SQLAlchemy Documentation.” [Truy cập: 24-11-2026].  
[4] Flask-WTF, “Flask-WTF Documentation.” [Truy cập: 24-11-2026].  
[5] PhimAPI, “API phim.” [Truy cập: 24-11-2026].

## Phụ lục A Hướng dẫn chạy

Tạo môi trường ảo, cài `requirements.txt`, cấu hình `.env`, chạy `flask --app run_web.py init-db`, tạo admin bằng `flask --app run_web.py create-admin`, sau đó chạy `python run_web.py`. Catalog dùng chung MongoDB với desktop và đồng bộ khi web nhận request; trang danh mục tự kiểm tra thay đổi định kỳ. Có thể gọi `flask --app run_web.py sync-desktop-movies` để ép đồng bộ ngay. Tạo tài khoản thành viên qua giao diện. Nguồn mã ở thư mục dự án hiện tại; chưa có URL GitHub được xác nhận. Không đưa thư mục virtual environment hoặc thông tin bí mật trong `.env` vào gói nộp.

## Phụ lục B Cơ sở dữ liệu và dữ liệu mẫu

Lệnh `init-db` tạo bảng SQLAlchemy trên SQLite cho tài khoản, bình luận, lịch sử và bản chiếu catalog. Catalog gốc dùng MongoDB chung với desktop. Quản trị viên nhập slug phimapi để tải metadata hoặc cập nhật metadata bằng biểu mẫu.
