# ghostvendor-demo-app

A deliberately fragile Python web service that calls Stripe and SendGrid with no resilience handling. Built as the target application for [GhostVendor](https://github.com/NithinBR-AI/ghostvendor) — an autonomous dependency resilience engineer.

---

## What this app does

Two endpoints:

| Endpoint | Vendor | What it does |
|---|---|---|
| `POST /charge` | Stripe | Creates and confirms a PaymentIntent |
| `POST /notify` | SendGrid | Sends a transactional email |

Both endpoints make raw HTTP calls with no retry logic, no timeout, no circuit breaker, and no fallback. A vendor outage causes immediate failure.

---

## Why it's intentionally fragile

This repo exists to demonstrate GhostVendor's value. GhostVendor will:

1. Discover the Stripe and SendGrid dependencies via static analysis
2. Generate Evil Twin simulators that impersonate those APIs
3. Inject real failure modes (502, timeout, malformed JSON) via GitHub Actions
4. Diagnose what breaks and why
5. Generate a minimal resilience patch
6. Open a PR — only after CI proves the fix survives chaos

The before/after is the demo. This repo is the "before."

---

## Project structure

```
ghostvendor-demo-app/
├── src/
│   └── app/
│       ├── __init__.py          # Flask app factory
│       ├── routes/
│       │   ├── charge.py        # POST /charge
│       │   └── notify.py        # POST /notify
│       └── clients/
│           ├── stripe.py        # Raw Stripe API calls
│           └── sendgrid.py      # Raw SendGrid API calls
├── tests/
│   ├── test_charge.py
│   └── test_notify.py
├── main.py                      # Entrypoint
├── pyproject.toml
└── .env.example
```

---

## Setup

```bash
git clone https://github.com/NithinBR-AI/ghostvendor-demo-app.git
cd ghostvendor-demo-app

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -e ".[dev]"

cp .env.example .env
python main.py
```

---

## Evil Twin URL override

GhostVendor redirects vendor calls to its Evil Twin simulators via environment variables:

```bash
STRIPE_BASE_URL=http://localhost:8001   # Evil Twin for Stripe
SENDGRID_BASE_URL=http://localhost:8002 # Evil Twin for SendGrid
```

No real API credentials are needed when running under GhostVendor.

---

## Running tests

```bash
pytest tests/ -v
```

---

## License

MIT
