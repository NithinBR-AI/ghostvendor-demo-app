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
    try:
        result = stripe.create_payment_intent(
            amount=data["amount"],
            currency=data.get("currency", "usd"),
            payment_method=data["payment_method"],
        )
    except Exception as e:
        return jsonify({"error": "vendor_exception", "message": str(e)}), 503
    if isinstance(result, dict) and "error" in result:
        if result["error"] == "timeout":
            return jsonify(result), 504
        elif result["error"] == "retry_failed":
            return jsonify(result), 502
        elif result["error"] == "invalid_json":
            return jsonify(result), 502
        else:
            return jsonify(result), 503
    if not isinstance(result, dict) or "id" not in result or "status" not in result:
        return jsonify({"error": "invalid_response", "message": "Unexpected response from Stripe"}), 502
    return jsonify({"payment_intent_id": result["id"], "status": result["status"]})
