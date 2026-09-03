import pytest
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("STRIPE_API_KEY", "sk_test_fake")
    monkeypatch.setenv("SENDGRID_API_KEY", "SG.fake")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def make_response(json_data, status_code=200):
    mock = MagicMock()
    mock.json.return_value = json_data
    mock.status_code = status_code
    return mock


class TestCharge:
    def test_successful_charge(self, client):
        with patch("app.requests.post") as mock_post:
            mock_post.return_value = make_response({"id": "pi_123", "status": "succeeded"})
            resp = client.post("/charge", json={
                "amount": 1000,
                "payment_method": "pm_card_visa",
            })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["payment_intent_id"] == "pi_123"
        assert data["status"] == "succeeded"

    def test_stripe_502_crashes_app(self, client):
        with patch("app.requests.post") as mock_post:
            mock_post.return_value = make_response({}, status_code=502)
            with pytest.raises(Exception):
                client.post("/charge", json={
                    "amount": 1000,
                    "payment_method": "pm_card_visa",
                })

    def test_stripe_timeout_crashes_app(self, client):
        import requests as req
        with patch("app.requests.post", side_effect=req.exceptions.Timeout):
            with pytest.raises(Exception):
                client.post("/charge", json={
                    "amount": 1000,
                    "payment_method": "pm_card_visa",
                })


class TestNotify:
    def test_successful_notify(self, client):
        with patch("app.requests.post") as mock_post:
            mock_post.return_value = make_response({}, status_code=202)
            resp = client.post("/notify", json={
                "to": "user@example.com",
                "subject": "Your receipt",
                "body": "Thanks for your purchase.",
            })
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "sent"

    def test_sendgrid_502_silently_returns(self, client):
        with patch("app.requests.post") as mock_post:
            mock_post.return_value = make_response({}, status_code=502)
            resp = client.post("/notify", json={
                "to": "user@example.com",
                "subject": "Your receipt",
                "body": "Thanks for your purchase.",
            })
        # No error handling — returns 200 even on vendor failure
        assert resp.status_code == 200
