"""POST /notify — send a transactional email via SendGrid."""

from flask import Blueprint, request, jsonify
from app.clients import sendgrid
import logging

notify_bp = Blueprint("notify", __name__)


@notify_bp.route("/notify", methods=["POST"])
def notify():
    data = request.json
    if data is None or "to" not in data or "subject" not in data or "body" not in data:
        return jsonify({"error": "missing required fields"}), 400
    try:
        result = sendgrid.send_email(
            to=data["to"],
            subject=data["subject"],
            body=data["body"],
            from_email=data.get("from", "noreply@ghostvendor.dev"),
        )
    except Exception:
        logging.getLogger(__name__).warning("SendGrid client raised an exception")
        return jsonify({"error": "vendor error"}), 503
    if not isinstance(result, dict) or "error" in result:
        logging.getLogger(__name__).warning("SendGrid returned an error")
        return jsonify({"error": "vendor error"}), 503
    return jsonify({"status": "sent", "code": result.get("status_code", 200)})
