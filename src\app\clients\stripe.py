"""Stripe API client — intentionally has no retry, timeout, or error handling."""

import os
import time
import threading
import logging
import requests

logger = logging.getLogger(__name__)

_circuit_open = False
_circuit_lock = threading.Lock()
_failure_count = 0
_last_failure_time = 0.0


def create_payment_intent(amount: int, currency: str, payment_method: str) -> dict:
    """
    Create and confirm a Stripe PaymentIntent.

    Args:
        amount: Amount in smallest currency unit (e.g. cents for USD).
        currency: ISO 4217 currency code (e.g. "usd").
        payment_method: Stripe PaymentMethod ID (e.g. "pm_card_visa").

    Returns:
        Raw Stripe API response as a dict.

    Raises:
        KeyError: If the response does not contain expected fields (no validation).
        requests.exceptions.Timeout: Propagates uncaught if Stripe times out.
    """
    global _circuit_open, _failure_count, _last_failure_time

    with _circuit_lock:
        if _circuit_open:
            if time.time() - _last_failure_time > 60:
                _circuit_open = False
                _failure_count = 0
            else:
                return {"error": "circuit_open", "message": "Stripe circuit breaker is open"}

    base_url = os.environ.get("STRIPE_BASE_URL", "https://api.stripe.com")
    api_key = os.environ["STRIPE_API_KEY"]

    try:
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
        )
        if response.status_code in (429, 502, 503):
            time.sleep(1)
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
            )
            if response.status_code in (429, 502, 503):
                raise requests.exceptions.HTTPError(f"Retry failed with status {response.status_code}")
        if not response.text:
            raise ValueError("Empty response body")
        result = response.json()
        with _circuit_lock:
            _failure_count = 0
        return result
    except Exception as e:
        with _circuit_lock:
            _failure_count += 1
            _last_failure_time = time.time()
            if _failure_count >= 3:
                _circuit_open = True
        logger.warning("Stripe call failed: %s", e)
        return {"error": "stripe_error", "message": str(e)}
