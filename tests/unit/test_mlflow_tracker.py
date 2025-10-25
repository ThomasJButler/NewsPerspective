"""
@author Tom Butler
@date 2025-10-25
@description Unit tests for MLflow tracking integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from mlflow_tracker import MLflowTracker, DummyContext


class TestMLflowTracker:
    """Test MLflow tracking functionality."""

    def test_tracker_disabled_by_default(self, monkeypatch):
        """Test tracker is disabled when MLFLOW_ENABLED is false."""
        monkeypatch.setenv("MLFLOW_ENABLED", "false")
        tracker = MLflowTracker()
        assert tracker.enabled is False

    def test_tracker_enabled_when_configured(self, monkeypatch):
        """Test tracker enables when properly configured."""
        monkeypatch.setenv("MLFLOW_ENABLED", "true")
        monkeypatch.setenv("MLFLOW_TRACKING_URI", "http://localhost:5000")

        with patch('mlflow_tracker.mlflow'):
            tracker = MLflowTracker()
            assert tracker.enabled is True

    @patch('mlflow_tracker.mlflow')
    def test_start_run_when_enabled(self, mock_mlflow, monkeypatch):
        """Test start_run creates MLflow run when enabled."""
        monkeypatch.setenv("MLFLOW_ENABLED", "true")
        tracker = MLflowTracker()

        tracker.start_run(run_name="test_run")
        mock_mlflow.start_run.assert_called_once_with(run_name="test_run")

    def test_start_run_returns_dummy_when_disabled(self, monkeypatch):
        """Test start_run returns DummyContext when disabled."""
        monkeypatch.setenv("MLFLOW_ENABLED", "false")
        tracker = MLflowTracker()

        context = tracker.start_run()
        assert isinstance(context, DummyContext)

    @patch('mlflow_tracker.mlflow')
    def test_log_params(self, mock_mlflow, monkeypatch):
        """Test parameter logging."""
        monkeypatch.setenv("MLFLOW_ENABLED", "true")
        tracker = MLflowTracker()

        params = {"batch_size": 20, "model": "gpt-3.5"}
        tracker.log_params(params)

        # Should call log_param for each parameter
        assert mock_mlflow.log_param.call_count == 2

    @patch('mlflow_tracker.mlflow')
    def test_log_metrics(self, mock_mlflow, monkeypatch):
        """Test metric logging."""
        monkeypatch.setenv("MLFLOW_ENABLED", "true")
        tracker = MLflowTracker()

        metrics = {"accuracy": 0.95, "loss": 0.05}
        tracker.log_metrics(metrics)

        # Should call log_metric for each metric
        assert mock_mlflow.log_metric.call_count == 2

    @patch('mlflow_tracker.mlflow')
    def test_log_metrics_with_step(self, mock_mlflow, monkeypatch):
        """Test metric logging with step parameter."""
        monkeypatch.setenv("MLFLOW_ENABLED", "true")
        tracker = MLflowTracker()

        metrics = {"accuracy": 0.95}
        tracker.log_metrics(metrics, step=5)

        mock_mlflow.log_metric.assert_called_with("accuracy", 0.95, step=5)

    @patch('mlflow_tracker.mlflow')
    def test_log_artifact(self, mock_mlflow, monkeypatch):
        """Test artifact logging."""
        monkeypatch.setenv("MLFLOW_ENABLED", "true")
        tracker = MLflowTracker()

        tracker.log_artifact("/path/to/artifact.txt")
        mock_mlflow.log_artifact.assert_called_once_with("/path/to/artifact.txt")

    @patch('mlflow_tracker.mlflow')
    def test_log_text(self, mock_mlflow, monkeypatch):
        """Test text logging as artifact."""
        monkeypatch.setenv("MLFLOW_ENABLED", "true")
        tracker = MLflowTracker()

        tracker.log_text("test content", "output.txt")
        mock_mlflow.log_text.assert_called_once_with("test content", "output.txt")

    @patch('mlflow_tracker.mlflow')
    def test_log_dict(self, mock_mlflow, monkeypatch):
        """Test dictionary logging as JSON artifact."""
        monkeypatch.setenv("MLFLOW_ENABLED", "true")
        tracker = MLflowTracker()

        test_dict = {"key": "value"}
        tracker.log_dict(test_dict, "config.json")
        mock_mlflow.log_dict.assert_called_once_with(test_dict, "config.json")

    @patch('mlflow_tracker.mlflow')
    def test_set_tag(self, mock_mlflow, monkeypatch):
        """Test setting single tag."""
        monkeypatch.setenv("MLFLOW_ENABLED", "true")
        tracker = MLflowTracker()

        tracker.set_tag("environment", "test")
        mock_mlflow.set_tag.assert_called_once_with("environment", "test")

    @patch('mlflow_tracker.mlflow')
    def test_set_tags(self, mock_mlflow, monkeypatch):
        """Test setting multiple tags."""
        monkeypatch.setenv("MLFLOW_ENABLED", "true")
        tracker = MLflowTracker()

        tags = {"environment": "test", "version": "v1.0"}
        tracker.set_tags(tags)
        mock_mlflow.set_tags.assert_called_once_with(tags)

    def test_operations_when_disabled(self, monkeypatch):
        """Test all operations are no-ops when disabled."""
        monkeypatch.setenv("MLFLOW_ENABLED", "false")
        tracker = MLflowTracker()

        # None of these should raise errors
        tracker.log_params({"key": "value"})
        tracker.log_metrics({"metric": 1.0})
        tracker.log_artifact("file.txt")
        tracker.log_text("text", "file.txt")
        tracker.log_dict({}, "file.json")
        tracker.set_tag("key", "value")
        tracker.set_tags({"key": "value"})
        tracker.end_run()

    @patch('mlflow_tracker.mlflow')
    def test_end_run(self, mock_mlflow, monkeypatch):
        """Test end_run is called correctly."""
        monkeypatch.setenv("MLFLOW_ENABLED", "true")
        tracker = MLflowTracker()

        tracker.end_run()
        mock_mlflow.end_run.assert_called_once()

    def test_dummy_context_manager(self):
        """Test DummyContext works as context manager."""
        dummy = DummyContext()

        with dummy as ctx:
            assert ctx is dummy
        # Should complete without errors

    @patch('mlflow_tracker.mlflow')
    def test_experiment_name_configuration(self, mock_mlflow, monkeypatch):
        """Test experiment name is set from environment."""
        monkeypatch.setenv("MLFLOW_ENABLED", "true")
        monkeypatch.setenv("MLFLOW_EXPERIMENT_NAME", "TestExperiment")

        tracker = MLflowTracker()
        mock_mlflow.set_experiment.assert_called_with("TestExperiment")

    def test_invalid_metrics_ignored(self, monkeypatch):
        """Test non-numeric metrics are ignored."""
        monkeypatch.setenv("MLFLOW_ENABLED", "true")

        with patch('mlflow_tracker.mlflow'):
            tracker = MLflowTracker()
            # Should not raise error
            tracker.log_metrics({"valid": 1.0, "invalid": "not_a_number", "none_value": None})
