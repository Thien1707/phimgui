import json
import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")
TOKEN_PATH = _ROOT / ".token"

_client: httpx.Client | None = None


def api_base() -> str:
    return os.environ.get("API_BASE_URL", "http://127.0.0.1:5000").rstrip("/")


def _get_client() -> httpx.Client:
    global _client
    if _client is None:
        _client = httpx.Client(
            timeout=httpx.Timeout(12.0, connect=3.0),
            follow_redirects=True,
            limits=httpx.Limits(max_connections=8, max_keepalive_connections=4),
        )
    return _client


def wait_for_backend(max_wait_sec: float = 12.0) -> bool:
    """Đợi Flask sẵn sàng (dùng khi khởi động run_desktop)."""
    import time

    url = f"{api_base()}/api/health"
    deadline = time.time() + max_wait_sec
    while time.time() < deadline:
        try:
            r = _get_client().get(url)
            if r.status_code == 200 and r.json().get("ok"):
                return True
        except httpx.HTTPError:
            pass
        time.sleep(0.35)
    return False


def get_token() -> str | None:
    if TOKEN_PATH.exists():
        return TOKEN_PATH.read_text(encoding="utf-8").strip() or None
    return None


def set_token(token: str | None) -> None:
    if token:
        TOKEN_PATH.write_text(token, encoding="utf-8")
    elif TOKEN_PATH.exists():
        TOKEN_PATH.unlink()


class ApiError(Exception):
    pass


def api(
    method: str,
    path: str,
    *,
    json_body: dict | None = None,
    token: str | None = None,
    params: dict | None = None,
    timeout: float | None = None,
) -> Any:
    headers = {"Accept": "application/json"}
    t = token if token is not None else get_token()
    if t:
        headers["Authorization"] = f"Bearer {t}"
    url = f"{api_base()}{path}"
    try:
        client = _get_client()
        if timeout is not None:
            r = client.request(
                method, url, headers=headers, json=json_body, params=params, timeout=timeout
            )
        else:
            r = client.request(method, url, headers=headers, json=json_body, params=params)
    except httpx.ConnectError as e:
        raise ApiError("Không kết nối backend. Chạy lại run_desktop.py hoặc đợi vài giây.") from e
    except httpx.TimeoutException as e:
        raise ApiError("API quá chậm — kiểm tra mạng hoặc phimapi.") from e
    text = r.text
    data: Any = {}
    if text:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = {"error": text}
    if r.status_code >= 400:
        raise ApiError(data.get("error") or r.reason_phrase or "Lỗi API")
    return data
