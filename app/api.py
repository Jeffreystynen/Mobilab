from flask import Blueprint, request, jsonify
from app.helpers.models_helper import *
from app.helpers.input_params_helper import *
from app.helpers.models_helper import *
from app.helpers.manage_models_helper import *
import shutil
import tempfile


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
    selected_model = data.get("model", "xgboost")

    # Call the prediction API (using your helper function)
    response = get_prediction_from_api(features, model=selected_model)
    print(response.text)
    if response.status_code != 200:
        return jsonify({"error": "Prediction API error", "details": response.text}), response.status_code

    # Process the API response
    data = response.json()
    prediction = data.get("prediction")
    contributions = data.get("contributions")  # H2O AI contributions

    if not contributions:
        return jsonify({"error": "No contributions found in the response"}), 500

    # Process LIME values into a plot and return its path
    lime_image_path, lime_explanation = process_lime_values(
        h2o_data={"contributions": contributions, "prediction": prediction},
        feature_names=features
    )

    return jsonify({
        "prediction": prediction,
        "lime_values": contributions,
        "lime_explanation": lime_explanation,
        "lime_image_path": lime_image_path
    })


@api.route('/file_upload', methods=["POST"])
def file_upload():
    """
    Uploads a model file to the model container in zip format (must include model.pkl, feature-mapping.json, metrics.json).
    ---
    tags:
      - Model Upload
    consumes:
      - multipart/form-data
    produces:
      - application/json
    parameters:
      - in: formData
        name: model_name
        type: string
        required: true
        description: The name to assign to the uploaded model.
      - in: formData
        name: file
        type: file
        required: true
        description: The .zip file containing the model and associated files.
    responses:
      200:
        description: File uploaded successfully.
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
      400:
        description: No file or model name provided.
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Missing file or model name"
      500:
        description: Internal server error.
        schema:
          type: object
          properties:
            error:
              type: string
              example: "File upload API error"
    """
    temp_dir = None
    if 'file' not in request.files or 'model_name' not in request.form:
        return jsonify({"error": "Missing file or model name"}), 400

    file = request.files['file']
    model_name = request.form['model_name']

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        # Save the uploaded file to a temporary directory
        temp_dir = tempfile.mkdtemp()
        zip_file_path = os.path.join(temp_dir, file.filename)
        file.save(zip_file_path)

        # Process the uploaded zip file
        processed_zip_path = process_zip_file(zip_file_path, model_name)

        # Send the file to the model container
        response = send_model_to_api(processed_zip_path, model_name)
      
        if response.status_code != 200:
            return jsonify({"error": "File upload API error", "details": response.text}), response.status_code

        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        shutil.rmtree(temp_dir)


@api.route('/delete_model/<model_name>', methods=["DELETE"])
def remove_model(model_name):
  """
    Deletes a model from the model container.
    ---
    tags:
      - Model Management
    parameters:
      - name: model_name
        in: path
        type: string
        required: true
        description: Name of the model to delete.
    responses:
      200:
        description: Model deleted successfully.
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
      404:
        description: Model not found.
      500:
        description: Internal server error.
    """
  url = f"http://127.0.0.1:5001/delete_model/{model_name}"

  try:
    response = requests.delete(url)
    if response.status_code != 200:
      return jsonify({"error": "Model deletion API error", "details": response.text}), response.status_code
    return jsonify({"success": "Model deleted successfully", "details": response.text}), response.status_code

  except Exception as e:
      return jsonify({"error": str(e)}), 500
