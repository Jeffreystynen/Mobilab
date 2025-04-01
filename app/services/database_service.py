from app.dao.model_dao import get_models, get_metrics, get_plots, get_report
import json

def get_all_models():
    """
    Retrieve all model names.
    """
    models = get_models()
    if not models:
        raise ValueError("No models found.")
    return models

def get_model_metrics(model_name):
    """
    Retrieve metrics for a specific model.
    """
    metrics = get_metrics(model_name)
    if not metrics:
        raise ValueError(f"No metrics found for model '{model_name}'.")
    return metrics

def get_model_plots(model_name):
    """
    Retrieve plots for a specific model.
    """
    plots = get_plots(model_name)
    if not plots:
        raise ValueError(f"No plots found for model '{model_name}'.")
    return plots

def get_model_report(model_name):
    """
    Retrieve and parse the report for a specific model.
    """
    result = get_report(model_name)
    if not result or "report" not in result:
        raise ValueError(f"No report found for model '{model_name}'.")
    try:
        report = json.loads(result["report"])
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse report JSON: {e}")
    return report