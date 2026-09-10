"""SendGrid API client — intentionally has no retry, timeout, or error handling."""

import os
import time
import requests


def send_email(to: str, subject: str, body: str, from_email: str = "noreply@ghostvendor.dev"):
    """
    Send a transactional email via SendGrid.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Plain-text email body.
        from_email: Sender address (defaults to noreply@ghostvendor.dev).

    Returns:
        HTTP status code from SendGrid (202 on success) or error dict on failure.

    Raises:
        requests.exceptions.Timeout: Propagates uncaught if SendGrid times out.
    """
    base_url = os.environ.get("SENDGRID_BASE_URL", "https://api.sendgrid.com")
    api_key = os.environ["SENDGRID_API_KEY"]

    for attempt in range(2):
        try:
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
                timeout=10,
            )
            if response.status_code in (429, 502, 503) and attempt == 0:
                time.sleep(1)
                continue
            if response.status_code >= 500:
                return {"error": "vendor_error", "message": f"SendGrid returned {response.status_code}"}
            return response.status_code
        except requests.exceptions.Timeout:
            if attempt == 0:
                time.sleep(1)
                continue
            return {"error": "timeout", "message": "SendGrid request timed out after retry"}
        except requests.exceptions.RequestException as e:
            if attempt == 0:
                time.sleep(1)
                continue
            return {"error": "request_failed", "message": str(e)}
    return {"error": "unknown", "message": "SendGrid request failed after retry"}
