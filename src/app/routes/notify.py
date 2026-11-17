"""POST /notify — send a transactional email via SendGrid."""

import logging

from flask import Blueprint, request, jsonify
from app.clients import sendgrid

notify_bp = Blueprint("notify", __name__)


@notify_bp.route("/notify", methods=["POST"])
def notify():
    data = request.json
    if not isinstance(data, dict) or not data or not all(data.get(k) for k in ("to", "subject", "body")):
        return jsonify({"error": "missing required fields"}), 400
    try:
        result = sendgrid.send_email(
            to=data["to"],
            subject=data["subject"],
            body=data["body"],
            from_email=data.get("from", "noreply@ghostvendor.dev"),
        )
    except Exception:
        logging.getLogger(__name__).warning("SendGrid call raised an exception", exc_info=True)
        return jsonify({"error": "vendor error"}), 503
    if not isinstance(result, dict) or "error" in result or result.get("status_code", 200) >= 400:
        logging.getLogger(__name__).warning("SendGrid vendor error: %s", result)
        return jsonify({"error": "vendor error"}), 503
    return jsonify({"status": "sent", "code": result.get("status_code", 200)})
