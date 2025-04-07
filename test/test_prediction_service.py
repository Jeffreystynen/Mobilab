import unittest
from unittest.mock import MagicMock, patch
from app.services.prediction_service import PredictionService
from app.services.feature_service import FeatureService
from app.services.api_client import APIClient


class TestPredictionService(unittest.TestCase):
    def setUp(self):
        # Mock dependencies
        self.mock_api_client = MagicMock()
        self.mock_feature_service = MagicMock()
        self.prediction_service = PredictionService(self.mock_api_client, self.mock_feature_service)

    def test_process_prediction_request_success(self):
        """Test processing a prediction request successfully."""
        # Mock feature extraction
        self.mock_feature_service.extract_and_validate_features.return_value = {"age": 30, "sex": 1}

        # Mock API response
        self.mock_api_client.post.return_value = {
            "prediction": 1,
            "contributions": {"age": 0.5, "sex": -0.2},
        }

        # Mock contribution processing
        self.mock_feature_service.process_contributions.return_value = (
            "/path/to/plot.png",
            "Age contributes positively.",
        )

        # Mock form
        form = MagicMock()

        # Call the method
        result = self.prediction_service.process_prediction_request(form, "test_model")

        # Assertions
        self.assertTrue(result["success"])
        self.assertEqual(result["prediction"], 1)
        self.assertIn("contributions_image_path", result)
        self.assertIn("explanation_text", result)

    def test_process_prediction_request_failure(self):
        """Test processing a prediction request with a failure."""
        # Mock feature extraction to raise an error
        self.mock_feature_service.extract_and_validate_features.side_effect = ValueError("Invalid features")

        # Mock form
        form = MagicMock()

        # Call the method
        result = self.prediction_service.process_prediction_request(form, "test_model")

        # Assertions
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Invalid features")


if __name__ == "__main__":
    unittest.main()