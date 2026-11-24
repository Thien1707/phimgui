"""Đồng bộ danh mục phim từ MongoDB desktop sang SQLAlchemy web."""

import re
import threading
import time
from datetime import datetime

from mongoengine import connect, disconnect
from mongoengine.connection import get_db

from app import db
from app.models import Movie

_MONGO_ALIAS = "web_catalog_sync"
_SYNC_INTERVAL_SECONDS = 5
_last_sync = 0.0
_sync_lock = threading.Lock()
_mongo_lock = threading.RLock()


def _open_shared_db():
    # Import config here so python-dotenv loads the existing project .env.
    from backend.config import Config

    _mongo_lock.acquire()
    try:
        connect(
            db=Config.MONGODB_DB_NAME,
            host=Config.MONGODB_URI,
            alias=_MONGO_ALIAS,
            serverSelectionTimeoutMS=3000,
        )
        return get_db(alias=_MONGO_ALIAS)
    except Exception:
        _mongo_lock.release()
        raise


def _close_shared_db():
    try:
        disconnect(alias=_MONGO_ALIAS)
    finally:
        _mongo_lock.release()


def sync_desktop_movies():
    """Đồng bộ toàn bộ catalog MongoDB sang SQLAlchemy web theo slug."""
    source = _open_shared_db()
    try:
        category_names = {
            str(row["_id"]): row.get("display_name") or row.get("name", "")
            for row in source["categories"].find({}, {"name": 1, "display_name": 1})
        }
        created = 0
        updated = 0
        source_movies = list(source["movies"].find({}))
        source_slugs = set()
        for row in source_movies:
            slug = (row.get("slug") or "").strip()
            title = (row.get("title") or "").strip()
            if not slug or not title:
                continue
            source_slugs.add(slug)

            movie = Movie.query.filter_by(slug=slug).first()
            if movie is None:
                movie = Movie(slug=slug, title=title)
                db.session.add(movie)
                created += 1
            else:
                updated += 1

            movie.title = title[:255]
            movie.origin_name = (row.get("origin_name") or "")[:255]
            movie.description = row.get("content") or ""
            movie.poster_url = row.get("poster_url") or row.get("thumb_url") or ""
            movie.year = row.get("year") if isinstance(row.get("year"), int) else None
            category_ids = row.get("category_ids") or []
            movie.category = ", ".join(
                filter(None, (category_names.get(str(cid), "") for cid in category_ids))
            )
            movie.is_vip = row.get("view_status", 0) == 1
            movie.is_active = row.get("is_active", True) is not False

        # The desktop admin currently deletes Mongo documents physically.
        # Hide the SQL projection when a slug has disappeared from the source.
        for movie in Movie.query.all():
            if movie.slug not in source_slugs:
                movie.is_active = False

        db.session.commit()
        return created, updated
    except Exception:
        db.session.rollback()
        raise
    finally:
        _close_shared_db()


def sync_desktop_movies_if_due():
    """Refresh the web catalog at most once per interval per process."""
    global _last_sync
    if time.monotonic() - _last_sync < _SYNC_INTERVAL_SECONDS:
        return
    with _sync_lock:
        if time.monotonic() - _last_sync < _SYNC_INTERVAL_SECONDS:
            return
        sync_desktop_movies()
        _last_sync = time.monotonic()


def save_web_movie_to_desktop(movie, api_data=None):
    """Write editable web movie fields to the shared desktop Mongo catalog."""
    source = _open_shared_db()
    try:
        category_ids = []
        for label in filter(None, (part.strip() for part in (movie.category or "").split(","))):
            category = source["categories"].find_one({"display_name": label})
            if category is None:
                name = re.sub(r"\s+", "-", label.lower())[:100] or "the-loai"
                category = source["categories"].find_one({"name": name})
            if category is None:
                name = re.sub(r"\s+", "-", label.lower())[:100] or "the-loai"
                result = source["categories"].insert_one({"name": name, "display_name": label})
                category_ids.append(result.inserted_id)
            else:
                category_ids.append(category["_id"])

        values = {
            "slug": movie.slug,
            "title": movie.title,
            "origin_name": movie.origin_name or "",
            "content": movie.description or "",
            "poster_url": movie.poster_url or "",
            "year": movie.year,
            "category_ids": category_ids,
            "view_status": 1 if movie.is_vip else 0,
            "is_active": movie.is_active,
            "updated_at": datetime.utcnow(),
        }
        if api_data:
            values.update({
                "type": api_data.get("type") or "",
                "thumb_url": api_data.get("thumb_url") or movie.poster_url or "",
                "external_id": str(api_data.get("_id") or ""),
                "country": ", ".join(
                    country.get("name", "")
                    for country in (api_data.get("country") or [])
                    if isinstance(country, dict)
                ),
            })
        insert_defaults = {
            "thumb_url": movie.poster_url or "",
            "type": "",
            "country": "",
            "view_count": 0,
            "comment_rating_policy": "public",
            "created_at": datetime.utcnow(),
        }
        for key in values:
            insert_defaults.pop(key, None)
        source["movies"].update_one(
            {"slug": movie.slug},
            {
                "$set": values,
                "$setOnInsert": insert_defaults,
            },
            upsert=True,
        )
    finally:
        _close_shared_db()

    global _last_sync
    _last_sync = 0.0


def deactivate_shared_movie(slug):
    """Soft-delete a movie in SQL and the shared Mongo catalog."""
    source = _open_shared_db()
    try:
        source["movies"].update_one({"slug": slug}, {"$set": {"is_active": False}})
    finally:
        _close_shared_db()
    global _last_sync
    _last_sync = 0.0
