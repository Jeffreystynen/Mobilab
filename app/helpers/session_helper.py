def store_prediction_results(session, result, features):
    """
    Stores prediction results in the session.
    """
    session['prediction_values'] = features
    session['prediction'] = result.get("prediction")
    session['contributions_image_path'] = result.get("contributions_image_path")
    session['contributions_explanation'] = result.get("contributions_explanation")