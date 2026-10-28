"""Stripe API client — intentionally has no retry, timeout, or error handling."""

import os
import random
import time
import uuid

import requests


def create_payment_intent(amount: int, currency: str, payment_method: str) -> dict:
    idempotency_key = str(uuid.uuid4())
    last_error = None
    for attempt in range(3):
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
        except requests.exceptions.Timeout as e:
            return {"error": "timeout", "message": str(e)}
        except requests.exceptions.ConnectionError as e:
            return {"error": "connection_error", "message": str(e)}
        except requests.exceptions.RequestException as e:
            return {"error": "request_error", "message": str(e)}
        if response.status_code >= 400:
            if response.status_code in (429, 502, 503):
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    if retry_after is not None:
                        try:
                            sleep_time = min(int(retry_after), 10)
                        except ValueError:
                            sleep_time = 2 ** attempt
                    else:
                        sleep_time = 2 ** attempt
                else:
                    sleep_time = 2 ** attempt
                time.sleep(sleep_time + random.uniform(0, 0.5))
                last_error = {"error": "vendor_error", "status_code": response.status_code}
                continue
            return {"error": "vendor_error", "status_code": response.status_code}
        if response.text:
            try:
                body = response.json()
            except ValueError:
                return {"error": "malformed_response", "message": "Response body is not valid JSON"}
            if not isinstance(body, dict) or not body:
                return {"error": "empty_response", "message": "Response body is empty or not a dict"}
            return body
        return {"status_code": response.status_code}
    return last_error if last_error else {"error": "request_error", "message": "Retries exhausted"}
