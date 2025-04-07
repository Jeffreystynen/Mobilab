from wtforms import Form, FloatField, IntegerField, SelectField
from wtforms.validators import DataRequired, NumberRange, ValidationError
from flask_wtf import FlaskForm


def validate_select(form, field):
    """Handles validation for dropdowns on the form."""
    if field.data == '' or field.data is None:
        raise ValidationError("Please select a valid option.")
    try:
        field.data = int(field.data)
    except ValueError:
        raise ValidationError("Invalid value selected.")

class PredictionForm(FlaskForm):
    """Handles validation of the form found on input parameters."""
    age = FloatField('Age', validators=[DataRequired(), NumberRange(min=0)])

    sex = SelectField(
        'Sex',
        choices=[('', 'Select Sex'), ('0', 'Female'), ('1', 'Male')],
        coerce=str,
        validators=[DataRequired(), validate_select]
    )

    chest_pain_type = SelectField(
        'Chest Pain Type',
        choices=[
            ('', 'Select Chest Pain Type'),
            ('1', 'Type 1'),
            ('2', 'Type 2'),
            ('3', 'Type 3'),
            ('4', 'Type 4')
        ],
        coerce=str,
        validators=[DataRequired(), validate_select]
    )

    resting_blood_pressure = FloatField('Resting Blood Pressure', validators=[DataRequired()])
    serum_cholesterol = FloatField('Serum Cholesterol', validators=[DataRequired()])

    fasting_blood_sugar = SelectField(
        'Fasting Blood Sugar > 120',
        choices=[('', 'Select an option'), ('0', 'No'), ('1', 'Yes')],
        coerce=str,
        validators=[DataRequired(), validate_select]
    )

    resting_electrocardiographic = SelectField(
        'Resting Electrocardiographic',
        choices=[
            ('', 'Select ECG Result'),
            ('0', 'Normal'),
            ('1', 'Abnormal 1'),
            ('2', 'Abnormal 2')
        ],
        coerce=str,
        validators=[DataRequired(), validate_select]
    )

    max_heart_rate = FloatField('Max Heart Rate', validators=[DataRequired()])

    exercise_induced_angina = SelectField(
        'Exercise Induced Angina',
        choices=[('', 'Select an option'), ('0', 'No'), ('1', 'Yes')],
        coerce=str,
        validators=[DataRequired(), validate_select]
    )

    oldpeak = FloatField('Oldpeak', validators=[DataRequired()])

    slope_of_peak_st_segment = SelectField(
        'Slope of Peak Exercise ST Segment',
        choices=[
            ('', 'Select Slope'),
            ('1', 'Up'),
            ('2', 'Flat'),
            ('3', 'Down')
        ],
        coerce=str,
        validators=[DataRequired(), validate_select]
    )

    num_major_vessels = IntegerField(
        'Number of Major Vessels',
        validators=[DataRequired(), NumberRange(min=0, max=3)]
    )

    thal = SelectField(
        'Thalassemia',
        choices=[
            ('', 'Select Thalassemia Type'),
            ('0', 'Normal'),
            ('1', 'Fixed defect'),
            ('2', 'Reversible defect')
        ],
        coerce=str,
        validators=[DataRequired(), validate_select]
    )


class CSRFProtectionForm(FlaskForm):
    """Handles CSRF protection for the form."""
    pass