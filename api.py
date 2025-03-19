from flask import Blueprint, request, jsonify
from app.helpers.models_helper import *
from app.helpers.input_params_helper import *
from app.helpers.models_helper import *


api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/predict', methods=["POST"])
def predict_api():
    """
    Predicts heart disease and returns a JSON response with prediction and LIME explanation.
    ---
    tags:
      - Prediction API
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Input parameters for prediction.
        required: true
        schema:
          type: object
          properties:
            features:
              type: array
              items:
                type: number
              example: [63, 1, 3, 145, 233, 1, 0, 150, 0, 2.3, 0, 0, 1]
            model:
              type: string
              example: xgboost
    responses:
      200:
        description: A JSON object containing the prediction and LIME explanation.
        schema:
          type: object
          properties:
            prediction:
              type: integer
              example: 0
            lime_values:
              type: object
              example: {"feature1": 0.1, "feature2": -0.2}
      400:
        description: Invalid input
      500:
        description: Internal server error
    """
    # Get JSON data from request
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    features = data.get("features")
    selected_model = data.get("model", "xgboost").lower()

    # Call the prediction API (using your helper function)
    response = get_prediction_from_api(features, model=selected_model)
    if response.status_code != 200:
        return jsonify({"error": "Prediction API error", "details": response.text}), response.status_code

    # Process the API response
    data = response.json()
    prediction = data.get("prediction")
    lime_values = data.get("lime_values")

    # Process LIME values into a plot and return its path
    lime_image_path, lime_explanation = process_lime_values(
        lime_values=lime_values,
        prediction=prediction,
        feature_names=features
    )

    return jsonify({
        "prediction": prediction,
        "lime_values": lime_values,
        "lime_image_path" : lime_image_path
    })


@api.route('/models', methods=["GET"])
def list_models():
    """
    Returns a list of available models.
    ---
    tags:
      - Models
    produces:
      - application/json
    responses:
      200:
        description: A JSON array of available models.
        schema:
          type: array
          items:
            type: object
            properties:
              name:
                type: string
                example: xgboost
      500:
        description: An error occurred while fetching models.
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Internal Server Error"
    """
    try:
        models = get_models()  # Replace with your helper function that returns a list, e.g. [{"name": "xgboost"}, {"name": "randomforest"}]
        return jsonify(models), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api.route('/models/<model_name>', methods=["GET"])
def get_model_info(model_name):
    """
    Returns model metrics, and plots for the specified model.
    ---
    tags:
      - Models
    parameters:
      - in: path
        name: model_name
        required: true
        type: string
        description: Name of the model (e.g., xgboost, randomforest)
    produces:
      - application/json
    responses:
      200:
        description: A JSON object containing model metrics, feature mapping, and plots.
        schema:
          type: object
          properties:
            metrics:
              type: object
              example: {"accuracy": 0.98, "precision": 1.0, "recall": 0.97}
            plots:
              type: object
              example: {
                "roc_curve": "data:image/png;base64,...",
                "pr_curve": "data:image/png;base64,...",
                "shap_summary": "data:image/png;base64,..."
              }
      404:
        description: Model not found.
      500:
        description: Internal server error.
    """
    try:
        # Use your helper functions to fetch model-specific data.
        metrics = get_metrics(model_name)
        plots = get_plots(model_name)
        
        # Return the data as JSON
        return jsonify({
            "metrics": metrics,
            "plots": plots
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
