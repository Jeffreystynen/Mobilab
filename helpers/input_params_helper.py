from ..form import PredictionForm 
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shap
import os


def extract_form_features(form):
    features = [
                int(form.age.data),
                int(form.sex.data),
                int(form.chest_pain_type.data),
                int(form.resting_blood_pressure.data),
                int(form.serum_cholesterol.data),
                int(form.fasting_blood_sugar.data),
                int(form.resting_electrocardiographic.data),
                int(form.max_heart_rate.data),
                int(form.exercise_induced_angina.data),
                float(form.oldpeak.data),
                int(form.slope_of_peak_st_segment.data),
                int(form.num_major_vessels.data),
                int(form.thal.data),
            ] 
    return features


def map_features(features):
    features_dict = {
                'age': features[0],
                'sex': features[1],
                'chest_pain_type': features[2],
                'resting_blood_pressure': features[3],
                'serum_cholesterol': features[4],
                'fasting_blood_sugar': features[5],
                'resting_electrocardiographic': features[6],
                'max_heart_rate': features[7],
                'exercise_induced_angina': features[8],
                'oldpeak': features[9],
                'slope_of_peak_st_segment': features[10],
                'num_major_vessels': features[11],
                'thal': features[12]
            }
    return features_dict


def get_prediction_from_api(features):
    """Sends features to API and returns a dictionary response."""
    api_url = "http://127.0.0.1:5001/predict"
    try:
        response = requests.post(api_url, json={"features": features})
        return response
    except requests.RequestException as e:
        print(f"API request failed: {e}")
    return None


def process_shap_values(shap_values, features):
    # Convert SHAP values to a DataFrame
    shap_values_list = list(shap_values.values())
    feature_names = list(shap_values.keys())
    
    # Convert to numpy array
    shap_values_array = np.array(shap_values_list).reshape(1, -1)

    # Now create a DataFrame for SHAP values
    shap_df = pd.DataFrame(shap_values_array, columns=feature_names)

    # Plot SHAP summary plot
    fig = plt.figure(figsize=(8, 6))
    shap.summary_plot(shap_df.values, features, feature_names=feature_names, show=False)
    shap_image_filename = "shap_plot.png"
    shap_image_path = os.path.join("static", "shap_plots", shap_image_filename)

    # Save plot as a static file in the static/shap_plots directory
    plt.savefig(shap_image_path)
    plt.close(fig)

    return shap_image_path


def process_lime_values(lime_values, prediction, feature_names):
    # Convert the LIME values dictionary into a DataFrame
    lime_df = pd.DataFrame(list(lime_values.items()), columns=['Feature', 'Importance'])
    
    # Sort by importance for better visualization
    lime_df = lime_df.sort_values(by='Importance', ascending=False)

    # Create a bar plot for the LIME values
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.barh(lime_df['Feature'], lime_df['Importance'], color='#0090A5')

    # Add labels and title
    prediction_label = "Disease" if prediction == 1 else "No Disease"
    ax.set_xlabel('Importance')
    ax.set_title(f'LIME Feature Importance (Prediction: {prediction_label})')

    # Save the figure as a static image
    lime_image_filename = "lime_plot.png"
    lime_image_path = os.path.join("static", "lime_plots", lime_image_filename)
    
    # Save the plot to the desired path
    plt.tight_layout()
    fig.savefig(lime_image_path)
    plt.close(fig)

    return lime_image_path
