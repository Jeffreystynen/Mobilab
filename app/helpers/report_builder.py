from flask import url_for
import json

class Report:
    """The complex object that is being built."""
    def __init__(self):
        self.sections = []

    def add_section(self, title, content):
        """Add a section to the report."""
        self.sections.append({"title": title, "content": content})

    def get_sections(self):
        """Return all sections of the report."""
        return self.sections


class ReportBuilder:
    """Builder class for constructing a report."""
    def __init__(self):
        self.report = Report()


    def add_prediction_results(self, explanation):
        """Add explanation for the prediction to the report."""
        if not explanation:
            content = "<p>No explanation available for the prediction.</p>"
        else:
            content = f"""
            <div class="card-body">
                <p class="card-text">{explanation}</p>
            </div>
            """
        self.report.add_section("", content)

    def add_feature_importance_plot(self, plot_path):
        """Add feature importance plot to the report."""
        if not plot_path:
            content = "<p>No Contributions plot available.</p>"
        elif plot_path.startswith("data:image/png;base64,"):  # Check if it's a Base64 string
            content = f"""
            <div class="row g-0 d-flex align-items-center">
                <div class="col-12">
                    <img src="{plot_path}" class="img-fluid" alt="Contributions Plot" style="width: 100%; height: auto;">
                </div>
            </div>
            """
        else:
            # Convert the relative path to an absolute URL
            absolute_url = url_for('static', filename=plot_path.split('static/')[-1], _external=True)
            content = f"""
            <div class="row g-0 d-flex align-items-center">
                <div class="col-12">
                    <img src="{absolute_url}" class="img-fluid" alt="Contributions Plot" style="width: 100%; height: auto;">
                </div>
            </div>
            """
        self.report.add_section("Feature Importance", content)
    
    def add_feature_importance_plot_explanation(self, explanation):
        """Add explanation for feature importance plot to the report."""
        content = f"<p>{explanation}</p>"
        self.report.add_section("Feature Importance Explanation", content)

    def add_input_parameters(self, parameters, form):
        """Add input parameters to the report."""
        content = """
        <div>
            <table class="table table-striped table-bordered">
                <thead class="thead-dark">
                    <tr>
                        <th>Parameter</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
        """
        for key, value in parameters.items():
            # Check if the field exists in the form and has choices
            if hasattr(form, key) and hasattr(form[key], "choices"):
                # Map the value to its corresponding label
                value = dict(form[key].choices).get(str(value), value)
            content += f"""
            <tr>
                <td>{key.replace('_', ' ')}</td>
                <td>{value}</td>
            </tr>
            """
        content += """
                </tbody>
            </table>
        </div>
        """
        self.report.add_section("Prediction Input Values", content)

    def add_model_metadata(self, metadata):
        """Add model metadata to the report."""
        content = """
        <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="border: 1px solid #ddd; padding: 8px;">Metric</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Value</th>
                </tr>
            </thead>
            <tbody>
        """
        if "trainingShape" in metadata:
            if isinstance(metadata["trainingShape"], str):
                metadata["trainingShape"] = json.loads(metadata["trainingShape"])
        for key, value in metadata.items():
            # Handle the trainingShape key specifically
            if key == "trainingShape" and isinstance(value, dict):
                value = f"Rows: {value.get('rows', 'N/A')}, Columns: {value.get('columns', 'N/A')}"
            content += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px;">{key.replace('_', ' ').title()}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{value}</td>
            </tr>
            """
        content += "</tbody></table>"
        self.report.add_section("Model Metadata", content)

    def add_model_plots(self, plots):
        """Add model plots to the report."""
        content = ""
        for name, path in plots.items():
            # Ensure the path is relative to the static directory
            relative_path = path.split("static/")[-1] if "static/" in path else path
            absolute_url = url_for('static', filename=relative_path, _external=True)
            content += f"""
            <div style="text-align: center; margin-bottom: 20px;">
                <h5>{name.replace('_', ' ').title()}</h5>
                <img src="{absolute_url}" alt="{name}" style="max-width: 100%; height: auto;">
            </div>
            """
        self.report.add_section("Model Plots", content)

    def add_model_report(self, report):
        """Add a complete model report to the report."""
        content = """
        <table style="width: 100%; border-collapse: collapse; border: 1px solid #ddd;">
            <thead>
                <tr style="background-color: #f2f2f2;">
                    <th style="border: 1px solid #ddd; padding: 8px;">Class</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Precision</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Recall</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">F1-Score</th>
                    <th style="border: 1px solid #ddd; padding: 8px;">Support</th>
                </tr>
            </thead>
            <tbody>
        """
        # Add rows for each class
        for class_name, metrics in report.items():
            if class_name not in ["accuracy", "macro avg", "weighted avg"]:
                content += f"""
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;">{class_name}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{metrics['precision']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{metrics['recall']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{metrics['f1-score']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{metrics['support']}</td>
                </tr>
                """

        # Add rows for accuracy, macro avg, and weighted avg
        content += f"""
            </tbody>
            <tfoot>
                <tr>
                    <th style="border: 1px solid #ddd; padding: 8px;">Accuracy</th>
                    <td colspan="4" style="border: 1px solid #ddd; padding: 8px;">{report['accuracy']}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid #ddd; padding: 8px;">Macro Avg</th>
                    <td style="border: 1px solid #ddd; padding: 8px;">{report['macro avg']['precision']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{report['macro avg']['recall']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{report['macro avg']['f1-score']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{report['macro avg']['support']}</td>
                </tr>
                <tr>
                    <th style="border: 1px solid #ddd; padding: 8px;">Weighted Avg</th>
                    <td style="border: 1px solid #ddd; padding: 8px;">{report['weighted avg']['precision']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{report['weighted avg']['recall']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{report['weighted avg']['f1-score']}</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{report['weighted avg']['support']}</td>
                </tr>
            </tfoot>
        </table>
        """
        self.report.add_section("Model Report", content)

    def get_report(self):
        """Return the constructed report."""
        return self.report


class ReportDirector:
    """Director class to construct reports using the builder."""
    def __init__(self, builder):
        self.builder = builder

    def build_web_report(self, parameters, plot_path, form):
        """Build a web-based report."""
        self.builder.add_feature_importance_plot(plot_path)
        self.builder.add_input_parameters(parameters, form)
        return self.builder.get_report()

    def build_pdf_report(self, explanation, contribution_image_path, parameters, form, metadata, plots, report):
        """Build a downloadable PDF report."""
        self.builder.add_prediction_results(explanation)
        self.builder.add_feature_importance_plot(contribution_image_path)
        self.builder.add_input_parameters(parameters, form)
        self.builder.add_model_metadata(metadata)
        self.builder.add_model_plots(plots)
        self.builder.add_model_report(report)
        return self.builder.get_report()
    
    def build_model_report(self, metadata, plots, report):
        """Build a model report."""
        self.builder.add_model_metadata(metadata)
        self.builder.add_model_plots(plots)
        self.builder.add_model_report(report)
        return self.builder.get_report()