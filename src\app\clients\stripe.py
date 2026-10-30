"""Stripe API client."""

import os
import random
import time
import uuid

import requests


def create_payment_intent(amount: int, currency: str, payment_method: str) -> dict:
    idempotency_key = str(uuid.uuid4())
    retries = 0
    while True:
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
                timeout=10,
                headers={"Idempotency-Key": idempotency_key},
            )
        except requests.exceptions.Timeout:
            return {"error": "timeout", "message": "Stripe request timed out"}
        except requests.exceptions.ConnectionError:
            return {"error": "connection_error", "message": "Could not connect to Stripe"}
        except requests.exceptions.RequestException:
            return {"error": "request_error", "message": "Stripe request failed"}

        if response.status_code >= 400 and response.status_code not in (429, 502, 503):
            return {"error": "vendor_error", "status_code": response.status_code}

        if response.status_code in (429, 502, 503):
            if retries >= 2:
                return {"error": "vendor_error", "status_code": response.status_code}
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after is not None:
                    try:
                        sleep_seconds = min(int(retry_after), 10)
                    except ValueError:
                        sleep_seconds = 1 + retries + random.uniform(0, 0.5)
                    time.sleep(sleep_seconds)
                else:
                    time.sleep(1 + retries + random.uniform(0, 0.5))
            else:
                time.sleep(1 + retries + random.uniform(0, 0.5))
            retries += 1
            continue

        if response.text:
            try:
                parsed = response.json()
            except ValueError:
                return {"error": "malformed_response", "message": "Stripe returned malformed JSON"}
            if not isinstance(parsed, dict) or not parsed:
                return {"error": "empty_response", "message": "Stripe returned an empty response"}
            return parsed
        return {"status_code": response.status_code}
