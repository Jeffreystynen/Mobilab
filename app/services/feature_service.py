import json
import os
import pandas as pd
import matplotlib.pyplot as plt
from app.dao.model_dao import ModelDAO
from flask import current_app as app
from io import BytesIO


class FeatureService:
    """Service for handling feature-related operations."""

    def __init__(self, model_dao: ModelDAO):
        """
        Initialize FeatureService with required dependencies.

        Args:
            model_dao (ModelDAO): DAO for interacting with the database.
        """
        self.model_dao = model_dao

    def extract_and_validate_features(self, form, model_name: str) -> dict:
        """
        Extract and validate features from the form.

        Args:
            form: Flask form containing feature values.
            model_name: Name of the model to validate against.

        Returns:
            dict: Validated and mapped features.

        Raises:
            ValueError: If features are invalid or missing.
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

        # Validate and map features
        return self._validate_and_map_features(input_features, model_name)

    def _validate_and_map_features(self, input_features: dict, model_name: str) -> dict:
        """
        Validate and map input features to the expected format for the model.

        Args:
            input_features: Dictionary of input features.
            model_name: Name of the model.

        Returns:
            dict: Validated and mapped features.

        Raises:
            ValueError: If required features are missing or invalid.
        """
        feature_mapping = self.model_dao.get_feature_mapping(model_name)
        if not feature_mapping or len(feature_mapping) == 0:
            raise ValueError(f"No feature mapping found for model: {model_name}")

        # Parse the JSON string
        raw_mapping = feature_mapping[0]["featureMapping"]
        parsed_mapping = json.loads(raw_mapping)

        # Ensure all required features are present
        required_features = set(parsed_mapping.values())
        print(f"required_features: {required_features}")
        print(f"input_features: {input_features}")
        missing_features = required_features - set(input_features.keys())
        if missing_features:
            raise ValueError(f"Missing required features: {missing_features}")

        # Map features to the expected order
        return {parsed_mapping[str(i)]: input_features[parsed_mapping[str(i)]] for i in range(len(parsed_mapping))}

    def process_contributions(self, prediction_result: dict, feature_names: list) -> tuple:
        """
        Process contributions and generate visualizations.

        Args:
            prediction_result: Dictionary containing prediction and contributions.
            feature_names: List of feature names.

        Returns:
            tuple: Path to contributions plot and explanation text.
        """
        contributions = prediction_result.get("contributions", {}).copy()
        prediction = prediction_result.get("prediction", 0)

        if not contributions:
            return None, "No contributions are available for this prediction."

        # Extract and adjust contributions
        bias_term = contributions.pop("BiasTerm", 0)
        adjusted_contributions = {feature: importance + bias_term for feature, importance in contributions.items()}

        # Generate plot
        plot_buffer = self._generate_contributions_plot(adjusted_contributions, prediction)

        # Generate explanation text
        explanation = self._generate_explanation_text(adjusted_contributions, bias_term, prediction, feature_names)

        return plot_buffer, explanation

    def _generate_contributions_plot(self, contributions: dict, prediction: int) -> BytesIO:
        """Generate a plot for feature contributions and return it as a BytesIO object."""
        # Sort contributions by absolute importance
        sorted_contributions = sorted(contributions.items(), key=lambda x: abs(x[1]), reverse=True)
        features = [feature for feature, _ in sorted_contributions]
        importances = [importance for _, importance in sorted_contributions]

        # Create the plot
        fig, ax = plt.subplots(figsize=(8, 6))
        bars = ax.barh(features, importances, color=["#E73C0D" if imp > 0 else "#0090A5" for imp in importances])
        ax.invert_yaxis()
        ax.set_xlabel("Importance")
        ax.set_title(f"Feature Contributions (Prediction: {'Disease' if prediction == 1 else 'No Disease'})")

        # Add annotations to bars
        for bar, importance in zip(bars, importances):
            ax.text(
                bar.get_width() + (0.002 if importance > 0 else -0.002),
                bar.get_y() + bar.get_height() / 2,
                f"{importance:.2f}",
                va="center",
                ha="left" if importance > 0 else "right",
                fontsize=10,
                color="black"
            )

        min_importance = min(importances)
        max_importance = max(importances)
        ax.set_xlim(min_importance * 1.2 if min_importance < 0 else 0, max_importance * 1.2 if max_importance > 0 else 0)

        # Save the plot to a BytesIO buffer
        buffer = BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")
        plt.close(fig)
        buffer.seek(0)  # Reset buffer pointer to the beginning

        return buffer

    def _generate_explanation_text(self, contributions: dict, bias_term: float, prediction: int, feature_names: list) -> str:
        """Generate textual explanation for contributions."""
        df = pd.DataFrame(list(contributions.items()), columns=["Feature", "Importance"])
        pos_contributors = df[df["Importance"] > 0].sort_values(by="Importance", ascending=False).head(2)
        neg_contributors = df[df["Importance"] < 0].sort_values(by="Importance", ascending=True).head(2)

        explanation = f"The model predicted {'Disease' if prediction == 1 else 'No Disease'}.\n"
        explanation += f"The bias term contributed {bias_term:.2f}.\n"

        if not pos_contributors.empty:
            explanation += "Top positive contributors: " + ", ".join(
                f"{row['Feature']} ({row['Importance']:.2f})" for _, row in pos_contributors.iterrows()
            ) + ".\n"

        if not neg_contributors.empty:
            explanation += "Top negative contributors: " + ", ".join(
                f"{row['Feature']} ({row['Importance']:.2f})" for _, row in neg_contributors.iterrows()
            ) + ".\n"

        return explanation