"""POST /notify \u2014 send a transactional email via SendGrid."""

import logging

from flask import Blueprint, request, jsonify
from app.clients import sendgrid

notify_bp = Blueprint("notify", __name__)
logger = logging.getLogger(__name__)


@notify_bp.route("/notify", methods=["POST"])
def notify():
    data = request.get_json(silent=True)
    if not data or not data.get("to") or not data.get("subject") or not data.get("body"):
        return jsonify({"error": "missing required fields"}), 400
    try:
        result = sendgrid.send_email(
            to=data["to"],
            subject=data["subject"],
            body=data["body"],
            from_email=data.get("from", "noreply@ghostvendor.dev"),
        )
    except Exception:
        logger.warning("SendGrid notify call raised an exception", exc_info=True)
        return jsonify({"error": "vendor error"}), 503
    if not isinstance(result, dict) or "error" in result or result.get("status_code", 200) >= 400:
        logger.warning("SendGrid notify call failed: %s", result)
        return jsonify({"error": "vendor error"}), 503
    return jsonify({"status": "sent", "code": result.get("status_code", 202)})
