import logging
from app.services.feature_service import FeatureService
from app.services.api_client import APIClient

logger = logging.getLogger(__name__)


class PredictionService:
    """Service for handling prediction workflows."""

    def __init__(self, api_client: APIClient, feature_service: FeatureService):
        """
        Initialize PredictionService with required dependencies.

        Args:
            api_client (APIClient): Client for making API requests.
            feature_service (FeatureService): Service for handling feature-related operations.
        """
        self.api_client = api_client
        self.feature_service = feature_service

    def process_prediction_request(self, form, model_name: str) -> dict:
        """
        Process the entire prediction workflow.

        Args:
            form: Flask form containing input data.
            model_name: Name of the model to use.

        Returns:
            dict: Prediction results and processed contributions.
        """
        try:
            # Extract and validate features
            features = self.feature_service.extract_and_validate_features(form, model_name)

            # Make prediction
            prediction_result = self._make_prediction(features, model_name)

            # Process contributions
            contributions_path, explanation = self.feature_service.process_contributions(
                prediction_result, list(features.keys())
            )

            return {
                "success": True,
                "prediction": prediction_result["prediction"],
                "contributions": prediction_result.get("contributions", {}),
                "contributions_image_path": contributions_path,
                "explanation_text": explanation,
                "features": features,
            }
        except ValueError as e:
            logger.error("Error processing prediction request", exc_info=True)
            return {"success": False, "error": str(e)}

    def _make_prediction(self, features: dict, model_name: str) -> dict:
        """Make a prediction using the external API."""
        try:
            response = self.api_client.post(
                "http://127.0.0.1:5001/predict", json={"features": features, "model": model_name}
            )
            if "error" in response:
                raise ValueError(response["error"])
            return response
        except Exception as e:
            logger.error("Error making prediction", exc_info=True)
            raise ValueError(f"Prediction failed: {str(e)}")