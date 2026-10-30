"""Stripe API client."""

import os
import random
import time
import uuid

import requests


def create_payment_intent(amount: int, currency: str, payment_method: str) -> dict:
    idempotency_key = str(uuid.uuid4())
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            base_url = os.environ.get("STRIPE_BASE_URL", "https://api.stripe.com")
            api_key = os.environ.get("STRIPE_API_KEY")
            if not api_key:
                return {"error": "config_error", "message": "STRIPE_API_KEY is not set"}
            response = requests.post(
                f"{base_url}/v1/payment_intents",
                auth=(api_key, ""),
                data={
                    "amount": amount,
                    "currency": currency,
                    "payment_method": payment_method,
                    "confirm": True,
                },
                timeout=10,
                headers={"Idempotency-Key": idempotency_key},
            )
        except requests.exceptions.Timeout:
            return {"error": "timeout", "message": "Stripe request timed out"}
        except requests.exceptions.ConnectionError:
            return {"error": "connection_error", "message": "Could not connect to Stripe"}
        except requests.exceptions.RequestException:
            return {"error": "request_error", "message": "Stripe request failed"}

        if response.status_code >= 400:
            if response.status_code in (429, 502, 503) and attempt < max_attempts - 1:
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after is not None:
                        try:
                            delay = max(0, min(int(retry_after), 10))
                        except ValueError:
                            delay = 2 ** attempt
                    else:
                        delay = 2 ** attempt
                else:
                    delay = 2 ** attempt
                time.sleep(delay + random.uniform(0, 0.5))
                continue
            return {"error": "vendor_error", "status_code": response.status_code}

        if response.text:
            try:
                body = response.json()
            except ValueError:
                return {"error": "malformed_response", "message": "Invalid JSON from Stripe"}
            if not isinstance(body, dict) or not body:
                return {"error": "empty_response", "message": "Empty or invalid response body from Stripe"}
            return body
        return {"status_code": response.status_code}

    return {"error": "vendor_error", "status_code": response.status_code}
