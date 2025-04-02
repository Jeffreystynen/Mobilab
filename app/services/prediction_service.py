import logging
from app.helpers.input_params_helper import extract_form_features, map_features
from app.services.database_service import get_all_models
from app.services.api_client import APIClient

logger = logging.getLogger(__name__)

def handle_prediction(features, selected_model, api_url="http://127.0.0.1:5000/api/predict"):
    """
    Handles the prediction process, including feature extraction, API calls, and result processing.
    """
    try:
        # If features are passed as a list, map them directly
        if isinstance(features, list):
            mapped_features = map_features(features)
        else:
            # Otherwise, extract features from the form
            features = extract_form_features(features)
            mapped_features = map_features(features)

        # Prepare the payload for the prediction API
        payload = {
            "features": features,
            "model": selected_model
        }

        # Call the prediction API using APIClient
        response = APIClient.post(api_url, json=payload)

        if "error" not in response:
            return {
                "success": True,
                "prediction": response.get("prediction"),
                "contributions": response.get("contributions"),
                "contributions_image_path": response.get("contributions_image_path"),
                "contributions_explanation": response.get("contributions_explanation"),
                "mapped_features": mapped_features
            }
        else:
            return {"success": False, "error": response["error"]}
    except Exception as e:
        logger.error("Error during prediction", exc_info=True)
        return {"success": False, "error": f"Error contacting prediction API: {str(e)}"}


def fetch_models():
    """
    Fetches the list of available models from the API.
    """
    try:
        models = get_all_models()
        if not models:
            logger.info("No models found.")
            return []
        return models
    except Exception as e:
        logger.error("Error fetching models", exc_info=True)
        return []