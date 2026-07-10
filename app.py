"""
CareerCompass AI - Flask Application Entry Point
"""

import logging
import os
from flask import Flask, render_template, redirect, url_for
from flask_cors import CORS

from config import ActiveConfig
from routes import api_bp


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO if not ActiveConfig.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Configuration
    app.config.from_object(ActiveConfig)
    app.secret_key = ActiveConfig.SECRET_KEY

    # Extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Blueprints
    app.register_blueprint(api_bp)

    # ---------------------------------------------------------------------------
    # Page routes (serve HTML templates)
    # ---------------------------------------------------------------------------

    @app.route("/")
    def index():
        """Landing page."""
        return render_template("index.html")

    @app.route("/profile")
    def profile():
        """Student profile input page."""
        return render_template("profile.html")

    @app.route("/analyzing")
    def analyzing():
        """Analysis loading/progress page."""
        return render_template("analyzing.html")

    @app.route("/report")
    def report():
        """Career analysis report dashboard."""
        return render_template("report.html")

    # ---------------------------------------------------------------------------
    # Error handlers
    # ---------------------------------------------------------------------------

    @app.errorhandler(404)
    def not_found(e):
        return render_template("error.html", code=404, message="Page Not Found"), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template("error.html", code=500, message="Internal Server Error"), 500

    # ---------------------------------------------------------------------------
    # Startup banner
    # ---------------------------------------------------------------------------
    missing = ActiveConfig.validate()
    if missing:
        logger.warning(
            "⚠️  Missing environment variables: %s. "
            "AI features will not work until these are set.",
            ", ".join(missing),
        )
    else:
        logger.info("✅ IBM watsonx.ai credentials detected.")

    logger.info(
        "🚀 CareerCompass AI starting on port %s (debug=%s)",
        ActiveConfig.APP_PORT,
        ActiveConfig.DEBUG,
    )

    return app


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=ActiveConfig.APP_PORT,
        debug=ActiveConfig.DEBUG,
    )
