from wtforms import Form, FloatField, IntegerField, SelectField
from wtforms.validators import DataRequired, NumberRange

class PredictionForm(Form):
    age = FloatField('Age', validators=[DataRequired(), NumberRange(min=0)])
    sex = SelectField('Sex', choices=[(0, 'Female'), (1, 'Male')], coerce=int, validators=[DataRequired()])
    chest_pain_type = SelectField('Chest Pain Type', choices=[(1, 'Type 1'), (2, 'Type 2'), (3, 'Type 3'), (4, 'Type 4')], coerce=int, validators=[DataRequired()])
    resting_blood_pressure = FloatField('Resting Blood Pressure', validators=[DataRequired()])
    serum_cholesterol = FloatField('Serum Cholesterol', validators=[DataRequired()])
    fasting_blood_sugar = SelectField('Fasting Blood Sugar > 120', choices=[(0, 'No'), (1, 'Yes')], coerce=int, validators=[DataRequired()])
    resting_electrocardiographic = SelectField('Resting Electrocardiographic', choices=[(0, 'Normal'), (1, 'Abnormal 1'), (2, 'Abnormal 2')], coerce=int, validators=[DataRequired()])
    max_heart_rate = FloatField('Max Heart Rate', validators=[DataRequired()])
    exercise_induced_angina = SelectField('Exercise Induced Angina', choices=[(0, 'No'), (1, 'Yes')], coerce=int, validators=[DataRequired()])
    oldpeak = FloatField('Oldpeak', validators=[DataRequired()])
    slope_of_peak_st_segment = SelectField('Slope of Peak Exercise ST Segment', choices=[(1, 'Up'), (2, 'Flat'), (3, 'Down')], coerce=int, validators=[DataRequired()])
    num_major_vessels = IntegerField('Number of Major Vessels', validators=[DataRequired(), NumberRange(min=0, max=3)])
    thal = SelectField('Thalassemia', choices=[(0, 'Normal'), (1, 'Fixed defect'), (2, 'Reversible defect')], coerce=int, validators=[DataRequired()])
