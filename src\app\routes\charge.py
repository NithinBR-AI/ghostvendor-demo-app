"""POST /charge \u2014 process a payment via Stripe."""

from flask import Blueprint, request, jsonify
import logging
from app.clients import stripe

charge_bp = Blueprint("charge", __name__)
logger = logging.getLogger(__name__)


@charge_bp.route("/charge", methods=["POST"])
def charge():
    data = request.json
    if data is None or not isinstance(data, dict):
        return jsonify({"error": "invalid request body"}), 400
    amount = data.get("amount")
    payment_method = data.get("payment_method")
    if amount is None or payment_method is None or not str(payment_method).strip():
        return jsonify({"error": "amount and payment_method are required"}), 400
    try:
        result = stripe.create_payment_intent(
            amount=amount,
            currency=data.get("currency", "usd"),
            payment_method=payment_method,
        )
    except Exception:
        logger.warning("Stripe charge failed with exception", exc_info=True)
        return jsonify({"error": "vendor error"}), 503
    if not isinstance(result, dict) or "error" in result or result.get("status_code", 200) >= 400:
        logger.warning("Stripe charge failed: %s", result)
        return jsonify({"error": "vendor error"}), 503
    return jsonify({"payment_intent_id": result.get("id"), "status": result.get("status")})
