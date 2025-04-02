from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
import requests
from .form import PredictionForm
from app.helpers.input_params_helper import extract_form_features, map_features
from app import oauth
from app.helpers.routes_helper import login_required, requires_role
from app.helpers.manage_models_helper import process_zip_file, send_model_to_api
from app.services.auth_service import (
    fetch_pending_approvals,
    approve_user,
    reject_user,
    remove_user,
    handle_auth_callback,
)
from app.services.database_service import get_all_models, get_model_metrics, get_model_plots, get_model_report
import secrets
import logging


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
def input_params():
    """
    Handles model interaction using a form. Sends the form parameters to the selected model for inference 
    (default is xgboost), retrieves the model's prediction and LIME plot, and stores these in the session.
    """
    prediction = None
    lime_image_path = None
    try:
        models_response = requests.get("http://127.0.0.1:5000/api/models")
        if models_response.status_code == 200:
            models = models_response.json()
        else:
            models = []
    except Exception as e:
        logger.warning("Failed to retrieve models", exc_info=True)
        models = []

    form = PredictionForm(request.form)
    if request.method == "POST" and form.validate():
        features = extract_form_features(form)
        session['prediction_values'] = map_features(features)
        selected_model = request.form.get("model", "xgboost").lower()
        payload = {
            "features": features,
            "model": selected_model
        }
        try:
            # Adjust the URL if needed (use the container name if on the same Docker network)
            response = requests.post("http://127.0.0.1:5000/api/predict", json=payload)
            if response.status_code == 200:
                logger.info("Prediction made")
                data = response.json()
                prediction = data.get("prediction")
                lime_image_path = data.get("lime_image_path")
                session['lime_explanation'] = data.get("lime_explanation")
                session['prediction'] = prediction
                session['lime_image_path'] = lime_image_path
            else:
                logger.warning("Prediction API error")
                flash("Prediction API error: " + response.text, "input_params")
        except Exception as e:
            logger.warning("Prediction API error", exc_info=True)
            flash("Error contacting prediction API: " + str(e), "input_params")
    elif request.method == "POST" and not form.validate():
        error_messages = "; ".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()])
        logger.info("Form error", exc_info=True)
        flash(f"The form contains errors: {error_messages}", "input_params")

    return render_template(
        "input_params.html",
        form=form,
        prediction=prediction,
        lime_image_path=lime_image_path,
        models=models,
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
        page_name = "input_params"
    )


@main.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    """Serves LIME plot and parameters used to make predictions from the last prediction."""
    lime_image_path = session.get("lime_image_path", None)
    prediction_values = session.get("prediction_values", None)
    lime_explanation = session.get("lime_explanation", None)
    return render_template(
        "dashboard.html",
        session=session.get("user"),
        lime_image_path=lime_image_path,
        prediction_values=prediction_values,
        lime_explanation=lime_explanation,
        pretty=json.dumps(session.get("user"), indent=4),
    )


@main.route("/models", methods=["GET", "POST"])
@login_required
def models():
    """
    Serves statistics and plots about the served model, including accuracy, precision, recall, training shape,
    ROC curve, P/R curve, and SHAP summary plot.
    """
    metrics = {}
    plots = {}

    # Fetch list of available models from the database service
    try:
        models = get_all_models()
    except ValueError as e:
        flash(f"Error fetching models: {str(e)}", "models")
        models = []

    selected_model = None
    if request.method == "POST":
        selected_model = request.form.get("model")
    
    # If no model is selected, default to the first model in the list
    if not selected_model:
        selected_model = models[0] if models else "No models available"

    try:
        # Fetch metrics and plots for the selected model
        metrics = get_model_metrics(selected_model)
        plots = get_model_plots(selected_model)
        report = get_model_report(selected_model)
        if "trainingShape" in metrics:
            metrics["trainingShape"] = json.loads(metrics["trainingShape"])
  
        print(metrics)
    except ValueError as e:
        flash(f"Error retrieving information for {selected_model}: {str(e)}", "models")
    print(models)
    return render_template(
        "models.html",
        models=models,
        selected_model=selected_model,
        metrics=metrics,
        plots=plots,
        report=report,
        page_name="models"
    )


