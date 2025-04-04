import pytest
from app.dao.model_dao import get_models, get_metrics, get_plots, get_report, get_feature_mapping
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
    for key in ["accuracy", "trainingShape", "createdAt", "version"]:
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


def test_get_feature_mapping():
    """
    Test that get_feature_mapping returns a dictionary with expected keys.
    """
    feature_mapping = get_feature_mapping(TEST_MODEL_NAME)
    print(f"FEATURE MAPPING: {feature_mapping}")
    
    # Ensure the result is not None and is a list
    assert feature_mapping is not None, "Feature mapping should not be None"
    assert isinstance(feature_mapping, list), "Feature mapping should be a list"
    assert len(feature_mapping) > 0, "Feature mapping should not be empty"

    # Extract the first row and parse the JSON string
    raw_mapping = feature_mapping[0]["featureMapping"]
    try:
        parsed_mapping = json.loads(raw_mapping)
    except Exception as e:
        pytest.fail(f"Feature mapping could not be loaded as JSON: {e}")

    # Verify that the parsed mapping contains the expected keys
    expected_keys = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
    for key in expected_keys:
        assert key in parsed_mapping, f"Missing key '{key}' in feature mapping"