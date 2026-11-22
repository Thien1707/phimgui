# GUI_DESIGN.md — Màn hình Desktop (CustomTkinter)

## 1. Nguyên tắc UX

- Dark theme mặc định (giống web PHIMHAY).
- Layout: **sidebar trái** (nav) + **content** + **status bar** (kết nối API/DB).
- Toast/snackbar cho success/error.
- Form validation trước khi gọi API.
- Loading: disable nút + spinner overlay.

## 2. Cấu trúc ứng dụng

```text
App (CTk)
├── AuthStack (login/register) — khi chưa có token
└── MainShell
    ├── Sidebar
    └── ContentFrame (swap views)
```

**Thư viện đề xuất:** `customtkinter`, `Pillow` (poster), `httpx`, `pywebview` (player).

## 3. Danh sách màn hình

### 3.1 Login (`LoginView`)

| Mục | Chi tiết |
|-----|----------|
| Mục đích | Đăng nhập email/displayName + password |
| Thành phần | 2 field, nút Login, link Register, checkbox "Nhớ phiên" |
| API | `POST /api/auth/login` |
| Luồng | Success → lưu token → `GET /api/auth/me` → MainShell |

### 3.2 Register (`RegisterView`)

| API | `POST /api/auth/register` |
| Ghi chú | Hiển thị lỗi 403 nếu registration disabled (settings public) |
| Admin bootstrap | Field ẩn/mở rộng: Admin secret (optional) |

### 3.3 Home (`HomeView`)

| Thành phần | Hero carousel (top 5 poster), grid phim, pagination |
| Continue | `GET /api/history/continue?limit=6` (nếu logged in) |
| API list | `GET /api/movies?page&limit=24` + filters |
| Thao tác | Click card → MovieDetail |

### 3.4 Browse / Search (`BrowseView` — có thể gộp Home)

| Thành phần | Search box, dropdown type/country/category |
| API | `/api/movies/filters`, `/api/movies/search` hoặc list có query |
| Filter | `FilterBar` component tái sử dụng |

### 3.5 Movie Detail (`MovieDetailView`)

| Thành phần | Poster, title, mô tả, series tabs, trailer link, VIP badge |
| API | `GET /api/movies/{slug}` |
| Comments/Ratings | Panel phụ, lazy load |
| Nút | "Xem phim" → WatchView nếu `canWatch`; else dialog đăng nhập/VIP |

### 3.6 Watch (`WatchView`)

| Thành phần | Combobox server, list tập, vùng player (pywebview) |
| API | Detail đã có episodes; `POST /api/history` debounce 1s |
| Resume | Query `episode`, `time` từ history |
| Guest block | Message + nút Login |

### 3.7 Watch History (`HistoryView`)

| API | GET/DELETE history |
| Thao tác | Xóa từng dòng, xóa tất cả, "Tiếp tục xem" |

### 3.8 Profile (`ProfileView`)

| API | GET/PUT `/api/auth/me` |
| Fields | displayName, email, phone, DOB, gender, đổi mật khẩu |

### 3.9 VIP (`VipView`) — Should-have

| API | `POST /api/payment/vnpay-create` → mở browser |
| Fallback | Hướng dẫn liên hệ admin nếu VNPay chưa cấu hình |

### 3.10 Admin Dashboard (`AdminDashboardView`)

| API | overview + charts |
| Widgets | Stat cards (CTk), biểu đồ đơn giản (matplotlib embedded hoặc bảng số) |

### 3.11 Admin Content — Movies (`AdminMoviesView`)

| Chức năng | List, import slug, toggle active/VIP view, sửa title/content |
| API | `/api/admin/movies`, `/api/movies/meta/phimapi-new` |
| UX | Dialog import, confirm delete |

### 3.12 Admin Categories (`AdminCategoriesView`)

| API | CRUD `/api/categories` |
| UX | Multi-select phim (search local list admin movies) |

### 3.13 Admin Users (`AdminUsersView`)

| API | admin users endpoints |
| UX | Ban, role combobox, reset password modal, VIP dates |

### 3.14 Admin Logs (`AdminLogsView`)

| API | `GET /api/admin/logs` |
| UX | Table + filter action |

### 3.15 Admin Settings (`AdminSettingsView`)

| API | GET/PUT settings |
| Fields | maintenance, registration, comments, site name |

## 4. Điều hướng & phân quyền

| Role | Menu hiển thị |
|------|----------------|
| Guest | Home, Browse, Login |
| User | + History, Profile, VIP |
| Admin | + Admin submenu (Dashboard, Movies, Categories, Users, Logs, Settings) |

Maintenance: `GET /api/settings/public` → nếu bật và không admin → màn hình Maintenance.

## 5. Xử lý trạng thái mạng

| Tình huống | GUI |
|------------|-----|
| Flask down | Status bar đỏ, retry button |
| 401 | Logout về Login |
| 503 maintenance | Dialog + quay lại |
| 502 phimapi | Thông báo trên Detail/Watch |

## 6. Wireframe logic (ASCII)

```text
+------------------+---------------------------+
| [Logo] PHIMHAY   |  Hero / Grid / Detail     |
| > Trang chủ      |                           |
| > Tìm kiếm       |                           |
| > Lịch sử        |                           |
| > VIP            |                           |
| > Admin *        |                           |
|                  |                           |
| [User menu]      |                           |
+------------------+---------------------------+
| API: OK | DB: OK                           |
+------------------+---------------------------+
```

## 7. Màn hình **không** triển khai (vì không có trong gốc)

- **Yêu thích** — chỉ khi bật FR-21 P2.
