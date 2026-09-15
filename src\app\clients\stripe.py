"""Stripe API client — intentionally has no retry, timeout, or error handling."""

import os
import time
import threading
import requests

_circuit_open = False
_circuit_lock = threading.Lock()
_circuit_failures = 0
_circuit_last_failure = 0.0


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
    global _circuit_open, _circuit_failures, _circuit_last_failure
    with _circuit_lock:
        if _circuit_open:
            if time.time() - _circuit_last_failure > 60:
                _circuit_open = False
                _circuit_failures = 0
            else:
                return {"error": "circuit_open", "message": "Stripe temporarily unavailable"}
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
            with _circuit_lock:
                _circuit_failures += 1
                _circuit_last_failure = time.time()
                if _circuit_failures >= 3:
                    _circuit_open = True
            return {"error": "vendor_error", "message": "Stripe returned status " + str(response.status_code)}
        if response.status_code != 200:
            with _circuit_lock:
                _circuit_failures += 1
                _circuit_last_failure = time.time()
                if _circuit_failures >= 3:
                    _circuit_open = True
            return {"error": "vendor_error", "message": "Stripe returned status " + str(response.status_code)}
        with _circuit_lock:
            _circuit_failures = 0
        return response.json()
    except requests.exceptions.Timeout:
        with _circuit_lock:
            _circuit_failures += 1
            _circuit_last_failure = time.time()
            if _circuit_failures >= 3:
                _circuit_open = True
        return {"error": "timeout", "message": "Stripe request timed out"}
    except Exception:
        with _circuit_lock:
            _circuit_failures += 1
            _circuit_last_failure = time.time()
            if _circuit_failures >= 3:
                _circuit_open = True
        return {"error": "vendor_error", "message": "Stripe request failed"}
