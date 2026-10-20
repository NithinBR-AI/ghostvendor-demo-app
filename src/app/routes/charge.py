"""POST /charge — process a payment via Stripe."""

import logging

from flask import Blueprint, request, jsonify
from app.clients import stripe

charge_bp = Blueprint("charge", __name__)
logger = logging.getLogger(__name__)


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
    except Exception as exc:
        logger.warning("Stripe charge failed: %s", exc)
        return jsonify({"error": "vendor_error", "message": "Stripe request failed"}), 502
    if isinstance(result, dict) and "error" in result:
        error_type = result.get("error", "unknown")
        logger.warning("Stripe returned error: %s", error_type)
        if error_type == "timeout":
            return jsonify(result), 504
        elif error_type == "transient_failure":
            return jsonify(result), 502
        else:
            return jsonify(result), 502
    try:
        return jsonify({"payment_intent_id": result["id"], "status": result["status"]})
    except (KeyError, TypeError) as exc:
        logger.warning("Malformed Stripe response: %s", exc)
        return jsonify({"error": "malformed_response", "message": "Stripe response missing expected fields"}), 502
