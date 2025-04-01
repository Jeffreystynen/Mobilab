import pytest
from app.dao.model_dao import get_models, get_metrics, get_plots, get_report
import json

TEST_MODEL_NAME = "DRF_1_AutoML_5_20250327_133650"

def test_get_models():
    """
    Test that get_models returns a list of model names.
    """
    models = get_models()
    print(f"MODELS: {models}")
    # Assert that the return value is a list.
    assert isinstance(models, list)
    # And check that our test model name is in the list.
    assert TEST_MODEL_NAME in models

def test_get_metrics():
    """
    Test that get_metrics returns a dictionary with expected keys.
    """
    metrics = get_metrics(TEST_MODEL_NAME)
    print(f"METRICS: {metrics}")
    assert metrics is not None, "Metrics should not be None"
    assert isinstance(metrics, dict), "Metrics should be a dictionary"
    # Check that the keys we expect exist:
    for key in ["accuracy", "trainingShape"]:
        assert key in metrics, f"Missing key '{key}' in metrics"

def test_get_plots():
    """
    Test that get_plots returns a dictionary with expected keys.
    """
    plots = get_plots(TEST_MODEL_NAME)
    print(f"PLOTS:  {plots}")
    assert plots is not None, "Plots should not be None"
    assert isinstance(plots, dict), "Plots should be a dictionary"
    for key in ["auc", "aucpr", "shap"]:
        assert key in plots, f"Missing key '{key}' in plots"

def test_get_report_structure():
    """
    Test that get_report returns a dictionary with a 'report' field that matches the expected JSON structure.
    """
    result = get_report(TEST_MODEL_NAME)
    print(f"REPORT:  {result}")
    
    # Ensure we got a result.
    assert result is not None, "Expected a non-None result for a known model."
    assert isinstance(result, dict), "Expected result to be a dict."

    # Check that the 'report' key is present.
    assert "report" in result, "Expected the key 'report' to be present in the result."

    # The report is stored as a JSON string; load it.
    try:
        report = json.loads(result["report"])
    except Exception as e:
        pytest.fail(f"Report could not be loaded as JSON: {e}")

    # Verify that the top-level keys are present.
    expected_keys = ["class 0", "class 1", "accuracy", "macro avg", "weighted avg"]
    for key in expected_keys:
        assert key in report, f"Missing key '{key}' in the report."
