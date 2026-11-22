from flask import Request

from backend.models import ActivityLog, User


def client_ip(req: Request) -> str:
    x = req.headers.get("X-Forwarded-For", "")
    if x:
        return x.split(",")[0].strip()
    return req.remote_addr or "127.0.0.1"


def log_activity(
    req: Request,
    *,
    action: str,
    target_type: str = "",
    target_id: str = "",
    metadata: dict | None = None,
    user: User | None = None,
) -> None:
    actor = user or getattr(req, "user", None)
    role = "guest"
    actor_id = None
    if actor:
        role = actor.role or ("admin" if actor.is_admin else "user")
        actor_id = actor.id
    entry = ActivityLog(
        actor_id=actor_id,
        actor_role=role,
        action=action,
        target_type=target_type,
        target_id=str(target_id) if target_id else "",
        metadata_json=metadata or {},
        ip_address=client_ip(req),
    )
    entry.save()
