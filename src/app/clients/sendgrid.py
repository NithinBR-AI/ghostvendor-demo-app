"""SendGrid API client."""

import os
import random
import time
import uuid
import requests


def send_email(to: str, subject: str, body: str, from_email: str = "noreply@ghostvendor.dev"):
    base_url = os.environ.get("SENDGRID_BASE_URL", "https://api.sendgrid.com")
    api_key = os.environ["SENDGRID_API_KEY"]
    idempotency_key = str(uuid.uuid4())
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Idempotency-Key": idempotency_key,
    }
    payload = {
        "personalizations": [{"to": [{"email": to}]}],
        "from": {"email": from_email},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }
    url = f"{base_url}/v3/mail/send"
    retries = 0
    while True:
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
        except requests.exceptions.Timeout:
            return {"error": "timeout", "message": "Request to SendGrid timed out"}
        except requests.exceptions.ConnectionError:
            return {"error": "connection_error", "message": "Failed to connect to SendGrid"}
        except requests.exceptions.RequestException:
            return {"error": "request_error", "message": "Unexpected request error"}
        if response.status_code >= 400 and response.status_code not in (429, 502, 503):
            return {"error": "vendor_error", "status_code": response.status_code}
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after is not None:
                try:
                    retry_after = min(int(retry_after), 10)
                except ValueError:
                    retry_after = None
            if retries >= 2:
                return {"error": "vendor_error", "status_code": 429}
            sleep_time = (2 ** retries) + random.uniform(0, 0.5)
            if retry_after is not None:
                sleep_time = retry_after
            time.sleep(sleep_time)
            retries += 1
            continue
        if response.status_code in (502, 503):
            if retries >= 2:
                return {"error": "vendor_error", "status_code": response.status_code}
            sleep_time = (2 ** retries) + random.uniform(0, 0.5)
            time.sleep(sleep_time)
            retries += 1
            continue
        if response.status_code >= 200 and response.status_code < 300:
            if response.text:
                try:
                    body = response.json()
                except ValueError:
                    return {"error": "malformed_response", "message": "Response is not valid JSON"}
                if not isinstance(body, dict) or not body:
                    return {"error": "empty_response", "message": "Response body is empty or not a dict"}
                return body
            return {"status_code": response.status_code}
        return {"error": "vendor_error", "status_code": response.status_code}
