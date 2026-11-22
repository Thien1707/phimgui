from datetime import datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    ObjectIdField,
    StringField,
)

VIEW_NORMAL = 0
VIEW_VIP = 1


class Movie(Document):
    meta = {
        "collection": "movies",
        "indexes": ["slug", "is_active", "category_ids", "series_id"],
    }

    slug = StringField(required=True, unique=True, max_length=255)
    title = StringField(required=True, max_length=512)
    origin_name = StringField(max_length=512, default="")
    poster_url = StringField(default="")
    thumb_url = StringField(default="")
    year = IntField(null=True)
    type = StringField(max_length=64, default="")
    content = StringField(default="")
    country = StringField(max_length=255, default="")
    series_id = ObjectIdField(null=True)
    part_number = IntField(null=True)
    view_status = IntField(default=VIEW_NORMAL)
    comment_rating_policy = StringField(
        max_length=32, choices=("public", "members"), default="public"
    )
    is_active = BooleanField(default=True)
    external_id = StringField(max_length=64, default="")
    view_count = IntField(default=0)
    category_ids = ListField(ObjectIdField(), default=list)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)


class Category(Document):
    meta = {
        "collection": "categories",
        "indexes": [{"fields": ["name"], "unique": True}],
    }

    name = StringField(required=True, unique=True, max_length=100)
    display_name = StringField(max_length=150, default="")
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
