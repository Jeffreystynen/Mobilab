from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from app import oauth
from functools import wraps
import requests
import matplotlib.pyplot as plt
import shap
import io
import base64
import numpy as np
import pandas as pd
import tempfile
import os
from .form import PredictionForm 

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

# TODO form only validated when non default values are selected for the select boxes
@main.route("/input", methods=["GET", "POST"])
@login_required
def input_params():
    prediction = None
    shap_values = None
    shap_image_path = None
    prediction_values = None

    form = PredictionForm(request.form)
    print('start')
    if request.method == "POST":
        print("there")
        if form.validate():
            print("here")
            # Extract features from form input
            features = [
                float(form.age.data),
                float(form.sex.data),
                float(form.chest_pain_type.data),
                float(form.resting_blood_pressure.data),
                float(form.serum_cholesterol.data),
                float(form.fasting_blood_sugar.data),
                float(form.resting_electrocardiographic.data),
                float(form.max_heart_rate.data),
                float(form.exercise_induced_angina.data),
                float(form.oldpeak.data),
                float(form.slope_of_peak_st_segment.data),
                float(form.num_major_vessels.data),
                float(form.thal.data),
            ]
            session['prediction_values'] = {
                'age': features[0],
                'sex': features[1],
                'chest_pain_type': features[2],
                'resting_blood_pressure': features[3],
                'serum_cholesterol': features[4],
                'fasting_blood_sugar': features[5],
                'resting_electrocardiographic': features[6],
                'max_heart_rate': features[7],
                'exercise_induced_angina': features[8],
                'oldpeak': features[9],
                'slope_of_peak_st_segment': features[10],
                'num_major_vessels': features[11],
                'thal': features[12]
            }
            

            # Send POST request to API with features
            api_url = "http://127.0.0.1:5001/predict"
            response = requests.post(
                api_url, 
                json={"features": features}
            )
            
            if response.status_code == 200:
                data = response.json()
                prediction = data.get("prediction")
                shap_values = data.get("shap_values")

                # Convert SHAP values to a DataFrame
                shap_values_list = list(shap_values.values())
                feature_names = list(shap_values.keys())
                
                # Convert to numpy array
                shap_values_array = np.array(shap_values_list).reshape(1, -1)

                # Now create a DataFrame for SHAP values
                shap_df = pd.DataFrame(shap_values_array, columns=feature_names)

                # Plot SHAP summary plot
                fig = plt.figure(figsize=(8, 6))
                shap.summary_plot(shap_df.values, features, feature_names=feature_names, show=False)
                shap_image_filename = "shap_plot.png"
                shap_image_path = os.path.join("static", "shap_plots", shap_image_filename)

                # Save plot as a static file in the static/shap_plots directory
                plt.savefig(shap_image_path)
                plt.close(fig)

                # Store the SHAP plot path in the session for later use
                session['shap_image_path'] = shap_image_path
                session['prediction'] = prediction
            else:
                prediction = "Error: Unable to get prediction."
        else:
            print("invalid")
            print(form.errors)
            print(form.data)
            if request.method == "POST":
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
    print(prediction_values)
    return render_template(
        "dashboard.html",
        session=session.get("user"),
        shap_image_path=shap_image_path,
        prediction_values=prediction_values,
        pretty=json.dumps(session.get("user"), indent=4),
    )
