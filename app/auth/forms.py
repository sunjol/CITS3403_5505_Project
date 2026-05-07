"""Forms for the auth blueprint."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError

from app.models import User


class RegistrationForm(FlaskForm):
    """Form for new user sign-up."""
    username = StringField(
        'Username',
        validators=[
            DataRequired(message='Username is required.'),
            Length(min=3, max=20, message='Username must be 3-20 characters.'),
            Regexp(r'^[A-Za-z0-9_]+$',
                   message='Only letters, numbers, and underscores allowed.')
        ]
    )
    email = StringField(
        'Email',
        validators=[
            DataRequired(message='Email is required.'),
            Email(message='Please enter a valid email address.')
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(message='Password is required.'),
            Length(min=8, message='Password must be at least 8 characters.')
        ]
    )
    confirm_password = PasswordField(
        'Confirm Password',
        validators=[
            DataRequired(message='Please confirm your password.'),
            EqualTo('password', message='Passwords do not match.')
        ]
    )
    submit = SubmitField('Create Community Account')

    def validate_username(self, username):
        """Custom validator: check username is not already taken."""
        existing = User.query.filter_by(username=username.data).first()
        if existing:
            raise ValidationError('Username already taken. Please choose another.')


class LoginForm(FlaskForm):
    """Form for user sign-in."""
    identifier = StringField(
        'Username or Email',
        validators=[DataRequired(message='Username is required.')]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired(message='Password is required.')]
    )
    remember = BooleanField('Remember me')
    submit = SubmitField('Enter PromptShare')