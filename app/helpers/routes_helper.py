from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    """Custom decorator that protects routes from users that are not logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:  # If user is not in session (not logged in)
            return redirect(url_for('main.login'))  # Redirect to login page
        return f(*args, **kwargs)
    return decorated_function

def requires_role(role):
    """Custom decorator to check for user roles in the decoded token stored in session."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # session['user'] should be the decoded token (a dict)
            decoded_token = session.get('user', {})
            if not decoded_token:
                flash("You need to log in first", "danger")
                return redirect(url_for('main.login'))
            # Extract roles using your custom namespace
            roles = decoded_token.get('https://mobilab.demo.app.com/roles', [])
            if role not in roles:
                flash("You don't have permission to access this page.", "danger")
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return wrapper
    return decorator
