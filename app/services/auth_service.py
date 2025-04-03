from app.helpers.auth0_helper import (
    get_management_api_token,
    get_pending_approvals,
    update_user_approval,
    delete_user,
)
from flask import session
import logging
import requests
from dotenv import load_dotenv
import os


load_dotenv() 
logger = logging.getLogger(__name__)


def fetch_all_users():
    """
    Fetch all approved users from Auth0 and include their roles from the Management API.
    """
    try:
        # Get the Management API token
        token = get_management_api_token()

        # Define the Auth0 Management API endpoints
        domain = os.getenv("AUTH0_DOMAIN")
        query = 'app_metadata.approved:true'
        users_url = f"https://{domain}/api/v2/users?q={query}&search_engine=v3"
        roles_url = f"https://{domain}/api/v2/roles"

        # Fetch all users
        headers = {"Authorization": f"Bearer {token}"}
        users_response = requests.get(users_url, headers=headers)
        users_response.raise_for_status()
        users = users_response.json()

        # Fetch all roles
        roles_response = requests.get(roles_url, headers=headers)
        roles_response.raise_for_status()
        roles = roles_response.json()

        # Create a mapping of role IDs to role names
        role_mapping = {role["id"]: role["name"] for role in roles}
        # Process the response to include only relevant fields
        processed_users = []
        for user in users:
            # Fetch roles for the user
            user_roles_url = f"https://{domain}/api/v2/users/{user['user_id']}/roles"
            user_roles_response = requests.get(user_roles_url, headers=headers)
            user_roles_response.raise_for_status()
            user_roles = user_roles_response.json()

            # Map role IDs to role names
            user_role_names = user_roles[0]['name'] if user_roles else []

            # Add the user with their roles
            processed_users.append({
                "user_id": user.get("user_id"),
                "email": user.get("email"),
                "name": user.get("name"),
                "role": user_role_names,
            })
        return processed_users
    except requests.RequestException as e:
        logger.error(f"Error fetching all users: {str(e)}")
        raise ValueError("Failed to fetch all users.")


def fetch_pending_approvals():
    """
    Fetch and process pending approvals from Auth0.
    """
    try:
        pending_users = get_pending_approvals()
        if not pending_users:
            logger.info("No pending approvals found.")
            return []
        return pending_users
    except Exception as e:
        logger.error(f"Error fetching pending approvals: {str(e)}")
        raise ValueError("Failed to fetch pending approvals.")


def approve_user(user_id):
    """
    Approve a user by updating their approval status in Auth0.
    """
    try:
        update_user_approval(user_id, True)
        logger.info(f"User approved: {user_id}")
        return {"success": True, "message": "User approved successfully."}
    except Exception as e:
        logger.error(f"Error approving user {user_id}: {str(e)}")
        raise ValueError(f"Failed to approve user: {str(e)}")


def reject_user(user_id):
    """
    Reject a user by updating their approval status in Auth0.
    """
    try:
        update_user_approval(user_id, False)
        delete_user(user_id)
        logger.info(f"User rejected: {user_id}")
        return {"success": True, "message": "User rejected successfully."}
    except Exception as e:
        logger.error(f"Error rejecting user {user_id}: {str(e)}")
        raise ValueError(f"Failed to reject user: {str(e)}")


def handle_auth_callback(token):
    """
    Handle the Auth0 callback by validating the token and checking user approval status.
    """
    try:
        # Validate nonce
        nonce = session.get("nonce")
        if not nonce:
            logger.error("Nonce is missing from the session.")
            raise ValueError("Invalid session state: missing nonce.")

        # Fetch user info from Auth0
        userinfo = get_user_info(token["access_token"])
        logger.debug(f"User info retrieved: {userinfo}")

        # Check if the user is approved
        approved = userinfo.get("https://mobilab.demo.app.com/approved", False)
        if not approved:
            logger.warning(f"User {userinfo.get('sub')} is not approved.")
            raise ValueError("User is not approved.")

        # Store the user info in the session
        session["user"] = userinfo
        logger.info(f"User {userinfo.get('sub')} logged in successfully.")
        return {"success": True, "message": "User logged in successfully."}
    except KeyError as e:
        logger.error(f"Missing key in token or user info: {str(e)}")
        raise ValueError("Invalid token or user info.")
    except Exception as e:
        logger.error(f"Error handling Auth0 callback: {str(e)}")
        raise ValueError(f"Failed to handle Auth0 callback: {str(e)}")


def get_user_info(access_token):
    """Fetch user info from Auth0 using the access token."""
    try:
        response = requests.get(
            f"https://{os.getenv('AUTH0_DOMAIN')}/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise ValueError(f"Failed to fetch user info: {str(e)}")