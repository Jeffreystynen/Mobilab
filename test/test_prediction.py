import unittest
from unittest.mock import patch, MagicMock
from app.helpers.input_params_helper import validate_and_map_features, extract_form_features
from app import create_app
import json
import re


class TestPrediction(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch("app.helpers.input_params_helper.get_feature_mapping")
    def test_validate_and_map_features_valid_input(self, mock_get_feature_mapping):
        """Test that feature mapping correctly validates and reorders input features."""
        input_features = {
            "age": 63,
            "sex": 1,
            "chest_pain_type": 3,
            "resting_blood_pressure": 145,
            "serum_cholesterol": 233,
            "fasting_blood_sugar": 1,
            "resting_electrocardiographic": 0,
            "max_heart_rate": 150,
            "exercise_induced_angina": 0,
            "oldpeak": 2.3,
            "slope_of_peak_st_segment": 0,
            "num_major_vessels": 0,
            "thal": 1,
        }
        feature_mapping = {
            "0": "age",
            "1": "sex",
            "2": "chest_pain_type",
            "3": "resting_blood_pressure",
            "4": "serum_cholesterol",
            "5": "fasting_blood_sugar",
            "6": "resting_electrocardiographic",
            "7": "max_heart_rate",
            "8": "exercise_induced_angina",
            "9": "oldpeak",
            "10": "slope_of_peak_st_segment",
            "11": "num_major_vessels",
            "12": "thal",
        }
        mock_get_feature_mapping.return_value = [{"featureMapping": json.dumps(feature_mapping)}]

        ordered_features = validate_and_map_features(input_features, "test_model")
        self.assertEqual(ordered_features, [63, 1, 3, 145, 233, 1, 0, 150, 0, 2.3, 0, 0, 1])

    @patch("app.helpers.input_params_helper.get_feature_mapping")
    def test_validate_and_map_features_missing_features(self, mock_get_feature_mapping):
        """Test that feature mapping raises an error for missing features."""
        input_features = {
            "age": 63,
            "sex": 1,
            "chest_pain_type": 3,
            # Missing "resting_blood_pressure", "serum_cholesterol", etc.
        }
        feature_mapping = {
            "0": "age",
            "1": "sex",
            "2": "chest_pain_type",
            "3": "resting_blood_pressure",
            "4": "serum_cholesterol",
        }
        mock_get_feature_mapping.return_value = [{"featureMapping": json.dumps(feature_mapping)}]

        with self.assertRaises(ValueError) as context:
            validate_and_map_features(input_features, "test_model")
        self.assertIn("Missing required features", str(context.exception))

    @patch("app.helpers.input_params_helper.validate_and_map_features")
    @patch("requests.post")
    def test_input_route_prediction(self, mock_post, mock_validate_and_map_features):
        """Test the /input route for making a prediction."""
        # Mock the feature mapping
        mock_validate_and_map_features.return_value = [63, 1, 3, 145, 233, 1, 0, 150, 0, 2.3, 0, 0, 1]

        # Mock the external prediction API response
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {
            "prediction": "positive",
            "contributions": {"age": 0.5, "sex": -0.2},
            "contributions_image_path": "/path/to/image",
            "contributions_explanation": "Age contributes positively."
        })

        # Simulate a logged-in user
        with self.client as client:
            with client.session_transaction() as session:
                session['user'] = {
                    "https://mobilab.demo.app.com/roles": ["user"],  # Add roles if required
                    "email": "test@example.com"
                }

            # Simulate a GET request to fetch the CSRF token
            response = client.get('/input')
            self.assertEqual(response.status_code, 200)
            csrf_token = self.extract_csrf_token(response.data.decode())
            print(f"CSRF Token: {csrf_token}")
            # Simulate form submission with the CSRF token
            form_data = {
                "age": 63,
                "sex": 1,
                "chest_pain_type": 3,
                "resting_blood_pressure": 145,
                "serum_cholesterol": 233,
                "fasting_blood_sugar": 1,
                "resting_electrocardiographic": 0,
                "max_heart_rate": 150,
                "exercise_induced_angina": 0,
                "oldpeak": 2.3,
                "slope_of_peak_st_segment": 0,
                "num_major_vessels": 0,
                "thal": 1,
                "model": "DRF_1_AutoML_5_20250327_133650",
                "csrf_token": csrf_token,
            }
            response = client.post('/input', data=form_data)
            print(f"Response Data: {response.data.decode()}")
            # Assertions
            self.assertEqual(response.status_code, 200)
            response_data = response.json
            print(response_data)
            self.assertEqual(response_data["prediction"], "0" or "1")
            self.assertIn("contributions", response_data)
            self.assertIn("contributions_image_path", response_data)
            self.assertIn("contributions_explanation", response_data)

    
    def extract_csrf_token(self, html):
        """Helper function to extract CSRF token from rendered HTML."""
        import re
        match = re.search(r'<input [^>]*name="csrf_token" [^>]*value="([^"]+)"', html)
        if match:
            return match.group(1)
        else:
            # print("CSRF token not found in HTML.")
            return None

if __name__ == "__main__":
    unittest.main()