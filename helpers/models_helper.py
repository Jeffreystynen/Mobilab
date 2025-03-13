import requests

def fetch_json(url):
    """Fetch JSON data from the given URL; return None if request fails."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def get_models():
    return fetch_json("http://127.0.0.1:5001/models") or []

def get_feature_mapping(model_name="xgboost"):
    return fetch_json(f"http://127.0.0.1:5001/feature-mapping?model={model_name}") or {}

def get_metrics(model_name="xgboost"):
    return fetch_json(f"http://127.0.0.1:5001/metrics?model={model_name}") or {}

def get_plots(model_name="xgboost"):
    return fetch_json(f"http://127.0.0.1:5001/plots?model={model_name}") or {}
