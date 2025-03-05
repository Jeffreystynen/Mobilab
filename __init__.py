from flask import Flask
from .config import Config
from authlib.integrations.flask_client import OAuth
import os

oauth = OAuth()

def create_app():
    # Create a Flask app instance
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize OAuth
    oauth.init_app(app)

    # Import and register blueprints (import after app is created to avoid circular imports)
    from .routes import main  
    app.register_blueprint(main)

    return app