"""Call the project's existing REST blueprints from server-rendered web views."""

from functools import wraps

from flask import abort, current_app, flash, g, redirect, request, session, url_for


class BackendAPIError(Exception):
    def __init__(self, message, status=500):
        super().__init__(message)
        self.status = status


def api_call(method, path, *, data=None, headers=None):
    request_headers = {"Accept": "application/json"}
    token = session.get("phimhay_token")
    if token:
        request_headers["Authorization"] = f"Bearer {token}"
    if headers:
        request_headers.update(headers)
    try:
        with current_app.test_client() as client:
            response = client.open(path, method=method, json=data, headers=request_headers)
    except Exception as exc:
        raise BackendAPIError("Không gọi được API nội bộ Flask.", 503) from exc
    payload = response.get_json(silent=True) or {}
    if response.status_code >= 400:
        raise BackendAPIError(payload.get("error") or "Yêu cầu không thành công.", response.status_code)
    return payload


def web_user():
    if getattr(g, "web_user_loaded", False):
        return getattr(g, "web_user", None)
    g.web_user_loaded = True
    if not session.get("phimhay_token"):
        g.web_user = None
        return None
    try:
        g.web_user = api_call("GET", "/api/auth/me")
    except BackendAPIError:
        session.pop("phimhay_token", None)
        g.web_user = None
    return g.web_user


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not web_user():
            flash("Vui lòng đăng nhập để tiếp tục.", "error")
            return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = web_user()
        if not user:
            flash("Vui lòng đăng nhập bằng tài khoản quản trị.", "error")
            return redirect(url_for("auth.login"))
        if not user.get("isAdmin") and user.get("role") != "admin":
            abort(403)
        return view(*args, **kwargs)

    return wrapped
