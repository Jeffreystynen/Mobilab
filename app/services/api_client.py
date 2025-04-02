import requests
import logging

logger = logging.getLogger(__name__)

class APIClient:
    """
    A centralized client for making API requests.
    """

    @staticmethod
    def get(url, params=None, headers=None):
        """
        Sends a GET request to the specified URL.
        """
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"GET request to {url} failed: {str(e)}", exc_info=True)
            return {"error": str(e)}

    @staticmethod
    def post(url, json=None, headers=None, timeout=10):
        """
        Sends a POST request to the specified URL.
        """
        try:
            response = requests.post(url, json=json, headers=headers, timeout=timeout)
            response.raise_for_status()  # Raise an HTTPError for bad responses
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"POST request to {url} failed: {str(e)}", exc_info=True)
            return {"error": str(e)}