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
                raise RuntimeError("Circuit breaker open — Stripe temporarily unavailable")
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
            timeout=(2, 5),
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
                timeout=(2, 5),
            )
            if response.status_code in (429, 502, 503):
                with _circuit_lock:
                    _failure_count += 1
                    _last_failure_time = time.time()
                    if _failure_count >= 3:
                        _circuit_open = True
                return {"error": "transient_failure", "message": "Stripe returned transient error after retry"}
        if response.status_code >= 400:
            with _circuit_lock:
                _failure_count += 1
                _last_failure_time = time.time()
                if _failure_count >= 3:
                    _circuit_open = True
            return {"error": "stripe_error", "message": f"Stripe returned status {response.status_code}"}
        try:
            result = response.json()
        except Exception:
            with _circuit_lock:
                _failure_count += 1
                _last_failure_time = time.time()
                if _failure_count >= 3:
                    _circuit_open = True
            return {"error": "malformed_json", "message": "Stripe response is not valid JSON"}
        with _circuit_lock:
            _failure_count = 0
        return result
    except requests.exceptions.Timeout:
        with _circuit_lock:
            _failure_count += 1
            _last_failure_time = time.time()
            if _failure_count >= 3:
                _circuit_open = True
        return {"error": "timeout", "message": "Stripe request timed out"}
    except requests.exceptions.ConnectionError:
        with _circuit_lock:
            _failure_count += 1
            _last_failure_time = time.time()
            if _failure_count >= 3:
                _circuit_open = True
        return {"error": "connection_error", "message": "Could not connect to Stripe"}
