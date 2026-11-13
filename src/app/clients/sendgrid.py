"""SendGrid API client."""

import os
import random
import time
import uuid
import requests


def send_email(to: str, subject: str, body: str, from_email: str = "noreply@ghostvendor.dev") -> int:
    idempotency_key = str(uuid.uuid4())
    attempts = 0
    while True:
        try:
            base_url = os.environ.get("SENDGRID_BASE_URL", "https://api.sendgrid.com")
            api_key = os.environ["SENDGRID_API_KEY"]
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
            return {"error": "connection_error", "message": "SendGrid connection failed"}
        except requests.exceptions.RequestException:
            return {"error": "request_error", "message": "SendGrid request failed"}
        except KeyError:
            return {"error": "config_error", "message": "SENDGRID_API_KEY is not set"}

        if response.status_code >= 400 and response.status_code not in (429, 502, 503):
            return {"error": "vendor_error", "status_code": response.status_code}

        if response.status_code in (429, 502, 503):
            if attempts >= 2:
                return {"error": "vendor_error", "status_code": response.status_code}
            retry_after = response.headers.get("Retry-After")
            if response.status_code == 429 and retry_after is not None:
                try:
                    delay = min(int(retry_after), 10)
                except ValueError:
                    delay = 2 ** attempts
            else:
                delay = 2 ** attempts
            time.sleep(delay + random.uniform(0, 0.5))
            attempts += 1
            continue

        if response.text:
            try:
                parsed = response.json()
            except ValueError:
                return {"error": "malformed_response", "message": "SendGrid returned invalid JSON"}
            if not isinstance(parsed, dict) or not parsed:
                return {"error": "empty_response", "message": "SendGrid returned an empty response body"}
        return {"status_code": response.status_code}
