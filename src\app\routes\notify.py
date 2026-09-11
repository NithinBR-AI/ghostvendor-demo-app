"""POST /notify — send a transactional email via SendGrid."""

from flask import Blueprint, request, jsonify
from app.clients import sendgrid

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
        return jsonify({"error": "vendor error", "message": str(e)}), 503
    if isinstance(code, dict) and "error" in code:
        return jsonify(code), 503
    if isinstance(code, int) and code >= 400:
        return jsonify({"error": "vendor error", "code": code}), 503
    return jsonify({"status": "sent", "code": code})
