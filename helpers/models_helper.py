import requests

def fetch_json(url):
    """Fetch JSON data from the given URL; return None if request fails."""
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None


def get_models():
    return fetch_json("http://127.0.0.1:5001/models") or []

def get_feature_mapping():
    return fetch_json("http://127.0.0.1:5001/feature-mapping") or {}

def get_metrics():
    return fetch_json("http://127.0.0.1:5001/metrics") or {}

def get_plots():
    return fetch_json("http://127.0.0.1:5001/plots") or {}
