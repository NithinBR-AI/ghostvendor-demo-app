"""POST /charge — process a payment via Stripe."""

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
    if not isinstance(data, dict):
        return jsonify({"error": "invalid_input", "message": "Request body must be a JSON object"}), 400
    if "amount" not in data or not isinstance(data["amount"], int) or data["amount"] <= 0:
        return jsonify({"error": "invalid_input", "message": "amount must be a positive integer"}), 400
    if "payment_method" not in data or not isinstance(data["payment_method"], str) or not data["payment_method"].strip():
        return jsonify({"error": "invalid_input", "message": "payment_method must be a non-empty string"}), 400
    result = stripe.create_payment_intent(
        amount=data["amount"],
        currency=data.get("currency", "usd"),
        payment_method=data["payment_method"],
    )
    if isinstance(result, dict) and "error" in result:
        return jsonify(result), 503
    return jsonify({"payment_intent_id": result["id"], "status": result["status"]})
