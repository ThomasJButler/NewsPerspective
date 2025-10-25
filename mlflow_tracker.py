"""
@author Tom Butler
@date 2025-10-25
@description MLflow tracking utilities for monitoring AI performance and operational metrics.
             Integrates with Azure AI Foundry for experiment tracking.
"""

import os
import mlflow
from dotenv import load_dotenv
from logger_config import setup_logger

load_dotenv()
logger = setup_logger("NewsPerspective.MLflow")


class MLflowTracker:
    """Manages MLflow experiment tracking for NewsPerspective."""

    def __init__(self):
        """Initialise MLflow tracker with Azure ML configuration."""
        self.enabled = os.getenv("MLFLOW_ENABLED", "false").lower() == "true"
        self.experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "NewsPerspective")
        self.tracking_uri = os.getenv("MLFLOW_TRACKING_URI", None)

        if not self.enabled:
            logger.info("MLflow tracking disabled")
            return

        # Set tracking URI if provided
        if self.tracking_uri:
            mlflow.set_tracking_uri(self.tracking_uri)
            logger.info(f"MLflow tracking URI set to: {self.tracking_uri}")

        # Set experiment name
        mlflow.set_experiment(self.experiment_name)
        logger.info(f"MLflow experiment set to: {self.experiment_name}")

    def start_run(self, run_name=None):
        """
        Start a new MLflow run.
        @param {str} run_name - Optional name for the run
        @return {object} MLflow run context manager or dummy context
        """
        if not self.enabled:
            return DummyContext()

        return mlflow.start_run(run_name=run_name)

    def log_params(self, params):
        """
        Log parameters to MLflow.
        @param {dict} params - Parameters to log
        """
        if not self.enabled:
            return

        try:
            for key, value in params.items():
                mlflow.log_param(key, value)
            logger.debug(f"Logged {len(params)} parameters to MLflow")
        except Exception as e:
            logger.error(f"Error logging parameters: {str(e)}")

    def log_metrics(self, metrics, step=None):
        """
        Log metrics to MLflow.
        @param {dict} metrics - Metrics to log
        @param {int} step - Optional step number for metric
        """
        if not self.enabled:
            return

        try:
            for key, value in metrics.items():
                if value is not None and isinstance(value, (int, float)):
                    mlflow.log_metric(key, value, step=step)
            logger.debug(f"Logged {len(metrics)} metrics to MLflow")
        except Exception as e:
            logger.error(f"Error logging metrics: {str(e)}")

    def log_artifact(self, artifact_path):
        """
        Log an artifact file to MLflow.
        @param {str} artifact_path - Path to artifact file
        """
        if not self.enabled:
            return

        try:
            mlflow.log_artifact(artifact_path)
            logger.debug(f"Logged artifact: {artifact_path}")
        except Exception as e:
            logger.error(f"Error logging artifact: {str(e)}")

    def log_text(self, text, artifact_file):
        """
        Log text content as an artifact.
        @param {str} text - Text content to log
        @param {str} artifact_file - Name of artifact file
        """
        if not self.enabled:
            return

        try:
            mlflow.log_text(text, artifact_file)
            logger.debug(f"Logged text artifact: {artifact_file}")
        except Exception as e:
            logger.error(f"Error logging text: {str(e)}")

    def log_dict(self, dictionary, artifact_file):
        """
        Log dictionary as JSON artifact.
        @param {dict} dictionary - Dictionary to log
        @param {str} artifact_file - Name of artifact file
        """
        if not self.enabled:
            return

        try:
            mlflow.log_dict(dictionary, artifact_file)
            logger.debug(f"Logged dict artifact: {artifact_file}")
        except Exception as e:
            logger.error(f"Error logging dictionary: {str(e)}")

    def set_tag(self, key, value):
        """
        Set a tag for the current run.
        @param {str} key - Tag key
        @param {str} value - Tag value
        """
        if not self.enabled:
            return

        try:
            mlflow.set_tag(key, value)
        except Exception as e:
            logger.error(f"Error setting tag: {str(e)}")

    def set_tags(self, tags):
        """
        Set multiple tags for the current run.
        @param {dict} tags - Tags dictionary
        """
        if not self.enabled:
            return

        try:
            mlflow.set_tags(tags)
            logger.debug(f"Set {len(tags)} tags")
        except Exception as e:
            logger.error(f"Error setting tags: {str(e)}")

    def end_run(self):
        """End the current MLflow run."""
        if not self.enabled:
            return

        try:
            mlflow.end_run()
            logger.info("MLflow run ended")
        except Exception as e:
            logger.error(f"Error ending run: {str(e)}")


class DummyContext:
    """Dummy context manager for when MLflow is disabled."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# Global instance
mlflow_tracker = MLflowTracker()
