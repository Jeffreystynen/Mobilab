from flask import render_template, flash
from flask_limiter.errors import RateLimitExceeded

def register_error_handlers(app):
    """Register global error handlers for the application."""

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template("errors/500.html"), 500

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.error(f"Unexpected error: {str(error)}", exc_info=True)
        return render_template("errors/500.html"), 500
    
    def register_error_handlers(app):
        @app.errorhandler(RateLimitExceeded)
        def rate_limit_error(e):
            return render_template("errors/rate_limit_exceeded.html"), 429

def flash_form_errors(form):
    """
    Flashes all validation errors from a Flask-WTF form.
    Args:
        form (FlaskForm): The form to validate.
    """
    for field_name, errors in form.errors.items():
        for error in errors:
            flash(f"{field_name.capitalize()}: {error}", "danger")