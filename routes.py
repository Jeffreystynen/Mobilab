from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from functools import wraps
import requests
from .form import PredictionForm
from app.helpers.input_params_helper import *
from app import oauth
import jwt
from app.helpers.routes_helper import *
from app.helpers.models_helper import *
from app.helpers.auth0_helper import get_pending_approvals, update_user_approval, delete_user
from app.helpers.manage_models_helper import *
import secrets
import zipfile
from .api import *


main = Blueprint('main', __name__)


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
    """Establishes access token and checks users approval status"""
    token = oauth.auth0.authorize_access_token()
    nonce = session.get("nonce")
    userinfo = oauth.auth0.parse_id_token(token, nonce=nonce)
    
    # Check if the user is approved
    approved = userinfo.get("https://mobilab.demo.app.com/approved", False)
    if not approved:
        flash("Your account is pending admin approval. Please contact an administrator.", "warning")
        return redirect(url_for("main.pending_approval"))
    
    # Store the decoded user info directly in the session
    session["user"] = userinfo
    return redirect(url_for("main.input_params"))



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
        models = []

    form = PredictionForm(request.form)
    if request.method == "POST" and form.validate():
        features = extract_form_features(form)
        selected_model = request.form.get("model", "xgboost").lower()
        payload = {
            "features": features,
            "model": selected_model
        }
        try:
            # Adjust the URL if needed (use the container name if on the same Docker network)
            response = requests.post("http://127.0.0.1:5000/api/predict", json=payload)
            print(response)
            if response.status_code == 200:
                data = response.json()
                prediction = data.get("prediction")
                lime_image_path = data.get("lime_image_path")
                # You can store these in session if needed or pass directly to the template
                session['prediction'] = prediction
                session['lime_image_path'] = lime_image_path
            else:
                flash("Prediction API error: " + response.text, "danger")
        except Exception as e:
            flash("Error contacting prediction API: " + str(e), "danger")

    return render_template(
        "input_params.html",
        form=form,
        prediction=prediction,
        lime_image_path=lime_image_path,
        models=models,
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4)
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
    metrics = None
    plots = None

    # Fetch list of available models from the API
    try:
        models_response = requests.get("http://127.0.0.1:5000/api/models")
        if models_response.status_code == 200:
            models = models_response.json()
        else:
            models = []
    except Exception as e:
        models = []

    selected_model = None
    if request.method == "POST":
        selected_model = request.form.get("model")
    
    # If no model is selected, default to "xgboost"
    if not selected_model:
        flash("No model selected. Please select a model.", "danger")
        selected_model = "xgboost"

    try:
        # Use selected_model to retrieve data from API
        response = requests.get(f"http://127.0.0.1:5000/api/models/{selected_model}")
        if response.status_code == 200:
            data = response.json()
            metrics = data.get("metrics")
            plots = data.get("plots")
        else:
            flash(f"Error retrieving information for {selected_model}.", "danger")
    except Exception as e:
        flash(f"No additional information found on {selected_model}.", "danger")

    return render_template(
        "models.html",
        models=models,
        selected_model=selected_model,
        metrics=metrics,
        plots=plots,
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
        )


@main.route("/upload_model", methods=["POST"])
@login_required
@requires_role("admin")
def upload_model():
    # Check if the post request has the file part

    model_name = request.form.get("modelName")
    if not model_name:
        flash("Please provide a model name.", "danger")
        return redirect(url_for("main.manage_models"))

    if 'modelFile' not in request.files:
        flash("No file uploaded, please upload a .zip file", "danger")
        return redirect(url_for("main.manage_models"))
    
    file = request.files['modelFile']
    
    # If no file is selected, flash an error
    if file.filename == '':
        flash("No file selected", "danger")
        return redirect(url_for("main.manage_models"))
    
    try:
        response = process_and_send_zip(uploaded_file=file, model_name=model_name)
        if response.status_code != 200:
            flash("Error uploading model: " + response.text, "danger")
        else:
            flash("Model uploaded successfully!", "success")
    except Exception as e:
        flash("An error occurred please try again: ")
    
    return redirect(url_for("main.manage_models"))


@main.route("/admin")
@login_required
@requires_role('admin')
def admin():
    """Retrieves a list of all unapproved users."""
    try:
        pending_users = get_pending_approvals()
    except Exception as e:
        flash(f"Error fetching pending approvals: {str(e)}", "danger")
        pending_users = []
    return render_template(
        "admin.html",
        pending_users=pending_users,
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )


@main.route("/approve/<user_id>", methods=["POST"])
@login_required
@requires_role("admin")
def approve_user(user_id):
    """Approves the user from the admin page and grants them access to the application."""
    try:
        update_user_approval(user_id, True)
        flash("User approved successfully.", "success")
    except Exception as e:
        flash(f"Error approving user: {str(e)}", "danger")
    return redirect(url_for("main.admin"))


@main.route("/reject/<user_id>", methods=["POST"])
@login_required
@requires_role("admin")
def reject_user(user_id):
    """Rejects and removes user from the admin page."""
    try:
        delete_user(user_id)
        flash("User rejected successfully.", "success")
    except Exception as e:
        flash(f"Error rejecting user: {str(e)}", "danger")
    return redirect(url_for("main.admin"))