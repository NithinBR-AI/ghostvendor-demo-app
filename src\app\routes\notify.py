"""POST /notify — send a transactional email via SendGrid."""

from flask import Blueprint, request, jsonify
from app.clients import sendgrid
import logging

notify_bp = Blueprint("notify", __name__)


@notify_bp.route("/notify", methods=["POST"])
def notify():
    """
    Send a transactional email via SendGrid.

    Request JSON:
        to (str): Recipient email address.
        subject (str): Email subject.
        body (str): Plain-text email body.
        from (str, optional): Sender address.

    Returns:
        JSON with status and HTTP code from SendGrid.
        No error handling — a 502 or timeout propagates silently or crashes.
    """
    data = request.json
    try:
        code = sendgrid.send_email(
            to=data["to"],
            subject=data["subject"],
            body=data["body"],
            from_email=data.get("from", "noreply@ghostvendor.dev"),
        )
    except Exception as e:
        logging.warning("SendGrid call failed with exception: %s", e)
        return jsonify({"error": "vendor error"}), 503
    if isinstance(code, dict) and "error" in code:
        logging.warning("SendGrid returned error: %s", code)
        return jsonify({"error": "vendor error"}), 503
    if not isinstance(code, int) or code >= 400:
        logging.warning("SendGrid returned non-success status: %s", code)
        return jsonify({"error": "vendor error"}), 503
    return jsonify({"status": "sent", "code": code})
