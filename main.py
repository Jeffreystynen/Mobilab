from app import create_app
from flask import Flask
from dotenv import load_dotenv
import os

def remove_shap_plots(SHAP_PLOTS_DIR):
    if os.path.exists(SHAP_PLOTS_DIR):
        for filename in os.listdir(SHAP_PLOTS_DIR):
            file_path = os.path.join(SHAP_PLOTS_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path) 

# load_dotenv()  
app = create_app()
remove_shap_plots(os.path.join('static', 'shap_plots'))
# app.secret_key = env.get("APP_SECRET_KEY")

if __name__ == "__main__":
    app.run(debug=True)
