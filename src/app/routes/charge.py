"""POST /charge — process a payment via Stripe."""

from flask import Blueprint, request, jsonify
from app.clients import stripe

charge_bp = Blueprint("charge", __name__)


@charge_bp.route("/charge", methods=["POST"])
def charge():
    data = request.json
    result = stripe.create_payment_intent(
        amount=data["amount"],
        currency=data.get("currency", "usd"),
        payment_method=data["payment_method"],
    )
    if "error" in result:
        return jsonify({"error": "vendor error"}), 503
    return jsonify({"payment_intent_id": result.get("id"), "status": result.get("status")})
