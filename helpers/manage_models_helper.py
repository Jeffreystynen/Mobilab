import os
import zipfile
import tempfile
import shutil
import requests

def process_and_send_zip(uploaded_file, model_name, target_url="http://127.0.0.1:5001/file_upload"):
    """
    Processes an uploaded .zip file by unzipping it, validating its contents, 
    re-zipping the validated files, and sending it to the model container via an API.
    
    Parameters:
        uploaded_file: The FileStorage object from Flask (e.g., request.files['modelFile'])
        model_name (str): The name for the new model, provided by the admin.
        target_url (str): The URL of the model container's upload endpoint.
    
    Returns:
        response: The response object from the API call.
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Save the uploaded file to a temporary zip file
        temp_zip_path = os.path.join(temp_dir, "uploaded.zip")
        uploaded_file.save(temp_zip_path)
    
        # Create a directory for extraction
        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
    
        # Unzip the file into extract_dir
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    
        # Validate that required files are present
        required_files = ["model.pkl", "metrics.json", "feature_mapping.json"]
        missing_files = [fname for fname in required_files if not os.path.exists(os.path.join(extract_dir, fname))]
        if missing_files:
            raise Exception("Missing required files: " + ", ".join(missing_files))
    
        # Re-zip the validated files into a new zip file
        new_zip_path = os.path.join(temp_dir, f"{model_name}.zip")
        with zipfile.ZipFile(new_zip_path, 'w') as new_zip:
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Write the file into the zip archive; arcname makes sure it's stored without the full path
                    new_zip.write(file_path, arcname=file)
    
        # Send the new zip file to the model container via an API call
        with open(new_zip_path, 'rb') as f:
            files_payload = {'model_zip': (f"{model_name}.zip", f, 'application/zip')}
            data_payload = {'modelName': model_name}
            response = requests.post(target_url, files=files_payload, data=data_payload)
    
        return response
    finally:
        # Clean up temporary directory and files
        shutil.rmtree(temp_dir)
