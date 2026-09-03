"""Flask application factory for ghostvendor-demo-app."""

from flask import Flask
from app.routes.charge import charge_bp
from app.routes.notify import notify_bp


def create_app() -> Flask:
    """
    Create and configure the Flask application.

    Registers all route blueprints. Configuration is loaded entirely
    from environment variables — no secrets in code.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)
    app.register_blueprint(charge_bp)
    app.register_blueprint(notify_bp)
    return app
