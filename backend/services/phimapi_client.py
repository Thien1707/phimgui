import time

import httpx
from flask import current_app

_cache: dict[str, tuple[float, dict]] = {}
_CACHE_TTL_SEC = 300


class PhimApiError(Exception):
    def __init__(self, message: str, status: int = 502):
        super().__init__(message)
        self.status = status


def _client() -> httpx.Client:
    base = current_app.config["PHIMAPI_BASE"]
    return httpx.Client(base_url=base, timeout=25.0, headers={"Accept": "application/json"})


def fetch_movie_by_slug(slug: str) -> dict:
    now = time.time()
    hit = _cache.get(slug)
    if hit and now - hit[0] < _CACHE_TTL_SEC:
        return hit[1]
    with _client() as client:
        r = client.get(f"/phim/{slug}")
        if r.status_code >= 400:
            raise PhimApiError("Không lấy được dữ liệu phimapi", 502)
        data = r.json()
    if not data or not data.get("status") or not data.get("movie"):
        msg = data.get("msg") if isinstance(data, dict) else "Phim không tồn tại trên phimapi"
        raise PhimApiError(msg or "Phim không tồn tại trên phimapi", 404)
    _cache[slug] = (time.time(), data)
    return data


def fetch_new_movies(page: int = 1) -> dict:
    with _client() as client:
        r = client.get("/danh-sach/phim-moi-cap-nhat", params={"page": page})
        r.raise_for_status()
        return r.json()
