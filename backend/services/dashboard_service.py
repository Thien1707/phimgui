from datetime import datetime, timedelta

from backend.models import ActivityLog, Movie, MovieView, User, WatchHistory


def overview() -> dict:
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "users": User.objects.count(),
        "movies": Movie.objects(is_active=True).count(),
        "moviesTotal": Movie.objects.count(),
        "viewsToday": MovieView.objects(created_at__gte=today_start).count(),
        "watchSessions": WatchHistory.objects.count(),
    }


def charts(days: int = 14) -> dict:
    days = min(30, max(1, days))
    since = datetime.utcnow() - timedelta(days=days)
    pipeline = [
        {"$match": {"created_at": {"$gte": since}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"},
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    rows = list(MovieView.objects.aggregate(pipeline))
    return {
        "viewsByDay": [{"date": r["_id"], "count": r["count"]} for r in rows],
        "recentLogs": ActivityLog.objects.order_by("-created_at").limit(10).count(),
    }
