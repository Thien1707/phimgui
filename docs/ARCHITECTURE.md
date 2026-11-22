# ARCHITECTURE.md — Kiến trúc PHIMHAY-GUI

## 1. Phương án đề xuất (chính thức)

**Desktop GUI (CustomTkinter) + Flask REST API (localhost) + MySQL**

```mermaid
flowchart TB
  subgraph Desktop["Windows Desktop"]
    GUI[CustomTkinter App]
    WEB[pywebview / browser cho player]
  end
  subgraph Backend["Flask (127.0.0.1:5000)"]
    RT[routes/]
    SV[services/]
    RP[repositories/]
  end
  DB[(MySQL)]
  EXT[phimapi.com]
  VNP[VNPay optional]

  GUI -->|requests + JWT| RT
  RT --> SV --> RP --> DB
  SV --> EXT
  GUI --> WEB
  GUI -->|mở browser| VNP
  VNP --> RT
```

### Vai trò từng lớp

| Lớp | Trách nhiệm |
|-----|-------------|
| **GUI** | Hiển thị màn hình, validate form cơ bản, lưu token local, gọi HTTP API, loading/error states |
| **Flask routes** | HTTP, auth decorator, parse JSON, status codes |
| **services** | Nghiệp vụ: playback access, VIP, import phim, dashboard aggregates |
| **repositories** | SQL thuần hoặc SQLAlchemy queries |
| **MySQL** | Persistence users, movies, history, payments, logs |

Flask **không** phục vụ static React; chỉ JSON API (+ optional Swagger).

## 2. So sánh phương án

| Tiêu chí | GUI + Flask + MySQL | GUI + SQLAlchemy trực tiếp |
|----------|---------------------|----------------------------|
| Đúng yêu cầu đề bài | Có | Flask bị bỏ qua |
| Tách lớp rõ | Cao | Trung bình |
| Test API độc lập | Dễ (pytest + client) | Khó hơn |
| Độ phức tạp triển khai | 2 process (Flask + GUI) | 1 process |
| Mở rộng multi-client sau này | Có | Hạn chế |

**Kết luận:** Dùng **GUI + Flask + MySQL**. Script `run.py` hoặc `start.bat` khởi chạy Flask nền rồi mở GUI (hoặc subprocess từ GUI).

### Phương án GUI

| Thư viện | Ưu | Nhược |
|----------|-----|-------|
| **CustomTkinter** (đề xuất) | Hiện đại, pip install, Windows ổn | Video player cần tích hợp riêng |
| Tkinter thuần | Có sẵn Python | Giao diện cũ |
| PyQt6 | Mạnh, đẹp | Cài nặng, license awareness |
| Flet | Flutter-like | Thêm dependency lớn |

**Đề xuất:** CustomTkinter cho shell app; **pywebview** hoặc **tkinterweb** cho iframe `link_embed`; fallback mở trình duyệt nếu embed lỗi.

## 3. Giao tiếp GUI ↔ Flask

- Base URL: `http://127.0.0.1:5000` (config `API_BASE_URL` trong GUI).
- Auth: header `Authorization: Bearer <token>`.
- Token lưu file local `%APPDATA%/PHIMHAY-GUI/token.json` hoặc keyring (P2).
- Client HTTP: `httpx` hoặc `requests` với timeout 30s.
- Threading: gọi API trong `threading.Thread` + `queue` để không block UI main loop.

## 4. Cấu hình

```
.env
  FLASK_ENV=development
  SECRET_KEY=...
  JWT_SECRET=...
  DATABASE_URL=mysql+pymysql://user:pass@127.0.0.1:3306/phimhay_gui
  PHIMAPI_BASE=https://phimapi.com
  VNP_* (optional)
  VIP_DURATION_DAYS=30
```

- Flask: `python-dotenv` load at startup.
- GUI: đọc `.env` hoặc `config.json` riêng chỉ `API_BASE_URL`.

## 5. Bảo mật

| Mục | Cách làm |
|-----|----------|
| Password | bcrypt (passlib) |
| JWT | PyJWT, exp 7d, sub=user id |
| SQL injection | Parameterized queries / SQLAlchemy |
| Admin routes | `@require_roles('admin')` |
| Rate limit | Flask-Limiter trên `/api/auth/login` |
| CORS | Chỉ allow localhost GUI nếu bật CORS |

## 6. Xử lý lỗi

- Repository: raise domain exceptions (`NotFound`, `Conflict`).
- Routes: `@app.errorhandler` → JSON `{ "error": "..." }`.
- GUI: map HTTP status → toast/dialog tiếng Việt.

## 7. Tích hợp phimapi

Giữ service `PhimApiClient` (httpx) mirror `server/src/services/phimapi.js`:

- `fetch_movie_by_slug(slug)`
- `fetch_new_movies(page)`

Timeout 25s, map lỗi 502 cho GUI.

## 8. VNPay trên desktop (Should-have)

1. GUI gọi `POST /api/payment/vnpay-create` → nhận `payUrl`.
2. `webbrowser.open(payUrl)`.
3. Return URL trỏ về Flask → redirect custom scheme hoặc trang `http://127.0.0.1:5000/payment/success` hiển thị "Quay lại app".
4. GUI poll `GET /api/auth/me` hoặc `GET /api/payment/status/{txnRef}` (endpoint bổ sung) để refresh VIP.

Nếu sandbox VNPay phức tạp: **admin gán VIP** đủ cho demo (FR-07 vẫn đạt).

## 9. Khởi chạy (dev)

```text
# Terminal 1
venv\Scripts\activate
python -m backend.app

# Terminal 2
python -m gui.main
```

Hoặc `python run_desktop.py` spawn Flask thread + GUI.

## 10. Mở rộng tương lai

- Tách Flask lên server LAN (giữ contract API).
- Redis cache phimapi.
- Web admin song song (Flask + Jinja) — không bắt buộc.
