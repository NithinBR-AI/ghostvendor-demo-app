"""POST /charge — process a payment via Stripe."""

from flask import Blueprint, jsonify

charge_bp = Blueprint("charge", __name__)


@charge_bp.route("/charge", methods=["POST"])
def charge():
    return jsonify({"error": "not implemented"}), 501
