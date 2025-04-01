import os
import requests

def get_management_api_token():
    """Retrieves the management api token from Auth0."""
    domain = os.getenv("AUTH0_DOMAIN")
    client_id = os.getenv("MGMT_API_CLIENT_ID")
    client_secret = os.getenv("MGMT_API_CLIENT_SECRET")
    audience = f"https://{domain}/api/v2/"
    token_url = f"https://{domain}/oauth/token"

    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": audience,
        "grant_type": "client_credentials"
    }

    response = requests.post(token_url, json=data)
    response.raise_for_status()  # Raise an error if the request fails
    token = response.json().get("access_token")
    return token


def get_pending_approvals():
    """
    Fetch users from Auth0 whose app_metadata.approved is false.
    Uses the Auth0 Management API with a query filter.
    """
    domain = os.getenv("AUTH0_DOMAIN")
    token = get_management_api_token()
    query = 'app_metadata.approved:false'
    url = f"https://{domain}/api/v2/users?q={query}&search_engine=v3"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def update_user_approval(user_id, approval_status):
    """Update a user's approval status via the Auth0 Management API based on the Auth0 user id."""
    domain = os.getenv("AUTH0_DOMAIN")
    token = get_management_api_token()
    url = f"https://{domain}/api/v2/users/{user_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "app_metadata": {"approved": approval_status}
    }
    response = requests.patch(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()


def delete_user(user_id):
    """Delete a user from Auth0 based on the Auth0 user id."""
    domain = os.getenv("AUTH0_DOMAIN")
    token = get_management_api_token()
    url = f"https://{domain}/api/v2/users/{user_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.delete(url, headers=headers)
    response.raise_for_status()  # Will raise an exception if the delete fails
    return response.json()


if __name__ == "__main__":
    token = get_management_api_token()
    pending = get_pending_approvals()
    print(json.dumps(pending, indent=4))