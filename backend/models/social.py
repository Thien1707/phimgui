from datetime import datetime

from mongoengine import DateTimeField, Document, IntField, ObjectIdField, StringField


class Comment(Document):
    meta = {
        "collection": "comments",
        "indexes": ["movie_id", ("movie_id", "-created_at")],
    }

    movie_id = ObjectIdField(required=True)
    user_id = ObjectIdField(required=True)
    body = StringField(required=True, max_length=2000)
    created_at = DateTimeField(default=datetime.utcnow)


class Rating(Document):
    meta = {
        "collection": "ratings",
        "indexes": [
            {
                "fields": ["movie_id", "user_id"],
                "unique": True,
            },
        ],
    }

    movie_id = ObjectIdField(required=True)
    user_id = ObjectIdField(required=True)
    stars = IntField(required=True, min_value=1, max_value=5)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
