"""Tests for POST /charge endpoint."""

import pytest
import requests as req
from unittest.mock import patch, MagicMock
from app import create_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("STRIPE_API_KEY", "sk_test_fake")
    monkeypatch.setenv("SENDGRID_API_KEY", "SG.fake")
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    m = MagicMock()
    m.json.return_value = json_data
    m.status_code = status_code
    return m


class TestCharge:
    def test_successful_charge(self, client):
        """Normal path — Stripe returns a confirmed PaymentIntent."""
        with patch("app.clients.stripe.requests.post") as mock_post:
            mock_post.return_value = mock_response({"id": "pi_123", "status": "succeeded"})
            resp = client.post("/charge", json={
                "amount": 1000,
                "currency": "usd",
                "payment_method": "pm_card_visa",
            })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["payment_intent_id"] == "pi_123"
        assert data["status"] == "succeeded"

    def test_stripe_502_crashes_app(self, client):
        """502 from Stripe — no error handling, KeyError on missing 'id' field propagates."""
        with patch("app.clients.stripe.requests.post") as mock_post:
            mock_post.return_value = mock_response({"error": "Bad Gateway"}, status_code=502)
            with pytest.raises(KeyError):
                client.post("/charge", json={
                    "amount": 1000,
                    "currency": "usd",
                    "payment_method": "pm_card_visa",
                })

    def test_stripe_timeout_crashes_app(self, client):
        """Stripe connection timeout — propagates uncaught as Timeout exception."""
        with patch("app.clients.stripe.requests.post", side_effect=req.exceptions.Timeout):
            with pytest.raises(req.exceptions.Timeout):
                client.post("/charge", json={
                    "amount": 1000,
                    "currency": "usd",
                    "payment_method": "pm_card_visa",
                })
