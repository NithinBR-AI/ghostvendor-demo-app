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
    except Exception as exc:
        logging.warning("Stripe charge failed: %s", exc)
        return jsonify({"error": "vendor error", "message": str(exc)}), 503
    if isinstance(result, dict) and "error" in result:
        logging.warning("Stripe returned error: %s", result)
        return jsonify({"error": "vendor error", "message": result.get("message", "unknown")}), 503
    return jsonify({"payment_intent_id": result["id"], "status": result["status"]})
