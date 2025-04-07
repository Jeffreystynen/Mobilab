from weasyprint import HTML
from flask import render_template

def generate_pdf(report):
    """
    Generate a PDF from the given report object.

    Args:
        report (Report): The report object containing sections.

    Returns:
        bytes: The generated PDF content.
    """
    html_content = render_template("pdf_report.html", report=report.get_sections())
    pdf = HTML(string=html_content).write_pdf()
    return pdf