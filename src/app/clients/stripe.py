"""Stripe API client."""

import os
import random
import time
import uuid
import requests


def create_payment_intent(amount: int, currency: str, payment_method: str) -> dict:
    idempotency_key = str(uuid.uuid4())
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            base_url = os.environ.get("STRIPE_BASE_URL", "https://api.stripe.com")
            api_key = os.environ["STRIPE_API_KEY"]
            response = requests.post(
                f"{base_url}/v1/payment_intents",
                auth=(api_key, ""),
                data={
                    "amount": amount,
                    "currency": currency,
                    "payment_method": payment_method,
                    "confirm": True,
                },
                headers={"Idempotency-Key": idempotency_key},
                timeout=10,
            )
        except requests.exceptions.Timeout:
            return {"error": "timeout", "message": "Stripe request timed out"}
        except requests.exceptions.ConnectionError:
            return {"error": "connection_error", "message": "Could not connect to Stripe"}
        except (requests.exceptions.RequestException, KeyError):
            return {"error": "request_error", "message": "Stripe request failed"}

        if response.status_code >= 400 and response.status_code not in (429, 502, 503):
            return {"error": "vendor_error", "status_code": response.status_code}

        if response.status_code in (429, 502, 503):
            if attempt >= max_retries:
                return {"error": "vendor_error", "status_code": response.status_code}
            if response.status_code == 429 and "Retry-After" in response.headers:
                try:
                    retry_after = int(response.headers["Retry-After"])
                    retry_after = min(retry_after, 10)
                except ValueError:
                    retry_after = None
                if retry_after is not None:
                    time.sleep(retry_after + random.uniform(0, 0.5))
                else:
                    time.sleep(2 ** attempt + random.uniform(0, 0.5))
            else:
                time.sleep(2 ** attempt + random.uniform(0, 0.5))
            continue

        if response.status_code < 300:
            if not response.text:
                return {"status_code": response.status_code}
            try:
                body = response.json()
            except ValueError:
                return {"error": "malformed_response", "message": "Invalid JSON from Stripe"}
            if not isinstance(body, dict) or not body:
                return {"error": "empty_response", "message": "Empty response from Stripe"}
            return body

    return {"error": "vendor_error", "status_code": response.status_code}
