import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")


def _default_mongodb_db_name() -> str:
    uri = os.environ.get("MONGODB_URI", "")
    if uri:
        path = urlparse(uri).path.strip("/")
        if path:
            return path.split("/")[0]
    return "phimhay_gui"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    JWT_SECRET = os.environ.get("JWT_SECRET", SECRET_KEY)
    MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://127.0.0.1:27017/phimhay_gui")
    MONGODB_DB_NAME = os.environ.get("MONGODB_DB_NAME") or _default_mongodb_db_name()
    PHIMAPI_BASE = os.environ.get("PHIMAPI_BASE", "https://phimapi.com").rstrip("/")
    INITIAL_ADMIN_SECRET = os.environ.get("INITIAL_ADMIN_SECRET", "")
    PORT = int(os.environ.get("PORT", "5000"))
    VIP_DURATION_DAYS = int(os.environ.get("VIP_DURATION_DAYS", "30"))
    VNP_TMN_CODE = os.environ.get("VNP_TMN_CODE", "")
    VNP_HASH_SECRET = os.environ.get("VNP_HASH_SECRET", "")
    VNP_URL = os.environ.get("VNP_URL", "https://sandbox.vnpayment.vn/paymentv2/vpcpay.html")
    VNP_VIP_AMOUNT = int(os.environ.get("VNP_VIP_AMOUNT", "100000"))
