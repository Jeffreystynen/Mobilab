from flask import Blueprint, render_template, request, redirect, url_for, session, flash, make_response, send_file
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
import requests
from .form import PredictionForm, CSRFProtectionForm
from app import oauth
from app.helpers.routes_helper import login_required, requires_role
from app.services.auth_service import (
    fetch_all_users,
    fetch_pending_approvals,
    approve_user,
    reject_user,
    handle_auth_callback,
)
import secrets
import logging
from app.helpers.session_helper import store_prediction_results
from . import limiter
from flask import current_app as app
from app.helpers.report_builder import ReportBuilder, ReportDirector
from app.helpers.pdf_generator import generate_pdf
from app.error_handlers import flash_form_errors
from io import BytesIO
import base64


main = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

logger.info("Application started successfully!")

# Register Auth0 OAuth
auth0 = oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)


@main.route('/')
def index():
    """Serves the Auth0 login page."""
    return login()


@main.route("/login")
@limiter.limit("5 per minute")
def login():
    """Serves the Auth0 login page."""
    nonce = secrets.token_urlsafe(16)
    session["nonce"] = nonce
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("main.callback", _external=True),
        nonce=nonce
    )


@main.route("/callback", methods=["GET", "POST"])
def callback():
    """Establishes access token and checks users' approval status."""
    try:
        token = oauth.auth0.authorize_access_token()
        result = handle_auth_callback(token)
        flash(result["message"], "success")
        return redirect(url_for("main.input_params"))
    except ValueError as e:
        logger.error(f"Error in callback: {str(e)}", exc_info=True)
        flash(str(e), "warning")
        return redirect(url_for("main.pending_approval"))


@main.route("/logout")
def logout():
    """Handles logout with Auth0."""
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("main.login", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )


@main.route("/pending_approval")
def pending_approval():
    """Users who are not approved yet get redirected to this route."""
    return render_template("pending_approval.html")


@main.route("/input", methods=["GET", "POST"])
@login_required
@limiter.limit("5 per minute")
def input_params():
    """
    Handles model interaction using a form.
    """
    prediction = None

    try:
        # Fetch available models
        model_dao = app.model_dao
        models = model_dao.get_models()
        prediction_service = app.prediction_service
        feature_service = app.feature_service
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}", exc_info=True)
        flash("Failed to load models. Please try again later.", "danger")
        models = []

    # Handle form submission
    form = PredictionForm()
    if request.method == "POST" and form.validate_on_submit():
        try:
            # Get selected model
            selected_model = request.form.get("model") or (models[0] if models else None)
            if not selected_model:
                raise ValueError("No model available.")

            # Process prediction request
            result = prediction_service.process_prediction_request(form, selected_model)
            
            if result["success"]:
                # Store results in session
                store_prediction_results(
                    session,
                    result,
                    result["features"],
                    result["contributions_image_path"],
                    result["explanation_text"],
                    selected_model
                )
                prediction = result["prediction"]
            else:
                flash(result["error"], "input_params")
                
        except ValueError as e:
            logger.error(f"Error processing prediction: {str(e)}", exc_info=True)
            flash(str(e), "input_params")
    else:
        flash_form_errors(form)

    return render_template(
        "input_params.html",
        form=form,
        prediction=prediction,
        models=models,
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
        page_name="input_params"
    )


@main.route("/dashboard", methods=["GET", "POST"])
@login_required
@limiter.limit("20 per minute")
def dashboard():
    """Serves LIME plot and parameters used to make predictions from the last prediction."""
    contributions_image_path = session.get("contributions_image_path", None)
    prediction_values = session.get("prediction_values", None)
    contributions_explanation = session.get("contributions_explanation", None)
    form = PredictionForm()

    if not prediction_values:
        flash("No prediction values available. Please make a prediction first.", "warning")
        return redirect(url_for("main.input_params"))

    # Build the report using the ReportBuilder
    builder = ReportBuilder()
    director = ReportDirector(builder)
    web_report = director.build_web_report(
        parameters=prediction_values,
        plot_path=contributions_image_path,
        form=form
    )

    # Pass the generated sections to the template
    return render_template(
        "dashboard.html",
        report=web_report.get_sections(),
        explanation=contributions_explanation,
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )


