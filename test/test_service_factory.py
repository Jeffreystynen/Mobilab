import unittest
from app.factories.service_factory import ServiceFactory
from app.services.feature_service import FeatureService
from app.services.prediction_service import PredictionService
from app.dao.model_dao import ModelDAO

class TestServiceFactory(unittest.TestCase):
    def test_create_model_dao(self):
        model_dao = ServiceFactory.create_model_dao()
        self.assertIsInstance(model_dao, ModelDAO)

    def test_create_feature_service(self):
        feature_service = ServiceFactory.create_feature_service()
        self.assertIsInstance(feature_service, FeatureService)

    def test_create_prediction_service(self):
        prediction_service = ServiceFactory.create_prediction_service()
        self.assertIsInstance(prediction_service, PredictionService)

if __name__ == "__main__":
    unittest.main()