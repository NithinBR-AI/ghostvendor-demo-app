"""POST /charge — process a payment via Stripe."""

from flask import Blueprint, request, jsonify
from app.clients import stripe
import logging

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
        logging.warning("Stripe charge failed with exception: %s", e)
        return jsonify({"error": "vendor_error", "message": "Stripe request failed"}), 503
    if isinstance(result, dict) and "error" in result:
        logging.warning("Stripe charge returned error: %s", result.get("message"))
        return jsonify(result), 503
    if not isinstance(result, dict) or "id" not in result or "status" not in result:
        logging.warning("Stripe charge returned unexpected response: %s", result)
        return jsonify({"error": "vendor_error", "message": "Unexpected Stripe response"}), 503
    return jsonify({"payment_intent_id": result["id"], "status": result["status"]})
