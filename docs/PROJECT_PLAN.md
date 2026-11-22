# PROJECT_PLAN.md — Kế hoạch PHIMHAY-GUI

## 1. Tên & vị trí dự án

- **Tên:** PHIMHAY-GUI  
- **Thư mục đề xuất:** `D:\PHIMHAY-GUI`  
- **Dự án tham chiếu (read-only):** `D:\PHIMHAY`

## 2. Stack mục tiêu

| Hạng mục | Lựa chọn |
|----------|----------|
| Language | Python 3.11+ |
| Backend | Flask 3.x |
| ORM/DB | SQLAlchemy 2 + PyMySQL |
| GUI | **CustomTkinter** |
| Player | pywebview (embed) + fallback browser |
| Config | python-dotenv |
| Auth | PyJWT + bcrypt |
| HTTP client (GUI) | httpx |
| Validation | Pydantic v2 |
| Docs API | flasgger hoặc flask-smorest (P1) |

## 3. Feature mapping

| STT | Chức năng PHIMHAY | Cách hoạt động hiện tại | Flask + GUI | Ưu tiên |
|-----|-------------------|-------------------------|-------------|---------|
| 1 | Đăng ký / đăng nhập | Express + JWT + bcrypt Mongo User | Flask auth routes + Login/Register views | **Must** |
| 2 | Hồ sơ cá nhân | PUT `/api/auth/me` | Giữ API + ProfileView | **Must** |
| 3 | Danh sách phim | Mongo `Movie` paginate | SQL query + Home grid | **Must** |
| 4 | Tìm kiếm | Regex title/originName | SQL LIKE + Browse | **Must** |
| 5 | Lọc type/country/category | Query params | Combobox filters | **Must** |
| 6 | Chi tiết phim | DB + phimapi episodes | PhimApiClient + DetailView | **Must** |
| 7 | Xem phim (player) | React iframe embed | pywebview WatchView | **Must** |
| 8 | VIP-only content | viewStatus=1 | Service `playback_access` | **Must** |
| 9 | Lịch sử / continue | WatchHistory collection | MySQL + History/Home | **Must** |
| 10 | Bình luận | Comment model | comments routes + UI panel | **Must** |
| 11 | Đánh giá sao | Rating unique pair | ratings routes + stars widget | **Must** |
| 12 | Admin import phim | slug → phimapi → Movie.create | Admin import dialog | **Must** |
| 13 | Admin sửa/xóa phim | PATCH/DELETE admin movies | AdminMoviesView | **Must** |
| 14 | Category CRUD | Transaction Mongo | Junction table + admin UI | **Must** |
| 15 | Gán series | seriesId updateMany | FK series_id + admin tool | **Should** |
| 16 | Quản lý user | ban/role/vip/reset | AdminUsersView | **Must** |
| 17 | Dashboard thống kê | Mongo aggregate | SQL aggregate + admin | **Should** |
| 18 | Activity logs | ActivityLog | Bảng activity_logs + table UI | **Should** |
| 19 | System settings | SystemSettings singleton | settings row + admin form | **Must** |
| 20 | Maintenance mode | Middleware 503 | Flask before_request + GUI gate | **Must** |
| 21 | Rate limit auth | express-rate-limit | Flask-Limiter | **Should** |
| 22 | VNPay VIP | Redirect web + callback | Browser open + poll status | **Could** |
| 23 | Swagger | swagger-ui-express | flasgger optional | **Could** |
| 24 | Yêu thích | **Không tồn tại** | Bảng favorites P2 | **Could** |
| 25 | Deploy Render/Vercel | Node monorepo | Desktop local + README | N/A (thay đổi) |
| 26 | Email SMTP | Config only in settings | Bỏ qua hoặc P2 | **Could** |

## 4. Cấu trúc thư mục đề xuất

```text
PHIMHAY-GUI/
├── backend/
│   ├── app.py                 # create_app(), run dev server
│   ├── config.py
│   ├── extensions.py          # db, limiter
│   ├── routes/
│   │   ├── auth.py
│   │   ├── movies.py
│   │   ├── categories.py
│   │   ├── comments.py
│   │   ├── ratings.py
│   │   ├── history.py
│   │   ├── payment.py
│   │   ├── settings.py
│   │   └── admin/
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── movie_service.py
│   │   ├── phimapi_client.py
│   │   ├── vip_service.py
│   │   ├── dashboard_service.py
│   │   └── activity_log_service.py
│   ├── repositories/
│   │   └── ...                # SQL queries per aggregate
│   ├── models/
│   │   └── ...                # SQLAlchemy models
│   └── middleware/
│       ├── auth.py
│       └── maintenance.py
├── gui/
│   ├── main.py
│   ├── api_client.py
│   ├── session.py             # token storage
│   ├── theme.py
│   ├── views/
│   │   ├── login.py
│   │   ├── home.py
│   │   ├── movie_detail.py
│   │   ├── watch.py
│   │   └── admin/
│   └── widgets/
│       ├── movie_card.py
│       └── pagination.py
├── database/
│   └── init.sql
├── tests/
│   ├── test_auth.py
│   ├── test_movies.py
│   └── test_vip.py
├── docs/                      # deliverables planning
├── .env.example
├── requirements.txt
├── run_desktop.py             # spawn flask + gui
└── README.md
```

### Nhiệm vụ thư mục

| Path | Vai trò |
|------|---------|
| `backend/routes` | HTTP layer, không business nặng |
| `backend/services` | Rules: VIP, import, playback |
| `backend/repositories` | SQL tái sử dụng |
| `gui/views` | Một file ≈ một màn hình |
| `database/` | DDL, không auto-run trong CI ban đầu |

## 5. Rủi ro & mitigations

| Rủi ro | Mức | Xử lý |
|--------|-----|-------|
| phimapi downtime/đổi API | Cao | Timeout, thông báo rõ; cache P2 |
| Embed video trong Tk | Trung bình | pywebview; fallback browser |
| VNPay sandbox desktop | Trung bình | Admin gán VIP; payment P2 |
| 2 process Flask+GUI | Thấp | `run_desktop.py` tự spawn |
| MySQL cài đặt sinh viên | Trung bình | README + Workbench screenshots |
| M3U8/HLS codec | Trung bình | Dùng embed URL như web gốc |

## 6. Deliverables planning (đã tạo)

| File | Path |
|------|------|
| PROJECT_ANALYSIS.md | `docs/` |
| PROJECT_PLAN.md | `docs/` |
| REQUIREMENTS.md | `docs/` |
| ARCHITECTURE.md | `docs/` |
| DATABASE_DESIGN.md | `docs/` |
| API_SPECIFICATION.md | `docs/` |
| GUI_DESIGN.md | `docs/` |
| DEVELOPMENT_ROADMAP.md | `docs/` |
| init.sql (design) | `database/` |

## 7. Bước tiếp theo (sau khi bạn xác nhận)

1. Khởi tạo `venv`, `requirements.txt`, skeleton Flask + CustomTkinter.  
2. Chạy `init.sql` trên MySQL Workbench.  
3. Implement Phase 4 theo thứ tự auth → movies → admin.  
4. GUI Phase 5 song song từng màn hình Must-have.

**Chờ xác nhận kế hoạch trước khi viết code ứng dụng.**
