from backend.models import Movie, User
from backend.models.movie import VIEW_VIP


def playback_access(user: User | None, movie: Movie) -> dict:
    if not user:
        return {"canWatch": False, "reason": "guest"}
    if user.is_admin:
        return {"canWatch": True, "reason": "admin"}
    if movie.view_status == VIEW_VIP and not user.is_vip_active():
        return {"canWatch": False, "reason": "vip_only"}
    reason = "vip" if user.is_vip_active() else "normal"
    return {"canWatch": True, "reason": reason}
