"""Stripe API client — intentionally has no retry, timeout, or error handling."""

import os
import random
import time
import uuid

import requests


def create_payment_intent(amount: int, currency: str, payment_method: str) -> dict:
    idempotency_key = str(uuid.uuid4())
    attempts = 0
    while True:
        attempts += 1
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
            if response.status_code in (429, 502, 503) and attempts < 3:
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after is not None:
                        try:
                            retry_after = int(retry_after)
                        except ValueError:
                            retry_after = None
                        if retry_after is not None:
                            time.sleep(min(retry_after, 10))
                            continue
                time.sleep((1 if attempts == 1 else 2) + random.uniform(0, 0.5))
                continue
            return {"error": "vendor_error", "status_code": response.status_code}

        if response.text:
            try:
                parsed = response.json()
            except ValueError:
                return {"error": "malformed_response", "message": "Stripe returned malformed JSON"}
            if not isinstance(parsed, dict) or not parsed:
                return {"error": "empty_response", "message": "Stripe returned an empty response"}
            return parsed
        return {"status_code": response.status_code}
