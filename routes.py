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
import secrets


main = Blueprint('main', __name__)  # Use 'main' instead of 'app'

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
    return login()


@main.route("/login")
def login():
    nonce = secrets.token_urlsafe(16)
    session["nonce"] = nonce
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("main.callback", _external=True),
        nonce=nonce
    )


@main.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    nonce = session.get("nonce")
    userinfo = oauth.auth0.parse_id_token(token, nonce=nonce)
    
    # Check if the user is approved (using your custom claim)
    approved = userinfo.get("https://mobilab.demo.app.com/approved", False)
    if not approved:
        flash("Your account is pending admin approval. Please contact an administrator.", "warning")
        return redirect(url_for("main.pending_approval"))
    
    # Store the decoded user info directly in the session
    session["user"] = userinfo
    return redirect(url_for("main.input_params"))



@main.route("/logout")
def logout():
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
    return render_template("pending_approval.html")


@main.route("/input", methods=["GET", "POST"])
@login_required
def input_params():
    prediction = None
    lime_image_path = None

    # Fetch list of available models from the model-serving API
    try:
        models_response = requests.get("http://127.0.0.1:5001/models")
        if models_response.status_code == 200:
            models = models_response.json()
        else:
            models = []
            flash("Unable to fetch models.", "warning")
    except Exception as e:
        models = []
        flash(f"Error fetching models: {str(e)}", "danger")

    form = PredictionForm(request.form)
    if request.method == "POST":
        if form.validate():
            features = extract_form_features(form)
            session['prediction_values'] = map_features(features)

            # Get the selected model from the form; default to "xgboost"
            selected_model = request.form.get("model", "xgboost").lower()

            # Send features and model parameter to the prediction API
            response = get_prediction_from_api(features, model=selected_model)
            if response.status_code == 200:
                data = response.json()
                prediction = data.get("prediction")
                session['prediction'] = prediction

                # Process LIME values (assumed to return a base64-encoded image or file path)
                lime_image_path = process_lime_values(
                    lime_values=data.get("lime_values"),
                    prediction=prediction,
                    feature_names=features
                )
                session['lime_image_path'] = lime_image_path
                print("LIME image path:", session['lime_image_path'])
            else:
                prediction = "Error: Unable to get prediction."
                flash("Prediction API error.", "danger")
        else:
            print("Form errors:", form.errors)
            flash("There were errors in the form. Please check your input.", "danger")

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
    lime_image_path = session.get("lime_image_path", None)
    prediction_values = session.get("prediction_values", None)
    return render_template(
        "dashboard.html",
        session=session.get("user"),
        lime_image_path=lime_image_path,
        prediction_values=prediction_values,
        pretty=json.dumps(session.get("user"), indent=4),
    )


@main.route("/models", methods=["GET", "POST"])
@login_required
def models():
    selected_model = None
    if request.method == "POST":
        selected_model = request.form.get("model")
    # If no model is selected, default to "xgboost"
    if not selected_model:
        flash("No model selected. Please select a model.", "danger")

    # Fetch model-specific data using the selected model as a query parameter.
    models_list = get_models()
    feature_mapping = get_feature_mapping(selected_model)
    metrics = get_metrics(selected_model)
    plots = get_plots(selected_model)

    return render_template(
        "models.html",
        models=models_list,
        selected_model=selected_model,
        metrics=metrics,
        feature_mapping=feature_mapping,
        plots=plots,
    )


@main.route("/admin")
@login_required
@requires_role('admin')
def admin():
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
    try:
        delete_user(user_id)
        flash("User rejected successfully.", "success")
    except Exception as e:
        flash(f"Error rejecting user: {str(e)}", "danger")
    return redirect(url_for("main.admin"))