@main.route("/manage models")
@login_required
@requires_role("admin")
def manage_models():
    try:
        models_response = requests.get("http://127.0.0.1:5000/api/models")
        if models_response.status_code == 200:
            models = models_response.json()
        else:
            models = []
    except Exception as e:
        models = []
    return render_template(
            "manage_models.html",
            models=models,
            session=session.get("user"),
            pretty=json.dumps(session.get("user"), indent=4),
            page_name="upload_model"
        )


@main.route("/upload_model", methods=["POST"])
@login_required
@requires_role("admin")
def upload_model():
    model_name = request.form.get("modelName")
    if not model_name:
        flash("Please provide a model name.", "upload_model")
        return redirect(url_for("main.manage_models"))

    if 'modelFile' not in request.files:
        flash("No file uploaded, please upload a .zip file", "upload_model")
        return redirect(url_for("main.manage_models"))
    
    file = request.files['modelFile']
    
    # If no file is selected, flash an error
    if file.filename == '':
        flash("No file selected", "upload_model")
        return redirect(url_for("main.manage_models"))
    
    try:
        zip_path = process_zip_file(file, model_name)
        response = send_model_to_api(zip_path, model_name)
        if response.status_code != 200:
            flash("Error uploading model: " + response.text, "upload_model")
            logger.warning(f"Failed to upload model: {model_name}")
        else:
            logger.info(f"Model uploaded: {model_name}")
            flash("Model uploaded successfully!", "upload_model")
    except Exception as e:
        logger.warning(f"Failed to upload model: {model_name}")
        flash("An error occurred please try again: ", "upload_model")
    
    return redirect(url_for("main.manage_models"))


@main.route("/remove_model", methods=["POST"])
@login_required
@requires_role("admin")
def remove_model():
    model_name = request.form.get('model_name')
    try:
        response = requests.delete(f"http://127.0.0.1:5000/api/delete_model/{model_name}")
        if response.status_code != 200:
            logger.warning(f"Failed to delete model: {model_name}")
            flash("Error, could not delete model: " + response.text, "upload_model")
        else:
            logger.warning(f"Model deleted: {model_name}")
            flash("Model deleted!", "upload_model")
    except Exception as e:
        logger.warning(f"Failed to delete model: {model_name}")
        flash("An error occurred please try again: ", "upload_model")
    return redirect(url_for('main.manage_models'))


@main.route("/admin")
@login_required
@requires_role('admin')
def admin():
    """Retrieves a list of all unapproved users."""
    try:
        pending_users = fetch_pending_approvals()
    except ValueError as e:
        flash(f"Error fetching pending approvals: {str(e)}", "admin")
        pending_users = []
    return render_template(
        "admin.html",
        pending_users=pending_users,
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
        page_name="admin"
    )


@main.route("/approve/<user_id>", methods=["POST"])
@login_required
@requires_role("admin")
def approve_user_route(user_id):
    """Approves the user from the admin page and grants them access to the application."""
    try:
        result = approve_user(user_id)
        flash(result["message"], "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("main.admin"))


@main.route("/reject/<user_id>", methods=["POST"])
@login_required
@requires_role("admin")
def reject_user_route(user_id):
    """Rejects and removes user from the admin page."""
    try:
        result = reject_user(user_id)
        flash(result["message"], "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("main.admin"))


@main.route("/delete/<user_id>", methods=["DELETE"])
@login_required
@requires_role("admin")
def delete_user_route(user_id):
    """Deletes a user from Auth0."""
    try:
        result = remove_user(user_id)
        flash(result["message"], "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("main.admin"))