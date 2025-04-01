import os
from dotenv import load_dotenv

class Config:
    """Configuration of the entire application."""
    load_dotenv() 

    # Flask settings
    SECRET_KEY = os.getenv('APP_SECRET_KEY') 
    SESSION_COOKIE_NAME = 'my_session_cookie'
    SESSION_TYPE = 'filesystem'
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.getenv('WTF_CSRF_SECRET_KEY')
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT")
    SECURITY_PASSWORD_HASH = "bcrypt"

    
    # Auth0 Settings
    AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
    AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
    AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
    AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")

    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True  