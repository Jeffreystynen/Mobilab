from app.dao.db import get_connection
import logging

logger = logging.getLogger(__name__)

class ModelDAO:
    """Data Access Object for model-related database operations."""

    def __init__(self, db_connection=None):
        """
        Initialize ModelDAO with a database connection.

        Args:
            db_connection: Optional database connection object.
        """
        self.db_connection = db_connection or get_connection()

    def get_models(self):
        """
        Fetch all available model names.

        Returns:
            list: A list of model names.

        Raises:
            Exception: If the database query fails.
        """
        try:
            with self.db_connection.cursor() as cursor:
                sql = "SELECT name FROM Model"
                cursor.execute(sql)
                models = cursor.fetchall()
                return [model['name'] for model in models]
        except Exception as e:
            logger.error("Error fetching models", exc_info=True)
            raise

    def get_metrics(self, model_name):
        """
        Fetch metrics for a specific model.

        Args:
            model_name (str): The name of the model.

        Returns:
            dict: A dictionary of model metrics.

        Raises:
            Exception: If the database query fails.
        """
        try:
            with self.db_connection.cursor() as cursor:
                sql = """
                    SELECT m.name, m.version, m.createdAt, met.accuracy, met.trainingShape
                    FROM Model m
                    JOIN Metric met ON m.modelId = met.modelId
                    WHERE m.name = %s
                """
                cursor.execute(sql, (model_name,))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error fetching metrics for model '{model_name}'", exc_info=True)
            raise

    def get_plots(self, model_name):
        """
        Fetch plots for a specific model.

        Args:
            model_name (str): The name of the model.

        Returns:
            dict: A dictionary of model plots.

        Raises:
            Exception: If the database query fails.
        """
        try:
            with self.db_connection.cursor() as cursor:
                sql = """
                    SELECT p.auc, p.aucpr, p.shap
                    FROM Model m
                    JOIN Plot p ON m.modelId = p.modelId
                    WHERE m.name = %s
                """
                cursor.execute(sql, (model_name,))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error fetching plots for model '{model_name}'", exc_info=True)
            raise

    def get_report(self, model_name):
        """
        Fetch the report for a specific model.

        Args:
            model_name (str): The name of the model.

        Returns:
            dict: A dictionary containing the report.

        Raises:
            Exception: If the database query fails.
        """
        try:
            with self.db_connection.cursor() as cursor:
                sql = """
                    SELECT met.report
                    FROM Model m
                    JOIN Metric met ON m.modelId = met.modelId
                    WHERE m.name = %s
                """
                cursor.execute(sql, (model_name,))
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error fetching report for model '{model_name}'", exc_info=True)
            raise

    def get_feature_mapping(self, model_name):
        """
        Fetch the feature mapping for a specific model.

        Args:
            model_name (str): The name of the model.

        Returns:
            dict: A dictionary containing the feature mapping.

        Raises:
            Exception: If the database query fails.
        """
        try:
            with self.db_connection.cursor() as cursor:
                sql = """
                    SELECT m.featureMapping
                    FROM Model m
                    WHERE m.name = %s
                """
                cursor.execute(sql, (model_name,))
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error fetching feature mapping for model '{model_name}'", exc_info=True)
            raise