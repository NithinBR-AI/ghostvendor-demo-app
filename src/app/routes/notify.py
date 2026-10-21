"""POST /notify — send a transactional email via SendGrid."""

from flask import Blueprint, request, jsonify
from app.clients import sendgrid

notify_bp = Blueprint("notify", __name__)


@notify_bp.route("/notify", methods=["POST"])
def notify():
    if request.json is None:
        return jsonify({"error": "vendor error"}), 503
    data = request.json
    if "to" not in data or not data["to"] or "subject" not in data or not data["subject"] or "body" not in data or not data["body"]:
        return jsonify({"error": "vendor error"}), 503
    try:
        result = sendgrid.send_email(
            to=data["to"],
            subject=data["subject"],
            body=data["body"],
            from_email=data.get("from", "noreply@ghostvendor.dev"),
        )
    except Exception:
        return jsonify({"error": "vendor error"}), 503
    if not isinstance(result, dict) or "error" in result or result.get("status_code", 200) >= 400:
        return jsonify({"error": "vendor error"}), 503
    return jsonify({"status": "sent", "code": result.get("status_code")})
