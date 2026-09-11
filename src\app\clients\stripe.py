"""Stripe API client — intentionally has no retry, timeout, or error handling."""

import os
import time
import requests


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
    except requests.exceptions.Timeout:
        return {"error": "timeout", "message": "Stripe request timed out"}

    if response.status_code in (429, 502, 503):
        time.sleep(1)
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
        except requests.exceptions.Timeout:
            return {"error": "timeout", "message": "Stripe request timed out on retry"}
        if response.status_code in (429, 502, 503):
            return {"error": "retry_failed", "message": f"Stripe returned {response.status_code} after retry"}

    try:
        return response.json()
    except ValueError:
        return {"error": "invalid_json", "message": "Stripe response was not valid JSON"}
