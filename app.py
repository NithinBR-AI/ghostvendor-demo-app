import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

STRIPE_API_KEY = os.environ["STRIPE_API_KEY"]
SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]
STRIPE_BASE_URL = os.environ.get("STRIPE_BASE_URL", "https://api.stripe.com")
SENDGRID_BASE_URL = os.environ.get("SENDGRID_BASE_URL", "https://api.sendgrid.com")


@app.route("/charge", methods=["POST"])
def charge():
    data = request.json
    response = requests.post(
        f"{STRIPE_BASE_URL}/v1/payment_intents",
        auth=(STRIPE_API_KEY, ""),
        data={
            "amount": data["amount"],
            "currency": data.get("currency", "usd"),
            "payment_method": data["payment_method"],
            "confirm": True,
        },
    )
    result = response.json()
    return jsonify({"payment_intent_id": result["id"], "status": result["status"]})


@app.route("/notify", methods=["POST"])
def notify():
    data = request.json
    response = requests.post(
        f"{SENDGRID_BASE_URL}/v3/mail/send",
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "personalizations": [{"to": [{"email": data["to"]}]}],
            "from": {"email": data.get("from", "noreply@ghostvendor.dev")},
            "subject": data["subject"],
            "content": [{"type": "text/plain", "value": data["body"]}],
        },
    )
    return jsonify({"status": "sent", "code": response.status_code})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
