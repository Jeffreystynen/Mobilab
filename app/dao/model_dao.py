from app.dao.db import get_connection
import logging
import pymysql
from threading import local

logger = logging.getLogger(__name__)

class ModelDAO:
    """Data Access Object for model-related database operations."""

    def __init__(self):
        """
        Initialize ModelDAO with a thread-local database connection.
        """
        self.local = local()

    @property
    def db_connection(self):
        """
        Get the thread-local database connection. Reconnect if necessary.
        """
        if not hasattr(self.local, "connection") or not self.local.connection or not self.local.connection.open:
            self.local.connection = get_connection()
        return self.local.connection

    def get_models(self):
        """
        Fetch all available model names.

        Returns:
            list: A list of model names, or an empty list if the database is unavailable.
        """
        try:
            self.check_connection()
            if not self.db_connection:
                logger.warning("Database connection is unavailable. Attempting to reconnect...")
                self.reconnect()
                if not self.db_connection:
                    return []

            with self.db_connection.cursor() as cursor:
                sql = "SELECT name FROM Model"
                cursor.execute(sql)
                models = cursor.fetchall()
                return [model['name'] for model in models]
        except pymysql.err.OperationalError as e:
            logger.error(f"Lost connection to the database: {e}", exc_info=True)
            self.reconnect()
            return []
        except pymysql.MySQLError as e:
            logger.error(f"Error fetching models: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_models: {e}", exc_info=True)
            return []

    def get_metrics(self, model_name):
        """
        Fetch metrics for a specific model.

        Args:
            model_name (str): The name of the model.

        Returns:
            dict: A dictionary of model metrics, or an empty dictionary if an error occurs.
        """
        try:
            if not self.db_connection:
                logger.warning("Database connection is unavailable. Attempting to reconnect...")
                self.reconnect()
                if not self.db_connection:
                    return {}

            with self.db_connection.cursor() as cursor:
                sql = """
                    SELECT m.name, m.version, m.createdAt, met.accuracy, met.trainingShape
                    FROM Model m
                    JOIN Metric met ON m.modelId = met.modelId
                    WHERE m.name = %s
                """
                cursor.execute(sql, (model_name,))
                return cursor.fetchone() or {}
        except pymysql.err.OperationalError as e:
            logger.error(f"Lost connection to the database: {e}", exc_info=True)
            self.reconnect()
            return {}
        except pymysql.MySQLError as e:
            logger.error(f"Error fetching metrics for model '{model_name}': {e}", exc_info=True)
            return {}
        except Exception as e:
            logger.error(f"Unexpected error in get_metrics for model '{model_name}': {e}", exc_info=True)
            return {}

    def get_plots(self, model_name):
        """
        Fetch plots for a specific model.

        Args:
            model_name (str): The name of the model.

        Returns:
            dict: A dictionary of model plots, or an empty dictionary if an error occurs.
        """
        try:
            if not self.db_connection:
                logger.warning("Database connection is unavailable. Attempting to reconnect...")
                self.reconnect()
                if not self.db_connection:
                    return {}

            with self.db_connection.cursor() as cursor:
                sql = """
                    SELECT p.auc, p.aucpr, p.shap
                    FROM Model m
                    JOIN Plot p ON m.modelId = p.modelId
                    WHERE m.name = %s
                """
                cursor.execute(sql, (model_name,))
                return cursor.fetchone() or {}
        except pymysql.err.OperationalError as e:
            logger.error(f"Lost connection to the database: {e}", exc_info=True)
            self.reconnect()
            return {}
        except pymysql.MySQLError as e:
            logger.error(f"Error fetching plots for model '{model_name}': {e}", exc_info=True)
            return {}
        except Exception as e:
            logger.error(f"Unexpected error in get_plots for model '{model_name}': {e}", exc_info=True)
            return {}

    def get_report(self, model_name):
        """
        Fetch the report for a specific model.

        Args:
            model_name (str): The name of the model.

        Returns:
            dict: A dictionary containing the report, or an empty dictionary if an error occurs.
        """
        try:
            if not self.db_connection:
                logger.warning("Database connection is unavailable. Attempting to reconnect...")
                self.reconnect()
                if not self.db_connection:
                    return {}

            with self.db_connection.cursor() as cursor:
                sql = """
                    SELECT met.report
                    FROM Model m
                    JOIN Metric met ON m.modelId = met.modelId
                    WHERE m.name = %s
                """
                cursor.execute(sql, (model_name,))
                return cursor.fetchone() or {}
        except pymysql.err.OperationalError as e:
            logger.error(f"Lost connection to the database: {e}", exc_info=True)
            self.reconnect()
            return {}
        except pymysql.MySQLError as e:
            logger.error(f"Error fetching report for model '{model_name}': {e}", exc_info=True)
            return {}
        except Exception as e:
            logger.error(f"Unexpected error in get_report: {e}", exc_info=True)
            return {}

    def get_feature_mapping(self, model_name):
        """
        Fetch the feature mapping for a specific model.

        Args:
            model_name (str): The name of the model.

        Returns:
            dict: A dictionary containing the feature mapping.
        """
        try:
            self.check_connection()

            with self.db_connection.cursor() as cursor:
                sql = """
                    SELECT m.featureMapping
                    FROM Model m
                    WHERE m.name = %s
                """
                cursor.execute(sql, (model_name,))
                result = cursor.fetchall()
                return result
        except pymysql.err.OperationalError as e:
            logger.error(f"Lost connection to the database: {e}", exc_info=True)
            self.reconnect()
            return {}
        except pymysql.MySQLError as e:
            logger.error(f"Error fetching feature mapping for model '{model_name}': {e}", exc_info=True)
            return {}
        except Exception as e:
            logger.error(f"Unexpected error in get_feature_mapping for model '{model_name}': {e}", exc_info=True)
            return {}

    def reconnect(self):
        """
        Reconnect to the database and refresh the thread-local connection.
        """
        self.local.connection = get_connection()
        if self.local.connection:
            logger.info("Reconnected to the database successfully.")
        else:
            logger.error("Failed to reconnect to the database.")

    def check_connection(self):
        """
        Ensure the database connection is valid. Reconnect if necessary.
        """
        try:
            if not self.db_connection or not self.db_connection.open:
                logger.warning("Database connection is invalid or closed. Attempting to reconnect...")
                self.reconnect()
        except Exception as e:
            logger.error(f"Error while checking database connection: {e}", exc_info=True)
            self.reconnect()