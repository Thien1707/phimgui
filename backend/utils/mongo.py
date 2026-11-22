from bson import ObjectId
from bson.errors import InvalidId


def parse_object_id(value) -> ObjectId | None:
    if value is None:
        return None
    if isinstance(value, ObjectId):
        return value
    try:
        s = str(value).strip()
        if not s:
            return None
        return ObjectId(s)
    except (InvalidId, TypeError, ValueError):
        return None
