from flask import Blueprint, request, jsonify
from app.helpers.models_helper import *
from app.helpers.input_params_helper import *
from app.helpers.models_helper import *
from app.helpers.manage_models_helper import *
import shutil
import tempfile
from app.services.api_client import APIClient


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
              example: DRF_1_AutoML_5_20250327_133650
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
    try:
        # Extract features and model from the request
        data = request.get_json()
        features = data.get("features")
        selected_model = data.get("model")

        if not features or not selected_model:
            return jsonify({"error": "Invalid input: features or model missing"}), 400

        # Call the external prediction API
        api_url = "http://127.0.0.1:5001/predict"
        response = APIClient.post(api_url, json={"features": features, "model": selected_model})

        if "error" in response:
            return jsonify({"error": response["error"]}), 500

        # Return the raw prediction and contributions
        return jsonify({
            "prediction": response.get("prediction", 0),
            "contributions": response.get("contributions", {})
        })
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


# @api.route('/file_upload', methods=["POST"])
# def file_upload():
#     """
#     Uploads a model file to the model container in zip format (must include model.pkl, feature-mapping.json, metrics.json).
#     ---
#     tags:
#       - Model Upload
#     consumes:
#       - multipart/form-data
#     produces:
#       - application/json
#     parameters:
#       - in: formData
#         name: model_name
#         type: string
#         required: true
#         description: The name to assign to the uploaded model.
#       - in: formData
#         name: file
#         type: file
#         required: true
#         description: The .zip file containing the model and associated files.
#     responses:
#       200:
#         description: File uploaded successfully.
#         schema:
#           type: object
#           properties:
#             success:
#               type: boolean
#               example: true
#       400:
#         description: No file or model name provided.
#         schema:
#           type: object
#           properties:
#             error:
#               type: string
#               example: "Missing file or model name"
#       500:
#         description: Internal server error.
#         schema:
#           type: object
#           properties:
#             error:
#               type: string
#               example: "File upload API error"
#     """
#     temp_dir = None
#     if 'file' not in request.files or 'model_name' not in request.form:
#         return jsonify({"error": "Missing file or model name"}), 400

#     file = request.files['file']
#     model_name = request.form['model_name']

#     if file.filename == '':
#         return jsonify({"error": "No file selected"}), 400

#     try:
#         # Save the uploaded file to a temporary directory
#         temp_dir = tempfile.mkdtemp()
#         zip_file_path = os.path.join(temp_dir, file.filename)
#         file.save(zip_file_path)

#         # Process the uploaded zip file
#         processed_zip_path = process_zip_file(zip_file_path, model_name)

#         # Send the file to the model container
#         response = send_model_to_api(processed_zip_path, model_name)
      
#         if response.status_code != 200:
#             return jsonify({"error": "File upload API error", "details": response.text}), response.status_code

#         return jsonify({"success": True})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#     finally:
#         shutil.rmtree(temp_dir)


# @api.route('/delete_model/<model_name>', methods=["DELETE"])
# def remove_model(model_name):
#   """
#     Deletes a model from the model container.
#     ---
#     tags:
#       - Model Management
#     parameters:
#       - name: model_name
#         in: path
#         type: string
#         required: true
#         description: Name of the model to delete.
#     responses:
#       200:
#         description: Model deleted successfully.
#         schema:
#           type: object
#           properties:
#             success:
#               type: boolean
#               example: true
#       404:
#         description: Model not found.
#       500:
#         description: Internal server error.
#     """
#   url = f"http://127.0.0.1:5001/delete_model/{model_name}"

#   try:
#     response = requests.delete(url)
#     if response.status_code != 200:
#       return jsonify({"error": "Model deletion API error", "details": response.text}), response.status_code
#     return jsonify({"success": "Model deleted successfully", "details": response.text}), response.status_code

#   except Exception as e:
#       return jsonify({"error": str(e)}), 500
