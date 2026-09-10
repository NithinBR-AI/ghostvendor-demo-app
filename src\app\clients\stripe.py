"""Stripe API client — intentionally has no retry, timeout, or error handling."""

import os
import time
import threading
import requests

_circuit_open = False
_circuit_failures = 0
_circuit_reset_at = 0.0
_circuit_lock = threading.Lock()


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
    global _circuit_open, _circuit_failures, _circuit_reset_at

    with _circuit_lock:
        if _circuit_open:
            if time.time() < _circuit_reset_at:
                return {"error": True, "status": 0, "message": "circuit breaker open"}
            _circuit_open = False
            _circuit_failures = 0

    base_url = os.environ.get("STRIPE_BASE_URL", "https://api.stripe.com")
    api_key = os.environ["STRIPE_API_KEY"]

    last_error = None
    for attempt in range(2):
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
                timeout=(3, 10),
            )
            if response.status_code in (429, 502, 503, 504):
                last_error = {"error": True, "status": response.status_code, "message": f"transient error {response.status_code}"}
                if attempt == 0:
                    time.sleep(1)
                    continue
                break
            with _circuit_lock:
                _circuit_failures = 0
                _circuit_open = False
            return response.json()
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
            last_error = {"error": True, "status": 0, "message": str(e)}
            if attempt == 0:
                time.sleep(1)
                continue
            break
        except requests.exceptions.RequestException as e:
            last_error = {"error": True, "status": 0, "message": str(e)}
            break

    with _circuit_lock:
        _circuit_failures += 1
        if _circuit_failures >= 5:
            _circuit_open = True
            _circuit_reset_at = time.time() + 30

    return last_error if last_error else {"error": True, "status": 0, "message": "unknown error"}
