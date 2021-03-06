from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, SelectField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, NumberRange, InputRequired, Length

from app.models import User


class MessageForm(FlaskForm):
    message = TextAreaField('Message', validators=[
        DataRequired(), Length(min=0, max=140)])
    submit = SubmitField('Submit')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    # this may result in a race condition if more than one process is attempting to access the db at the same time
    # TODO: come up with a better way to handle duplicate usernames
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError("Username already in use.  Please use a different username.")


class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class EquationForm(FlaskForm):
    operator_choices = ['+', '-', '*', '/']
    x_var = DecimalField('X Value', validators=[InputRequired(), NumberRange()])
    y_var = DecimalField('Y Value', validators=[InputRequired(), NumberRange()])
    operator = SelectField('Operator', choices=operator_choices, validators=[DataRequired()])
    submit = SubmitField('Submit')

    def validate_y_var(self, y_var):
        if self.operator.data == '/' and y_var.data == 0:
            raise ValidationError('Cannot divide by zero! Please enter a different divisor!')
