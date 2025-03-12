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
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("main.callback", _external=True)
    )


@main.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    id_token = token.get("id_token")
    if id_token:
        # Decode the id_token without verifying the signature (development only!)
        decoded_token = jwt.decode(id_token, options={"verify_signature": False})
        session["user"] = decoded_token
    else:
        session["user"] = token
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


@main.route("/input", methods=["GET", "POST"])
@login_required
def input_params():
    prediction = None
    shap_values = None
    lime_image_path = None
    prediction_values = None

    # Fetch list of available models
    models_response = requests.get("http://127.0.0.1:5001/models")
    models = models_response.json() if models_response.status_code == 200 else []

    form = PredictionForm(request.form)
    if request.method == "POST":
        if form.validate():

            features = extract_form_features(form)

            session['prediction_values'] = map_features(features)
            
            response = get_prediction_from_api(features)
            
            if response.status_code == 200:
                data = response.json()
                prediction = data.get("prediction")
                session['prediction'] = prediction

                # shap_image_path = process_shap_values(shap_values=data.get("shap_values"), features=features)
                # session['shap_image_path'] = shap_image_path
                lime_image_path = process_lime_values(lime_values=data.get("lime_values"), prediction=prediction, feature_names=features)         
                session['lime_image_path'] = lime_image_path
                print(session['lime_image_path'])
            else:
                prediction = "Error: Unable to get prediction."
        else:
            if request.method == "POST":
                print(form.errors)
                flash("There were errors in the form. Please check your input.", "danger")

    return render_template(
        "input_params.html",
        form=form,
        prediction=prediction,
        lime_image_path=lime_image_path,
        models=models,
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
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
    # Fetch data using helper functions
    models = get_models()
    feature_mapping = get_feature_mapping()
    metrics = get_metrics()
    plots = get_plots()

    selected_model = None
    selected_metrics = {}
    selected_feature_mapping = {}
    selected_plots = {}

    if request.method == "POST":
        selected_model = request.form.get("model")
        if selected_model:
            selected_metrics = metrics
            selected_feature_mapping = feature_mapping
            selected_plots = plots

    return render_template(
        "models.html",
        models=models,
        selected_model=selected_model,
        metrics=selected_metrics,
        feature_mapping=selected_feature_mapping,
        plots=selected_plots,
    )



@main.route("/admin")
@login_required
@requires_role('admin')
def admin():
    return render_template(
        "admin.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )