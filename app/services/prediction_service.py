import logging
from app.helpers.input_params_helper import (
    extract_form_features, 
    process_h2o_contributions, 
    validate_and_map_features
)
from app.services.api_client import APIClient

logger = logging.getLogger(__name__)


def make_prediction(features, selected_model):
    """
    Makes a prediction using the external API directly.
    
    Args:
        features (dict): Dictionary of features
        selected_model (str): Name of the model to use
    
    Returns:
        dict: Prediction results including prediction value and contributions
    """
    try:
        # Call the external prediction API directly
        api_url = "http://127.0.0.1:5001/predict"
        response = APIClient.post(
            api_url, 
            json={"features": features, "model": selected_model}
        )

        if "error" in response:
            raise ValueError(response["error"])

        return response
    except Exception as e:
        logger.error("Error making prediction", exc_info=True)
        raise ValueError(f"Prediction failed: {str(e)}")


def process_prediction_request(form, selected_model):
    """
    Processes the entire prediction workflow from form data to final results.
    
    Args:
        form (FlaskForm): The submitted form with prediction inputs
        selected_model (str): Name of the model to use
    
    Returns:
        dict: Contains prediction results and processed contributions
    """
    try:
        # Extract and validate features
        features = extract_form_features(form, selected_model)
        
        # Make prediction using external API
        result = make_prediction(features, selected_model)
        
        # Process contributions
        contributions_image_path, explanation_text = process_h2o_contributions(
            result,
            features.keys()
        )
        
        # Return all processed results
        return {
            "success": True,
            "prediction": result["prediction"],
            "contributions": result.get("contributions", {}),
            "contributions_image_path": contributions_image_path,
            "explanation_text": explanation_text,
            "features": features
        }
    except ValueError as e:
        logger.error("Error processing prediction request", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }