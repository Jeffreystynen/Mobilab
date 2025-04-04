from ..form import PredictionForm 
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shap
import os
from app.dao.model_dao import get_feature_mapping
import json


def extract_form_features(form, model_name):
    """
    Extracts and maps all features from the input parameters form dynamically.
    
    Args:
        form (PredictionForm): The prediction form submitted by the user.
        model_name (str): The name of the model.

    Returns:
        list: A list of features in the correct order for the model.
    """
    # Extract features from the form
    input_features = {
        "age": int(form.age.data),
        "sex": int(form.sex.data),
        "chest_pain_type": int(form.chest_pain_type.data),
        "resting_blood_pressure": int(form.resting_blood_pressure.data),
        "serum_cholesterol": int(form.serum_cholesterol.data),
        "fasting_blood_sugar": int(form.fasting_blood_sugar.data),
        "resting_electrocardiographic": int(form.resting_electrocardiographic.data),
        "max_heart_rate": int(form.max_heart_rate.data),
        "exercise_induced_angina": int(form.exercise_induced_angina.data),
        "oldpeak": float(form.oldpeak.data),
        "slope_of_peak_st_segment": int(form.slope_of_peak_st_segment.data),
        "num_major_vessels": int(form.num_major_vessels.data),
        "thal": int(form.thal.data),
    }
    # Validate and map features dynamically
    ordered_features = validate_and_map_features(input_features, model_name)
    return ordered_features


def generate_h2o_explanation_text(contributions, bias_term, prediction, feature_names):
    """
    Generates a textual explanation for the H2O AI contributions.
    """
    # Convert contributions to a DataFrame
    df = pd.DataFrame(list(contributions.items()), columns=['Feature', 'Importance'])

    # Exclude the BiasTerm for ranking
    df = df[df['Feature'] != 'BiasTerm']

    # Separate positive and negative contributions
    pos_df = df[df['Importance'] > 0].sort_values(by='Importance', ascending=False)
    neg_df = df[df['Importance'] < 0].sort_values(by='Importance', ascending=True)

    # Pick top 2 from each group, if they exist
    top_pos = pos_df.head(2)
    top_neg = neg_df.head(2)

    # Build a short sentence
    prediction_label = "Disease" if prediction == 1 else "No Disease"
    explanation_text = (f"This plot shows how each feature contributed to the model's final decision of '{prediction_label}'. "
                        f"The bias term contributed {bias_term:.2f} to the prediction. "
                        "Positive bars indicate features pushing the prediction toward 'Disease', while negative bars indicate features pushing it away.\n")

    # Add top positive contributors
    if not top_pos.empty:
        explanation_text += "The top positive contributors are: "
        explanation_text += ", ".join([f"{row['Feature']} ({row['Importance']:.2f})" for _, row in top_pos.iterrows()])
        explanation_text += ".\n"

    # Add top negative contributors
    if not top_neg.empty:
        explanation_text += "The top negative contributors are: "
        explanation_text += ", ".join([f"{row['Feature']} ({row['Importance']:.2f})" for _, row in top_neg.iterrows()])
        explanation_text += ".\n"

    explanation_text += "For more details, see the bar lengths and colors in the chart."
    return explanation_text


def process_h2o_contributions(h2o_data, feature_names):
    """
    Processes the H2O AI contributions and plots them. Plots are used for the dashboard.
    """
    # Extract contributions and prediction
    contributions = h2o_data.get("contributions", {}).copy()  # Create a copy to avoid modifying the original
    prediction = h2o_data.get("prediction", 0)

    # Handle empty contributions
    if not contributions:
        default_text = "No contributions are available for this prediction."
        return None, default_text

    # Extract the BiasTerm and remove it from the contributions
    bias_term = contributions.pop("BiasTerm", 0)

    # Add the BiasTerm to all other contributions
    adjusted_contributions = {feature: importance + bias_term for feature, importance in contributions.items()}

    # Sort contributions by absolute importance
    sorted_contributions = sorted(adjusted_contributions.items(), key=lambda x: abs(x[1]), reverse=True)

    # Assign colors based on the sign of importance
    def pick_color(value):
        return '#E73C0D' if value > 0 else '#0090A5'

    colors = [pick_color(importance) for _, importance in sorted_contributions]

    # Create a horizontal bar plot
    features = [feature for feature, _ in sorted_contributions]
    importances = [importance for _, importance in sorted_contributions]

    if not importances:
        return None, "No contributions are available for this prediction."

    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.barh(features, importances, color=colors)
    ax.invert_yaxis()  # So the largest bar is on top

    # Add annotations at the end of each bar
    for bar, importance in zip(bars, importances):
        width = bar.get_width()
        yloc = bar.get_y() + bar.get_height() / 2
        if width > 0:
            xloc = width + 0.002
            ha = 'left'
        else:
            xloc = width - 0.002
            ha = 'right'
        ax.text(xloc, yloc, f'{width:.2f}', va='center', ha=ha, fontsize=9)

    # Add a little horizontal margin so text isn't cut off
    max_val = max(importances)
    min_val = min(importances)
    margin = 0.1 * (max_val - min_val)  # 10% margin
    ax.set_xlim(min_val - margin, max_val + margin)

    # Labels and title
    prediction_label = "Disease" if prediction == 1 else "No Disease"
    ax.set_xlabel('Importance')
    ax.set_title(f'H2O Local Feature Contributions (Prediction: {prediction_label})')

    plt.tight_layout()

    # Ensure the directory exists
    contributions_plots_dir = os.path.join("app/static", "contributions_plots")
    os.makedirs(contributions_plots_dir, exist_ok=True)

    # Save the plot
    contributions_image_filename = "h2o_contributions_plot.png"
    contributions_image_path = os.path.join(contributions_plots_dir, contributions_image_filename)
    plt.savefig(contributions_image_path, bbox_inches="tight")
    plt.close(fig)

    # Generate explanation text
    explanation_text = generate_h2o_explanation_text(contributions, bias_term, prediction, feature_names)

    return contributions_image_path, explanation_text


def validate_and_map_features(input_features, model_name):
    """
    Validate and map input features to the expected format for the model.
    """
    # Fetch the feature mapping for the model
    feature_mapping = get_feature_mapping(model_name)
    if not feature_mapping or len(feature_mapping) == 0:
        raise ValueError(f"No feature mapping found for model: {model_name}")

    # Parse the JSON string
    raw_mapping = feature_mapping[0]["featureMapping"]
    parsed_mapping = json.loads(raw_mapping)

    # Ensure all required features are present
    required_features = set(parsed_mapping.values())
    missing_features = required_features - set(input_features.keys())
    if missing_features:
        raise ValueError(f"Missing required features: {missing_features}")

    # Return the validated dictionary of features
    return {parsed_mapping[str(i)]: input_features[parsed_mapping[str(i)]] for i in range(len(parsed_mapping))}