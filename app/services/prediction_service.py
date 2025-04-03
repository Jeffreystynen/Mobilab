import logging
from app.helpers.input_params_helper import extract_form_features, map_features, process_h2o_contributions
from app.services.database_service import get_all_models
from app.services.api_client import APIClient

logger = logging.getLogger(__name__)

def handle_prediction(features, selected_model):
    """
    Handles the prediction process, including feature extraction and result processing.
    """
    try:
        # If features are passed as a list, map them directly
        if isinstance(features, list):
            mapped_features = map_features(features)
        else:
            # Otherwise, extract features from the form
            features = extract_form_features(features)
            mapped_features = map_features(features)

        # Return processed features and mapped features
        return {
            "success": True,
            "features": features,
            "mapped_features": mapped_features
        }
    except Exception as e:
        logger.error("Error during feature processing", exc_info=True)
        return {"success": False, "error": f"Error processing features: {str(e)}"}


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