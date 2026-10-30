"""POST /charge \u2014 process a payment via Stripe."""

import logging

from flask import Blueprint, request, jsonify
from app.clients import stripe

charge_bp = Blueprint("charge", __name__)


@charge_bp.route("/charge", methods=["POST"])
def charge():
    data = request.json
    if not data or not data.get("amount") or not data.get("payment_method"):
        return jsonify({"error": "missing required fields"}), 400
    try:
        result = stripe.create_payment_intent(
            amount=data["amount"],
            currency=data.get("currency", "usd"),
            payment_method=data["payment_method"],
        )
    except Exception:
        logging.getLogger(__name__).warning("Stripe charge failed", exc_info=True)
        return jsonify({"error": "vendor error"}), 503
    if not isinstance(result, dict) or "error" in result or result.get("status_code", 200) >= 400:
        logging.getLogger(__name__).warning("Stripe charge failed: %s", result)
        return jsonify({"error": "vendor error"}), 503
    return jsonify({"payment_intent_id": result.get("id"), "status": result.get("status")})
