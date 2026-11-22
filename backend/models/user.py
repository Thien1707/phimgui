from datetime import datetime

from mongoengine import BooleanField, DateField, DateTimeField, Document, StringField


class User(Document):
    meta = {
        "collection": "users",
        "indexes": [
            {"fields": ["email"], "unique": True},
            {"fields": ["display_name"], "unique": True},
        ],
    }

    email = StringField(required=True, max_length=255)
    password_hash = StringField(required=True, max_length=255)
    display_name = StringField(required=True, max_length=100)
    phone_number = StringField(max_length=32, default="")
    date_of_birth = DateField(null=True)
    gender = StringField(max_length=32, default="")
    role = StringField(max_length=32, choices=("user", "moderator", "admin"), default="user")
    is_vip = BooleanField(default=False)
    vip_expires_at = DateTimeField(null=True)
    is_unlimited_vip = BooleanField(default=False)
    banned = BooleanField(default=False)
    last_login = DateTimeField(null=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)

    def is_vip_active(self) -> bool:
        if not self.is_vip:
            return False
        if self.is_unlimited_vip:
            return True
        if not self.vip_expires_at:
            return True
        return self.vip_expires_at.replace(tzinfo=None) > datetime.utcnow()

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
