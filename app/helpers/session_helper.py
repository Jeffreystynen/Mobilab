def store_prediction_results(session, result, features, contributions_image_path, explanation_text):
    """
    Stores prediction results in the session.
    """
    session['prediction_values'] = features
    session['prediction'] = result.get("prediction")
    session['contributions_image_path'] = contributions_image_path
    session['contributions_explanation'] = explanation_text