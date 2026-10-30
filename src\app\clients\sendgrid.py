"""SendGrid API client."""

import os
import random
import time
import uuid

import requests


def send_email(to: str, subject: str, body: str, from_email: str = "noreply@ghostvendor.dev") -> dict:
    idempotency_key = uuid.uuid4().hex
    attempt = 0
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
            return {"error": "connection_error", "message": "Could not connect to SendGrid"}
        except requests.exceptions.RequestException:
            return {"error": "request_error", "message": "SendGrid request failed"}
        except KeyError:
            return {"error": "config_error", "message": "SENDGRID_API_KEY is not set"}

        if response.status_code >= 400:
            if response.status_code not in (429, 502, 503):
                return {"error": "vendor_error", "status_code": response.status_code}
            if attempt >= 2:
                return {"error": "vendor_error", "status_code": response.status_code}
            if response.status_code == 429 and "Retry-After" in response.headers:
                try:
                    retry_after = int(response.headers["Retry-After"])
                    retry_after = min(retry_after, 10)
                except ValueError:
                    retry_after = None
                if retry_after is not None:
                    time.sleep(retry_after)
                else:
                    time.sleep(1 + random.uniform(0, 0.5) if attempt == 0 else 2 + random.uniform(0, 0.5))
            else:
                time.sleep(1 + random.uniform(0, 0.5) if attempt == 0 else 2 + random.uniform(0, 0.5))
            attempt += 1
            continue

        if response.text:
            try:
                parsed = response.json()
            except ValueError:
                return {"error": "malformed_response", "message": "SendGrid returned invalid JSON"}
            if not isinstance(parsed, dict) or not parsed:
                return {"error": "empty_response", "message": "SendGrid returned an empty response body"}
        return {"status_code": response.status_code}
