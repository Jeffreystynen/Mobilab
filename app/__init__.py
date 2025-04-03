from flask import Flask, session
from .config import Config
from authlib.integrations.flask_client import OAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import logging
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
oauth = OAuth()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

def create_app():
    # Create a Flask app instance
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Initialize extensions
    csrf = CSRFProtect(app)
    oauth.init_app(app)
    limiter.init_app(app)  # Initialize limiter with app

    # Import and register blueprints
    from .routes import main
    app.register_blueprint(main)

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint)

    # Initialize Swagger for API documentation
    from flasgger import Swagger
    app.config['SWAGGER'] = {
        'title': 'My API',
        'uiversion': 3
    }
    Swagger(app)

    @app.context_processor
    def inject_user_roles():
        """Retrieves the user roles at startup."""
        roles = []
        user = session.get("user")
        if user:
            roles = user.get("https://mobilab.demo.app.com/roles", [])
        return dict(user_roles=roles)

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