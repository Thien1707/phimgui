from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from mongoengine import connect

limiter = Limiter(key_func=get_remote_address, default_limits=["200 per minute"])


def init_mongo(app: Flask) -> None:
    connect(
        db=app.config["MONGODB_DB_NAME"],
        host=app.config["MONGODB_URI"],
        alias="default",
    )
