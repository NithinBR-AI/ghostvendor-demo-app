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
        return jsonify({"error": "vendor error", "message": str(exc)}), 503
    if isinstance(result, dict) and "error" in result:
        error_type = result["error"]
        if error_type == "timeout":
            logger.warning("Stripe charge timed out")
            return jsonify({"error": "timeout", "message": result.get("message", "Stripe request timed out")}), 408
        elif error_type == "retry_failed":
            logger.warning("Stripe charge retry failed: %s", result.get("message"))
            return jsonify({"error": "retry_failed", "message": result.get("message", "Stripe retry failed")}), 502
        elif error_type == "parse_error":
            logger.warning("Stripe charge parse error: %s", result.get("message"))
            return jsonify({"error": "parse_error", "message": result.get("message", "Failed to parse Stripe response")}), 502
        else:
            logger.warning("Stripe charge vendor error: %s", result.get("message"))
            return jsonify({"error": "vendor error", "message": result.get("message", "Stripe error")}), 503
    try:
        payment_intent_id = result["id"]
        status = result["status"]
    except (KeyError, TypeError) as exc:
        logger.warning("Stripe charge unexpected response format: %s", exc)
        return jsonify({"error": "vendor error", "message": "Unexpected Stripe response format"}), 502
    return jsonify({"payment_intent_id": payment_intent_id, "status": status})
