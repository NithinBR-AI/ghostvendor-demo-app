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
    """
    data = request.json
    result = sendgrid.send_email(
        to=data["to"],
        subject=data["subject"],
        body=data["body"],
        from_email=data.get("from", "noreply@ghostvendor.dev"),
    )
    if "error" in result:
        return jsonify({"error": "vendor error"}), 503
    code = result.get("status_code", 202)
    return jsonify({"status": "sent", "code": code})
