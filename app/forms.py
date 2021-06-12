from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DecimalField, SelectField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Email, NumberRange, InputRequired
from app.models import User


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_two = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')


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
    x_var = DecimalField('x value', validators=[InputRequired(), NumberRange()])
    y_var = DecimalField('y_value', validators=[InputRequired(), NumberRange()])
    operator = SelectField('Operator', choices=operator_choices, validators=[DataRequired()])
    submit = SubmitField('Submit')

    def validate_y_var(self, y_var):
        if self.operator.data == '/' and y_var.data == 0:
            raise ValidationError('Cannot divide by zero! Please enter a different divisor!')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password_two = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')
