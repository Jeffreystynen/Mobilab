from app.services.feature_service import FeatureService
from app.services.prediction_service import PredictionService
from app.services.api_client import APIClient
from app.dao.model_dao import ModelDAO

class ServiceFactory:
    """Factory for creating services and DAOs."""

    @staticmethod
    def create_model_dao():
        """
        Create and return a ModelDAO instance.
        """
        return ModelDAO()

    @staticmethod
    def create_feature_service():
        """
        Create and return a FeatureService instance.
        """
        model_dao = ServiceFactory.create_model_dao()
        return FeatureService(model_dao)

    @staticmethod
    def create_prediction_service():
        """
        Create and return a PredictionService instance.
        """
        feature_service = ServiceFactory.create_feature_service()
        api_client = APIClient()
        return PredictionService(api_client, feature_service)