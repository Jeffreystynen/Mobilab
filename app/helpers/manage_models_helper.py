import os
import zipfile
import shutil
import requests
import tempfile

def process_zip_file(zip_file_path, model_name):
    """
    Processes an uploaded .zip file by unzipping, validating its contents, 
    and re-zipping the validated files.
    
    Returns:
        path to the re-zipped file
    """
    temp_dir = tempfile.mkdtemp()
    try:
        extract_dir = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)

        # Extract the zip file
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)


        # Validate required files
        required_files = ["model.pkl", "metrics.json", "feature_mapping.json"]
        missing_files = [fname for fname in required_files if not os.path.exists(os.path.join(extract_dir, fname))]
        if missing_files:
            raise Exception("Missing required files: " + ", ".join(missing_files))

        # Create a new validated zip
        new_zip_path = os.path.join(temp_dir, f"{model_name}.zip")
        with zipfile.ZipFile(new_zip_path, 'w') as new_zip:
            for root, dirs, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    new_zip.write(file_path, arcname=file)

    except Exception as e:
        print(e)

    return new_zip_path


def send_model_to_api(zip_file_path, model_name):
    url = "http://127.0.0.1:5001/upload_model"

    if not os.path.exists(zip_file_path):
        shutil.rmtree(temp_dir)
        return {"error": "File not found before sending"}

    response = None

    try:
        with open(zip_file_path, "rb") as f:
            files = {"file": (f"{model_name}.zip", f, "application/zip")}
            data = {"model_name": model_name}
            response = requests.post(url, files=files, data=data)


    except Exception as e:
        response = {"error": str(e)}

    return response
