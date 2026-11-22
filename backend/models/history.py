from datetime import datetime

from mongoengine import DateTimeField, DictField, Document, IntField, ObjectIdField, StringField


class WatchHistory(Document):
    meta = {
        "collection": "watch_history",
        "indexes": [
            {
                "fields": ["user_id", "movie_id", "episode"],
                "unique": True,
            },
            ("user_id", "-updated_at"),
        ],
    }

    user_id = ObjectIdField(required=True)
    movie_id = ObjectIdField(required=True)
    episode = IntField(default=1)
    current_time_sec = IntField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)


class MovieView(Document):
    meta = {
        "collection": "movie_views",
        "indexes": ["movie_id", "created_at"],
    }

    user_id = ObjectIdField(null=True)
    movie_id = ObjectIdField(required=True)
    ip_address = StringField(max_length=45, default="")
    created_at = DateTimeField(default=datetime.utcnow)


class Payment(Document):
    meta = {
        "collection": "payments",
        "indexes": [{"fields": ["txn_ref"], "unique": True}, "user_id"],
    }

    user_id = ObjectIdField(required=True)
    txn_ref = StringField(required=True, unique=True, max_length=64)
    amount = IntField(required=True)
    status = StringField(
        max_length=32, choices=("pending", "success", "failed"), default="pending"
    )
    vnp_response = DictField(null=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
