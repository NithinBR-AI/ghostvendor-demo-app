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
    result = sendgrid.send_email(
        to=data["to"],
        subject=data["subject"],
        body=data["body"],
        from_email=data.get("from", "noreply@ghostvendor.dev"),
    )
    if isinstance(result, dict) and "error" in result:
        if result["error"] == "timeout":
            return jsonify(result), 504
        return jsonify(result), 502
    if isinstance(result, int):
        if result == 429:
            return jsonify({"error": "rate_limited", "message": "SendGrid returned 429"}), 429
        if result >= 500:
            return jsonify({"error": "vendor_error", "message": f"SendGrid returned {result}"}), 502
        if result == 202:
            return jsonify({"status": "sent", "code": result})
        return jsonify({"status": "sent", "code": result})
    return jsonify({"error": "unexpected_response", "message": "Unexpected response from SendGrid"}), 502
