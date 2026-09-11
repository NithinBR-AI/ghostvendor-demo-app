"""POST /notify — send a transactional email via SendGrid."""

from flask import Blueprint, jsonify

notify_bp = Blueprint("notify", __name__)


@notify_bp.route("/notify", methods=["POST"])
def notify():
    return jsonify({"error": "not implemented"}), 501
