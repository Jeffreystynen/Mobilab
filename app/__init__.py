from flask import Flask, session, flash, redirect, url_for
from .config import Config
from authlib.integrations.flask_client import OAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
import os
import logging
from flask_wtf.csrf import CSRFProtect
from app.factories.service_factory import ServiceFactory
from app.helpers.env_validator import validate_env_vars
from app.error_handlers import register_error_handlers


# Initialize extensions
oauth = OAuth()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

csrf = CSRFProtect()

def create_app():
    # Create a Flask app instance
    validate_env_vars()
    app = Flask(__name__)
    app.model_dao = ServiceFactory.create_model_dao()
    app.feature_service = ServiceFactory.create_feature_service()
    app.prediction_service = ServiceFactory.create_prediction_service()

    # Load configuration
    app.config.from_object(Config)


    # Initialize extensions
    csrf.init_app(app)
    oauth.init_app(app)
    limiter.init_app(app)
    register_error_handlers(app)

    # Import and register blueprints
    from .routes import main
    app.register_blueprint(main)


    # Add security headers
    @app.after_request
    def add_security_headers(response):
        """Add security headers to every response."""
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://code.jquery.com https://cdn.jsdelivr.net https://stackpath.bootstrapcdn.com; "
            "style-src 'self' 'unsafe-inline' https://stackpath.bootstrapcdn.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https://*.auth0.com; "
            "font-src 'self' https://cdnjs.cloudflare.com https://stackpath.bootstrapcdn.com; "
            "frame-src 'self' https://*.auth0.com; "
            "connect-src 'self' https://*.auth0.com;"
        )
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Protection against clickjacking
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Enable browser's XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Force HTTPS
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response

    @app.context_processor
    def inject_user_roles():
        """Retrieves the user roles at startup."""
        roles = []
        user = session.get("user")
        if user:
            roles = user.get("https://mobilab.demo.app.com/roles", [])
        return dict(user_roles=roles)
    
    @app.errorhandler(RateLimitExceeded)
    def handle_ratelimit_error(e):
        """Handle rate limit exceeded errors globally."""
        flash("Too many requests. Please try again later.", "error")
        return redirect(url_for("main.rate_limit_exceeded")), 429


    return app


def setup_logging():
    """Configures logging for the Flask app."""
    log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    log_level = logging.INFO

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.FileHandler("logs/app.log"),
        ]
    )

    # Reduce verbosity for third-party libraries
    # logging.getLogger("werkzeug").setLevel(logging.WARNING)
    # logging.getLogger("urllib3").setLevel(logging.WARNING)