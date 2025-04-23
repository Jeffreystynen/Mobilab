def store_prediction_results(session, result, features, contributions_plot, explanation_text, model):
    """
    Stores prediction results in the session.
    """
    session['prediction_values'] = features
    session['prediction'] = result.get("prediction")
    session['contributions_plot'] = contributions_plot
    session['contributions_explanation'] = explanation_text
    session['model'] = model