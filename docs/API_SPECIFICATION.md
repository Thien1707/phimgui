# API_SPECIFICATION.md — Flask API dự kiến

Base URL: `http://127.0.0.1:5000`  
Format: JSON, UTF-8  
Auth: `Authorization: Bearer <jwt>` (trừ endpoint public)

## 1. Health & Settings

| Method | Path | Auth | Mô tả |
|--------|------|------|--------|
| GET | `/api/health` | No | `{ ok, db: true }` |
| GET | `/api/settings/public` | No | siteName, maintenance, registration, comments |

## 2. Auth

| Method | Path | Auth | Body / Response |
|--------|------|------|-----------------|
| POST | `/api/auth/register` | No | `{ email, password, displayName }` → `{ token, user }` |
| POST | `/api/auth/login` | No | `{ identifier, password }` → `{ token, user }` |
| GET | `/api/auth/me` | Yes | User profile |
| PUT | `/api/auth/me` | Yes | Update profile, optional password |

**Headers đặc biệt:** `x-admin-secret` khi register (bootstrap admin).

**Errors:** 400 validation, 401 auth, 403 banned/registration closed, 409 duplicate.

## 3. Movies (public + user)

| Method | Path | Auth | Ghi chú |
|--------|------|------|---------|
| GET | `/api/movies` | Optional | Query: `page`, `limit`, `type`, `country`, `category` |
| GET | `/api/movies/search` | Optional | Query: `q`, `page`, `limit` |
| GET | `/api/movies/filters` | No | `{ types, countries }` |
| GET | `/api/movies/meta/phimapi-new` | Admin* | Gợi ý import (có thể admin-only) |
| GET | `/api/movies/{slug}` | Optional | Detail + episodes nếu `canWatch` |
| GET | `/api/movies/{id}/series` | No | Parts cùng series |
| PUT | `/api/movies/{id}/categories` | Admin | `{ categoryIds: [] }` |
| POST | `/api/movies/{id}/assign-series` | Admin | `{ movieIds: [] }` |

**Response detail (rút gọn):**

```json
{
  "movie": {
    "id": 1,
    "slug": "...",
    "title": "...",
    "canWatch": true,
    "accessReason": "normal",
    "viewStatus": 0,
    "series": [],
    "episodes": []
  }
}
```

## 4. Categories

| Method | Path | Auth |
|--------|------|------|
| GET | `/api/categories` | No |
| POST | `/api/categories` | Admin |
| PUT | `/api/categories/{id}` | Admin |
| DELETE | `/api/categories/{id}` | Admin |

## 5. Comments

| Method | Path | Auth |
|--------|------|------|
| GET | `/api/comments/movie/{movieId}` | Optional |
| POST | `/api/comments/movie/{movieId}` | Yes `{ body }` |
| DELETE | `/api/comments/{id}` | Yes (owner/admin) |

## 6. Ratings

| Method | Path | Auth |
|--------|------|------|
| GET | `/api/ratings/movie/{movieId}` | Optional |
| POST | `/api/ratings/movie/{movieId}` | Yes `{ stars: 1-5 }` |

## 7. Watch history

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/history` | Yes `{ movieId, episode, currentTime }` |
| GET | `/api/history` | Yes | Full list (limit 50) |
| GET | `/api/history/continue` | Yes | Query `limit` |
| DELETE | `/api/history/{historyId}` | Yes |
| DELETE | `/api/history` | Yes | Clear all |

## 8. Payment (Should-have)

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/payment/vnpay-create` | Yes → `{ payUrl, txnRef }` |
| GET | `/api/payment/vnpay-return` | No | VNPay callback (browser) |
| GET | `/api/payment/status/{txnRef}` | Yes | **Mới** — GUI poll trạng thái |

## 9. Admin (`/api/admin/*`, require admin)

### Users

| Method | Path |
|--------|------|
| GET | `/api/admin/users` | Query: page, search |
| GET | `/api/admin/users/{id}` |
| PATCH | `/api/admin/users/{id}/ban` |
| PATCH | `/api/admin/users/{id}/unban` |
| DELETE | `/api/admin/users/{id}` |
| POST | `/api/admin/users/{id}/reset-password` |
| PATCH | `/api/admin/users/{id}/role` |
| PATCH | `/api/admin/users/{id}/vip` |

### Movies

| Method | Path |
|--------|------|
| GET | `/api/admin/movies` |
| POST | `/api/admin/movies/import` `{ slug }` |
| PATCH | `/api/admin/movies/{id}` |
| DELETE | `/api/admin/movies/{id}` |

### Dashboard

| GET | `/api/admin/dashboard/overview` |
| GET | `/api/admin/dashboard/charts?days=14` |

### Logs & Settings

| GET | `/api/admin/logs` |
| GET | `/api/admin/settings` |
| PUT | `/api/admin/settings` |

## 10. Mã lỗi chuẩn

```json
{ "error": "Mô tả lỗi tiếng Việt" }
```

| HTTP | Ý nghĩa |
|------|---------|
| 503 | Maintenance mode |
| 502 | phimapi upstream fail |

## 11. Compatibility với PHIMHAY gốc

Contract cố ý **giữ path và payload tương thích** để port logic GUI từ `client.ts` sang Python client dễ dàng. Khác biệt:

- `id` là số thay vì Mongo ObjectId string (GUI hiển thị string hóa).
- Admin list movies có thể trả `id` thay `_id` (adapter layer trong GUI).
