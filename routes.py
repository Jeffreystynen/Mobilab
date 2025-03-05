from flask import Blueprint, render_template, request, redirect, url_for, session
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
from app import oauth
from functools import wraps

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
    if request.method == "POST":
        param1 = request.form["param1"]
        param2 = request.form["param2"]
        # Placeholder prediction
        prediction = f"Prediction for {param1} and {param2}"

    return render_template(
        "input_params.html",
        prediction=prediction,
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )


@main.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    return render_template(
        "dashboard.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )