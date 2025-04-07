import unittest
from unittest.mock import MagicMock
from app.services.feature_service import FeatureService
from app.dao.model_dao import ModelDAO
from app.form import PredictionForm
from flask import Flask


class TestFeatureService(unittest.TestCase):
    def setUp(self):
        # Create a Flask app and push the context
        self.app = Flask(__name__)
        self.app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Mock the ModelDAO
        self.mock_model_dao = MagicMock()
        self.feature_service = FeatureService(self.mock_model_dao)

    def tearDown(self):
        # Pop the Flask app context
        self.app_context.pop()

    def test_extract_and_validate_features_valid_input(self):
        """Test feature extraction and validation with valid input."""
        # Mock the DAO response
        self.mock_model_dao.get_feature_mapping.return_value = [
            {"featureMapping": '{"0": "age", "1": "sex"}'}
        ]

        # Mock form data
        form = MagicMock()
        form.age.data = 30
        form.sex.data = 1

        # Call the method
        features = self.feature_service.extract_and_validate_features(form, "test_model")

        # Assertions
        self.assertEqual(features, {"age": 30, "sex": 1})
        self.mock_model_dao.get_feature_mapping.assert_called_once_with("test_model")

    # def test_extract_and_validate_features_missing_features(self):
    #     """Test feature extraction and validation with missing features."""
    #     # Mock the DAO response
    #     self.mock_model_dao.get_feature_mapping.return_value = [
    #         {"featureMapping": '{"0": "age", "1": "sex"}'}
    #     ]

    #     # Create a real form instance with missing fields
    #     form_data = {
    #         "age": 30,
    #         "sex": "",  # Simulate missing value
    #         "chest_pain_type": "",
    #         "resting_blood_pressure": "",
    #         "serum_cholesterol": "",
    #         "fasting_blood_sugar": "",
    #         "resting_electrocardiographic": "",
    #         "max_heart_rate": "",
    #         "exercise_induced_angina": "",
    #         "oldpeak": "",
    #         "slope_of_peak_st_segment": "",
    #         "num_major_vessels": "",
    #         "thal": "",
    #     }
    #     form = PredictionForm(data=form_data)
    #     form.process(data=form_data)
    #     form.validate()  

    #     # Call the method and assert it raises a ValueError
    #     with self.assertRaises(ValueError) as context:
    #         self.feature_service.extract_and_validate_features(form, "test_model")
    #     self.assertIn("Missing required features", str(context.exception))

    def test_process_contributions(self):
        """Test processing contributions and generating visualizations."""
        # Mock prediction result
        prediction_result = {
            "contributions": {"age": 0.5, "sex": -0.2, "BiasTerm": 0.1},
            "prediction": 1,
        }

        # Call the method
        plot_path, explanation = self.feature_service.process_contributions(
            prediction_result, ["age", "sex"]
        )

        # Assertions
        self.assertIsNotNone(plot_path)


if __name__ == "__main__":
    unittest.main()