from ..form import PredictionForm 
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shap
import os


def extract_form_features(form):
    """Extracts all features from the input parameters form."""
    if isinstance(form, list):
        features = form

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
    """Maps extraced form features in a dictionary."""
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