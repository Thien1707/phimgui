from datetime import datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    Document,
    ListField,
    ObjectIdField,
    StringField,
)


class ActivityLog(Document):
    meta = {
        "collection": "activity_logs",
        "indexes": ["action", "-created_at"],
    }

    actor_id = ObjectIdField(null=True)
    actor_role = StringField(max_length=32, default="guest")
    action = StringField(required=True, max_length=64)
    target_type = StringField(max_length=32, default="")
    target_id = StringField(max_length=64, default="")
    metadata_json = DictField(default=dict)
    ip_address = StringField(max_length=45, default="")
    created_at = DateTimeField(default=datetime.utcnow)


class SystemSettings(Document):
    meta = {
        "collection": "system_settings",
        "indexes": [{"fields": ["setting_key"], "unique": True}],
    }

    setting_key = StringField(required=True, unique=True, max_length=32, default="global")
    site_name = StringField(max_length=128, default="PHIMHAY")
    logo = StringField(default="")
    banner_images = ListField(default=list)
    maintenance_mode = BooleanField(default=False)
    registration_enabled = BooleanField(default=True)
    comments_enabled = BooleanField(default=True)
    email_config = DictField(null=True)
    third_party_api_keys = DictField(null=True)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
