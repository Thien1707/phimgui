# REQUIREMENTS.md — Yêu cầu dự án PHIMHAY-GUI

## 1. Mục tiêu

Xây dựng ứng dụng desktop Windows có chức năng nghiệp vụ **tương đương PHIMHAY**, dùng **Python 3**, **Flask**, **MySQL**, **GUI desktop**, quản lý DB bằng **MySQL Workbench**, môi trường **venv**.

## 2. Yêu cầu chức năng (Functional)

### 2.1 Must-have (P0)

| ID | Yêu cầu | Nguồn PHIMHAY |
|----|---------|---------------|
| FR-01 | Đăng ký, đăng nhập, JWT, phiên 7 ngày | `/api/auth` |
| FR-02 | Khách xem catalog; đăng nhập để xem phim | `playbackAccess` |
| FR-03 | Danh sách phim phân trang, lọc type/country/category | `GET /api/movies` |
| FR-04 | Tìm kiếm theo title/originName | `GET /api/movies/search` |
| FR-05 | Chi tiết phim + episodes từ phimapi | `GET /api/movies/:slug` |
| FR-06 | Phát video (embed/m3u8) trong desktop | `WatchPage` iframe |
| FR-07 | VIP gate (`viewStatus=1`) | Movie model |
| FR-08 | Lịch sử xem + continue watching | `/api/history` |
| FR-09 | Bình luận & đánh giá | comments, ratings |
| FR-10 | Admin: import phim by slug, CRUD metadata | `/api/admin/movies` |
| FR-11 | Admin: quản lý user (ban, role, reset pwd, VIP) | `/api/admin/users` |
| FR-12 | Admin: category CRUD + gán phim | `/api/categories` |
| FR-13 | Cài đặt hệ thống (maintenance, registration, comments) | SystemSettings |
| FR-14 | Health check API | `/api/health` |

### 2.2 Should-have (P1)

| ID | Yêu cầu |
|----|---------|
| FR-15 | Dashboard thống kê (users, movies, views, VIP) |
| FR-16 | Activity logs (đăng nhập, import, VIP, ...) |
| FR-17 | Gán nhiều phim vào series (`seriesId`) |
| FR-18 | Rate limiting auth/API cơ bản |
| FR-19 | Validation đầu vào (Pydantic hoặc marshmallow) |
| FR-20 | Swagger hoặc tài liệu API nội bộ |

### 2.3 Could-have (P2)

| ID | Yêu cầu | Ghi chú |
|----|---------|---------|
| FR-21 | Thanh toán VNPay từ desktop | Mở browser hệ thống + deep link return |
| FR-22 | Danh sách yêu thích | **Không có trong PHIMHAY gốc** — bổ sung mở rộng |
| FR-23 | Cache episode JSON vào MySQL | Giảm phụ thuộc phimapi |
| FR-24 | Đóng gói `.exe` (PyInstaller) | Phase 7 |
| FR-25 | Moderator role đầy đủ | Gốc có enum nhưng ít dùng |

## 3. Yêu cầu phi chức năng (Non-functional)

| ID | Yêu cầu |
|----|---------|
| NFR-01 | Chạy trên Windows 10/11 |
| NFR-02 | Cài đặt qua venv + `requirements.txt` |
| NFR-03 | GUI không kết nối trực tiếp MySQL (qua Flask) |
| NFR-04 | Mật khẩu hash (bcrypt/werkzeug) |
| NFR-05 | Secret qua `.env`, có `.env.example` |
| NFR-06 | Thông báo lỗi thân thiện (mất mạng, DB down) |
| NFR-07 | Code module hóa: routes / services / repositories |
| NFR-08 | UTF-8, hỗ trợ tiếng Việt |
| NFR-09 | Phù hợp sinh viên: dễ đọc, ít magic |

## 4. Ràng buộc kỹ thuật

- **Không** dùng React/Vite/Node làm stack chính dự án mới.
- **Có** Flask + MySQL + GUI desktop.
- Giữ tích hợp **phimapi.com** (giống bản gốc) trừ khi có cache P2.
- VNPay: tùy chọn P1/P2; có thể admin gán VIP thay thế tối thiểu.

## 5. Personas

| Persona | Nhu cầu |
|---------|---------|
| Guest | Duyệt phim, tìm kiếm, xem trailer/meta hạn chế |
| User | Xem phim, comment, rating, history, VIP |
| Admin | Import nội dung, quản trị user, settings, logs |

## 6. Tiêu chí chấp nhận tổng thể

1. User đăng nhập → xem phim VIP/normal đúng rule.
2. Admin import slug mới → phim xuất hiện trên GUI.
3. Lịch sử cập nhật khi xem → hiển thị continue watching.
4. Maintenance mode chặn user thường, admin vẫn vào được.
5. MySQL Workbench kết nối được schema đã thiết kế.
