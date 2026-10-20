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
        logger.warning("Stripe charge failed with exception: %s", exc)
        return jsonify({"error": "vendor_error", "message": "Stripe request failed"}), 502
    if isinstance(result, dict) and "error" in result:
        error_type = result.get("error", "vendor_error")
        if error_type == "timeout":
            logger.warning("Stripe charge timed out")
            return jsonify(result), 504
        elif error_type == "vendor_error":
            logger.warning("Stripe returned vendor error: %s", result.get("message"))
            return jsonify(result), 502
        elif error_type == "parse_error":
            logger.warning("Stripe response parse error")
            return jsonify(result), 502
        else:
            logger.warning("Stripe returned error: %s", result)
            return jsonify(result), 502
    try:
        return jsonify({"payment_intent_id": result["id"], "status": result["status"]})
    except (KeyError, TypeError) as exc:
        logger.warning("Stripe response missing expected fields: %s", exc)
        return jsonify({"error": "vendor_error", "message": "Invalid response from Stripe"}), 502
