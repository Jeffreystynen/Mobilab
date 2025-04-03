from app.helpers.input_params_helper import extract_form_features

def process_prediction_form(form):
    """
    Validates the form and extracts features for prediction.
    """
    if not form.validate():
        error_messages = "; ".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()])
        raise ValueError(f"Form validation failed: {error_messages}")
    return extract_form_features(form)