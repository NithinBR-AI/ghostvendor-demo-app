"""SendGrid API client — intentionally has no retry, timeout, or error handling."""

import os
import random
import time
import uuid
import requests


def send_email(to: str, subject: str, body: str, from_email: str = "noreply@ghostvendor.dev") -> int:
    base_url = os.environ.get("SENDGRID_BASE_URL", "https://api.sendgrid.com")
    api_key = os.environ["SENDGRID_API_KEY"]
    idempotency_key = str(uuid.uuid4())
    last_error = None
    for attempt in range(3):
        try:
            response = requests.post(
                f"{base_url}/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Idempotency-Key": idempotency_key,
                },
                json={
                    "personalizations": [{"to": [{"email": to}]}],
                    "from": {"email": from_email},
                    "subject": subject,
                    "content": [{"type": "text/plain", "value": body}],
                },
                timeout=10,
            )
        except requests.exceptions.Timeout:
            return {"error": "timeout", "message": "SendGrid request timed out"}
        except requests.exceptions.ConnectionError:
            return {"error": "connection_error", "message": "Failed to connect to SendGrid"}
        except requests.exceptions.RequestException as e:
            return {"error": "request_error", "message": str(e)}
        if response.status_code >= 400:
            if response.status_code in (429, 502, 503):
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            retry_after = min(int(retry_after), 10)
                        except ValueError:
                            retry_after = None
                    if retry_after:
                        time.sleep(retry_after + random.uniform(0, 0.5))
                    else:
                        time.sleep(2 ** attempt + random.uniform(0, 0.5))
                else:
                    time.sleep(2 ** attempt + random.uniform(0, 0.5))
                last_error = {"error": "vendor_error", "status_code": response.status_code}
                continue
            return {"error": "vendor_error", "status_code": response.status_code}
        if response.text:
            try:
                body_parsed = response.json()
            except ValueError:
                return {"error": "malformed_response", "message": "Response is not valid JSON"}
            if not isinstance(body_parsed, dict) or not body_parsed:
                return {"error": "empty_response", "message": "Response body is empty or not a dict"}
        return {"status_code": response.status_code}
    return last_error
