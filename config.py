import os

class Config:
    # Flask settings
    SECRET_KEY = os.getenv('APP_SECRET_KEY') 
    SESSION_COOKIE_NAME = 'my_session_cookie'
    SESSION_TYPE = 'filesystem'
    WTF_CSRF_ENABLED = True
    
    # Auth0 Settings
    AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
    AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
    AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
