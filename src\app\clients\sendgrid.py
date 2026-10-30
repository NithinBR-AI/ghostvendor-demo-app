"""SendGrid API client."""

import os
import time
import random
import uuid
import requests


def send_email(to: str, subject: str, body: str, from_email: str = "noreply@ghostvendor.dev"):
    idempotency_key = str(uuid.uuid4())
    max_retries = 2
    for attempt in range(max_retries + 1):
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
            return {"error": "connection_error", "message": "Could not connect to SendGrid"}
        except requests.exceptions.RequestException:
            return {"error": "request_error", "message": "SendGrid request failed"}
        except KeyError:
            return {"error": "config_error", "message": "Missing SENDGRID_API_KEY"}

        if response.status_code >= 400:
            if response.status_code in (429, 502, 503) and attempt < max_retries:
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after is not None:
                        try:
                            delay = min(int(retry_after), 10)
                        except (ValueError, TypeError):
                            delay = 1 if attempt == 0 else 2
                    else:
                        delay = 1 if attempt == 0 else 2
                else:
                    delay = 1 if attempt == 0 else 2
                time.sleep(delay + random.uniform(0, 0.5))
                continue
            return {"error": "vendor_error", "status_code": response.status_code}

        if response.text:
            try:
                data = response.json()
            except ValueError:
                return {"error": "malformed_response", "message": "SendGrid returned malformed JSON"}
            if not isinstance(data, dict) or not data:
                return {"error": "empty_response", "message": "SendGrid returned an empty response body"}
            return data
        return {"status_code": response.status_code}
