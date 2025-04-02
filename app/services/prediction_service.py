import requests
import logging
from app.helpers.input_params_helper import extract_form_features, map_features
from app.services.database_service import get_all_models

logger = logging.getLogger(__name__)

def handle_prediction(form, selected_model):
    """
    Handles the prediction process, including feature extraction, API calls, and result processing.
    """
    try:
        # Extract features from the form
        features = extract_form_features(form)
        mapped_features = map_features(features)

        # Prepare the payload for the prediction API
        payload = {
            "features": features,
            "model": selected_model
        }

        # Call the prediction API
        response = requests.post("http://127.0.0.1:5000/api/predict", json=payload)
        if response.status_code == 200:
            logger.info("Prediction made successfully")
            data = response.json()
            return {
                "success": True,
                "prediction": data.get("prediction"),
                "contributions_image_path": data.get("lime_image_path"),  # Update key name if needed
                "contributions_explanation": data.get("lime_explanation"),  # Update key name if needed
                "mapped_features": mapped_features
            }
        else:
            logger.warning("Prediction API error: " + response.text)
            return {"success": False, "error": "Prediction API error: " + response.text}
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