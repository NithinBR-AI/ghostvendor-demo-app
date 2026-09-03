"""Tests for POST /notify endpoint."""

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


def mock_response(status_code: int) -> MagicMock:
    m = MagicMock()
    m.status_code = status_code
    return m


class TestNotify:
    def test_successful_notify(self, client):
        """Normal path — SendGrid accepts the email (202)."""
        with patch("app.clients.sendgrid.requests.post") as mock_post:
            mock_post.return_value = mock_response(202)
            resp = client.post("/notify", json={
                "to": "user@example.com",
                "subject": "Your receipt",
                "body": "Thanks for your purchase.",
            })
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "sent"
        assert resp.get_json()["code"] == 202

    def test_sendgrid_502_silently_returns_200(self, client):
        """502 from SendGrid — no error handling, returns 200 with error code hidden."""
        with patch("app.clients.sendgrid.requests.post") as mock_post:
            mock_post.return_value = mock_response(502)
            resp = client.post("/notify", json={
                "to": "user@example.com",
                "subject": "Your receipt",
                "body": "Thanks for your purchase.",
            })
        assert resp.status_code == 200
        assert resp.get_json()["code"] == 502

    def test_sendgrid_timeout_crashes_app(self, client):
        """SendGrid connection timeout — propagates uncaught as Timeout exception."""
        with patch("app.clients.sendgrid.requests.post", side_effect=req.exceptions.Timeout):
            with pytest.raises(req.exceptions.Timeout):
                client.post("/notify", json={
                    "to": "user@example.com",
                    "subject": "Your receipt",
                    "body": "Thanks for your purchase.",
                })
