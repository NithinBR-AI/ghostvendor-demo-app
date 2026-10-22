"""POST /notify — send a transactional email via SendGrid."""

from flask import Blueprint, request, jsonify
from app.clients import sendgrid

notify_bp = Blueprint("notify", __name__)


@notify_bp.route("/notify", methods=["POST"])
def notify():
    data = request.json
    if data is None or "to" not in data or "subject" not in data or "body" not in data:
        return jsonify({"error": "Missing required fields"}), 400
    result = sendgrid.send_email(
        to=data["to"],
        subject=data["subject"],
        body=data["body"],
        from_email=data.get("from", "noreply@ghostvendor.dev"),
    )
    if isinstance(result, dict) and "error" in result:
        return jsonify({"error": "vendor error"}), 503
    return jsonify({"status": "sent", "code": result.get("status_code", 202)})
