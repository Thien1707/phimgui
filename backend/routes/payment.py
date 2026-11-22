import secrets
from datetime import datetime, timedelta

from flask import Blueprint, g, jsonify, request

from backend.config import Config
from backend.middleware.auth import require_auth
from backend.models import Payment, User

bp = Blueprint("payment", __name__, url_prefix="/api/payment")


@bp.post("/vnpay-create")
@require_auth
def vnpay_create():
    if not Config.VNP_TMN_CODE or not Config.VNP_HASH_SECRET:
        return jsonify(
            {
                "error": "VNPay chưa cấu hình. Admin có thể gán VIP trong Quản trị → Users.",
            }
        ), 503
    txn_ref = f"VIP{g.user.id}{secrets.token_hex(4).upper()}"
    amount = Config.VNP_VIP_AMOUNT
    pay = Payment(user_id=g.user.id, txn_ref=txn_ref, amount=amount, status="pending")
    pay.save()
    pay_url = f"{Config.VNP_URL}?vnp_TxnRef={txn_ref}&vnp_Amount={amount * 100}"
    return jsonify({"payUrl": pay_url, "txnRef": txn_ref})


@bp.get("/status/<txn_ref>")
@require_auth
def payment_status(txn_ref: str):
    pay = Payment.objects(txn_ref=txn_ref, user_id=g.user.id).first()
    if not pay:
        return jsonify({"error": "Không tìm thấy giao dịch"}), 404
    return jsonify(
        {
            "txnRef": pay.txn_ref,
            "status": pay.status,
            "amount": pay.amount,
            "updatedAt": pay.updated_at.isoformat() if pay.updated_at else None,
        }
    )


@bp.get("/vnpay-return")
def vnpay_return():
    txn = request.args.get("vnp_TxnRef", "")
    pay = Payment.objects(txn_ref=txn).first()
    if pay:
        pay.status = "success"
        pay.vnp_response = dict(request.args)
        pay.updated_at = datetime.utcnow()
        user = User.objects(id=pay.user_id).first()
        if user:
            user.is_vip = True
            user.vip_expires_at = datetime.utcnow() + timedelta(days=Config.VIP_DURATION_DAYS)
            user.save()
        pay.save()
    return jsonify({"message": "Thanh toán đã ghi nhận (sandbox). Bạn có thể đóng tab."})
