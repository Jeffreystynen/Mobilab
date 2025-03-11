from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from functools import wraps
import requests
from .form import PredictionForm
from .input_params_helper import *
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


def requires_role(role):
    """Custom decorator to check for user roles in the JWT token."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = session.get('user', {}).get('id_token', '')
            
            if not token:
                flash("You need to log in first", "danger")
                return redirect(url_for('main.login'))

            try:
                decoded_token = json.loads(token)
                roles = decoded_token.get('https://yourapp.com/roles', [])

                if role not in roles:
                    flash("You don't have permission to access this page.", "danger")
                    return redirect(url_for('main.index'))
                
            except Exception as e:
                flash(f"Error: {str(e)}", "danger")
                return redirect(url_for('main.index'))

            return f(*args, **kwargs)

        return wrapper
    return decorator


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
    print(token)
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


@main.route("/models", methods=["GET", "POST"])
@login_required
@requires_role('admin')
def models():
    # Fetch list of available models
    models_response = requests.get("http://127.0.0.1:5001/models")
    models = models_response.json() if models_response.status_code == 200 else []

    # Fetch feature mappings
    feature_mapping_response = requests.get("http://127.0.0.1:5001/feature-mapping")
    feature_mapping = feature_mapping_response.json() if feature_mapping_response.status_code == 200 else {}

    # Fetch model metrics
    metrics_response = requests.get("http://127.0.0.1:5001/metrics")
    metrics = metrics_response.json() if metrics_response.status_code == 200 else {}

    # Fetch all plots
    plots_response = requests.get("http://127.0.0.1:5001/plots")
    plots = plots_response.json() if plots_response.status_code == 200 else {}

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


# @main.route("/admin")
# @roles_required("admin")
# def admin_dashboard():
#     return "Welcome, Admin!"