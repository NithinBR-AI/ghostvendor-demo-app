"""POST /charge — process a payment via Stripe."""

import logging

from flask import Blueprint, request, jsonify
from app.clients import stripe

charge_bp = Blueprint("charge", __name__)


@charge_bp.route("/charge", methods=["POST"])
def charge():
    """
    Process a payment intent via Stripe.

    Request JSON:
        amount (int): Amount in cents.
        currency (str, optional): ISO 4217 code. Defaults to "usd".
        payment_method (str): Stripe PaymentMethod ID.

    Returns:
        JSON with payment_intent_id and status on success.
        No error handling — any Stripe failure propagates as an unhandled exception.
    """
    data = request.json
    try:
        result = stripe.create_payment_intent(
            amount=data["amount"],
            currency=data.get("currency", "usd"),
            payment_method=data["payment_method"],
        )
    except Exception as e:
        logging.warning("Stripe client raised exception: %s", e)
        return jsonify({"error": "vendor error", "message": str(e)}), 502
    if isinstance(result, dict) and "error" in result:
        error_type = result.get("error", "")
        if error_type == "timeout":
            logging.warning("Stripe timeout")
            return jsonify(result), 504
        elif error_type == "transient_failure":
            logging.warning("Stripe transient failure: %s", result.get("message"))
            return jsonify(result), 503
        else:
            logging.warning("Stripe error: %s", result.get("message"))
            return jsonify(result), 502
    if not isinstance(result, dict) or "id" not in result or "status" not in result:
        logging.warning("Stripe returned malformed response: %s", result)
        return jsonify({"error": "vendor error", "message": "malformed response"}), 502
    return jsonify({"payment_intent_id": result["id"], "status": result["status"]})
