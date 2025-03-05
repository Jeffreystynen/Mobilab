import os

class Config:
    # Flask settings (you can add others here later)
    SECRET_KEY = os.getenv('APP_SECRET_KEY')  # Change this to a proper secret key
    SESSION_COOKIE_NAME = 'my_session_cookie'
    
    # Auth0 Settings
    AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
    AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
    AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
