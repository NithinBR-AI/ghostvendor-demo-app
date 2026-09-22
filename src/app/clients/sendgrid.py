"""SendGrid API client — intentionally has no retry, timeout, or error handling."""

import os
import requests


def send_email(to: str, subject: str, body: str, from_email: str = "noreply@ghostvendor.dev") -> int:
    """
    Send a transactional email via SendGrid.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Plain-text email body.
        from_email: Sender address (defaults to noreply@ghostvendor.dev).

    Returns:
        HTTP status code from SendGrid (202 on success).

    Raises:
        requests.exceptions.Timeout: Propagates uncaught if SendGrid times out.
    """
    base_url = os.environ.get("SENDGRID_BASE_URL", "https://api.sendgrid.com")
    api_key = os.environ["SENDGRID_API_KEY"]

    response = requests.post(
        f"{base_url}/v3/mail/send",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": from_email},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}],
        },
    )
    return response.status_code
