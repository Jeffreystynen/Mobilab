from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from functools import wraps
import requests
from .form import PredictionForm
from .input_params import *
from app import oauth


main = Blueprint('main', __name__)  # Use 'main' instead of 'app'

# Register Auth0 OAuth
auth0 = oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:  # If user is not in session (not logged in)
              return login()  # Redirect to login page
        return f(*args, **kwargs)
    return decorated_function

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
    shap_image_path = None
    prediction_values = None

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

                shap_image_path = process_shap_values(shap_values=data.get("shap_values"), features=features)
                
                session['shap_image_path'] = shap_image_path
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
        shap_image_path=shap_image_path,
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )


@main.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    shap_image_path = session.get("shap_image_path", None)
    prediction_values = session.get("prediction_values", None)
    return render_template(
        "dashboard.html",
        session=session.get("user"),
        shap_image_path=shap_image_path,
        prediction_values=prediction_values,
        pretty=json.dumps(session.get("user"), indent=4),
    )