@main.route("/download_report", methods=["GET"])
@login_required
@limiter.limit("5 per minute")
def download_report():
    """Generate and download the prediction report as a PDF."""
    model_dao = app.model_dao
    model = session.get("model", None)

    prediction = session.get("prediction_values", {}).get("prediction", 1)
    explanation = session.get("contributions_explanation", "No explanation available.")
    contribution_image_path = session.get("contributions_image_path", None)
    parameters = session.get("prediction_values", {})
    metadata = model_dao.get_metrics(model)
    plots = model_dao.get_plots(model)
    report = model_dao.get_report(model)["report"]
    report = json.loads(report)
    form = PredictionForm()

    # Build report
    builder = ReportBuilder()
    director = ReportDirector(builder)
    pdf_report = director.build_pdf_report(explanation, contribution_image_path, parameters, form, metadata, plots, report)

    # Generate PDF
    pdf = generate_pdf(pdf_report)

    return send_file(
        BytesIO(pdf),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="report.pdf"
    )


@main.route("/models", methods=["GET", "POST"])
@login_required
@limiter.limit("20 per minute")
def models():
    """
    Serves statistics and plots about the served model, including accuracy, precision, recall, training shape,
    ROC curve, P/R curve, and SHAP summary plot.
    """
    form = CSRFProtectionForm()
    model_dao = app.model_dao

    try:
        models = model_dao.get_models()
    except Exception as e:
        logger.error(f"Error fetching models: {str(e)}", exc_info=True)
        flash("Failed to load models. Please try again later.", "danger")
        models = []
        return redirect(url_for("main.input_params"))

    selected_model = request.form.get("model") if request.method == "POST" else None
    selected_model = selected_model or (models[0] if models else "No models available")

    try:
        metrics = model_dao.get_metrics(selected_model)
        plots = model_dao.get_plots(selected_model)
        report = json.loads(model_dao.get_report(selected_model)["report"])
    except Exception as e:
        logger.error(f"Error fetching model data for {selected_model}: {str(e)}", exc_info=True)
        flash(f"Error retrieving information for {selected_model}.", "danger")
        metrics, plots, report = {}, {}, {}

    builder = ReportBuilder()
    director = ReportDirector(builder)
    model_report = director.build_model_report(metrics, plots, report)

    metrics_content = next((section["content"] for section in model_report.get_sections() if section["title"] == "Model Metadata"), "")
    plots_content = next((section["content"] for section in model_report.get_sections() if section["title"] == "Model Plots"), "")
    report_content = next((section["content"] for section in model_report.get_sections() if section["title"] == "Model Report"), "")

    return render_template(
        "models.html",
        models=models,
        selected_model=selected_model,
        metrics=metrics_content,
        plots=plots_content,
        report=report_content,
        form=form,
        page_name="models"
    )


@main.route("/admin", methods=["GET", "POST"])
@login_required
@limiter.limit("20 per minute")
@requires_role('admin')
def admin():
    """Retrieves a list of all unapproved users."""
    form = CSRFProtectionForm()
    if request.method == "POST":
        if not form.validate_on_submit():
            flash("CSRF token validation failed", "error")
            return redirect(url_for("main.admin"))

    try:
        users = fetch_all_users()
        pending_users = fetch_pending_approvals()
    except ValueError as e:
        flash(f"Error fetching pending approvals: {str(e)}", "admin")
        pending_users = []

    return render_template(
        "admin.html",
        users=users,
        form=form,
        pending_users=pending_users,
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
        page_name="admin"
    )


@main.route("/approve/<user_id>", methods=["POST"])
@login_required
@limiter.limit("5 per minute")
@requires_role("admin")
def approve_user_route(user_id):
    """Approves the user from the admin page and grants them access to the application."""
    form = CSRFProtectionForm()
    if not form.validate_on_submit():
        flash("CSRF token validation failed", "error")
        return redirect(url_for("main.admin"))
    
    try:
        result = approve_user(user_id)
        flash(result["message"], "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("main.admin"))


@main.route("/reject/<user_id>", methods=["POST"])
@login_required
@limiter.limit("5 per minute")
@requires_role("admin")
def reject_user_route(user_id):
    """Rejects and removes user from the admin page."""
    form = CSRFProtectionForm()
    if not form.validate_on_submit():
        flash("CSRF token validation failed", "error")
        return redirect(url_for("main.admin"))
    
    try:
        result = reject_user(user_id)
        flash(result["message"], "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("main.admin"))


@main.route("/rate_limit_exceeded")
@login_required
def rate_limit_exceeded():
    """Serves the rate limit exceeded page."""
    return render_template("errors/rate_limit_exceeded.html", session=session.get("user"))