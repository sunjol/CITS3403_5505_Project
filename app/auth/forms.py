"""Forms for the auth blueprint.

This module defines all Flask-WTF form classes used by the authentication
flow: user registration, login, and password change.

All forms inherit from FlaskForm, which provides automatic CSRF protection
via a hidden token field rendered through {{ form.hidden_tag() }} in templates.

Server-side validation is handled by WTForms validators, which run when
form.validate_on_submit() is called in the route. Failed validation
attaches error messages to form.<field>.errors for display in templates.

Example usage in a route:

    from app.auth.forms import RegistrationForm

    @bp.route('/register', methods=['GET', 'POST'])
    def register():
        form = RegistrationForm()
        if form.validate_on_submit():
            # form data is valid, safe to use
            new_user = User(username=form.username.data, email=form.email.data)
            ...
        return render_template('auth/signup.html', form=form)
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError

from app.models import User


class RegistrationForm(FlaskForm):
    """Form for new user sign-up.

    Fields:
        username: 3-20 characters, alphanumeric and underscores only.
                  Must be unique (checked via custom validator).
        email: Standard email format, validated by WTForms Email validator.
        password: Minimum 8 characters.
        confirm_password: Must match password exactly (EqualTo validator).
        submit: Form submit button.

    Validation order: DataRequired → Length → Regexp → custom validate_username.
    All validators must pass for form.validate_on_submit() to return True.
    """
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
        """Ensure the chosen username is not already taken.

        WTForms automatically calls any method named validate_<field_name>
        as part of validate_on_submit(). Raising ValidationError attaches
        the error message to the field's errors list for display.

        Args:
            username: The username field passed by WTForms (not a string).

        Raises:
            ValidationError: If a user with this username already exists.
        """
        existing = User.query.filter_by(username=username.data).first()
        if existing:
            raise ValidationError('Username already taken. Please choose another.')


class LoginForm(FlaskForm):
    """Form for user sign-in.

    Fields:
        identifier: Username or email address (the route looks up by username).
        password: Password (validated against stored hash by route).
        remember: Optional 'Remember me' checkbox; controls session duration
                  via Flask-Login's REMEMBER_COOKIE_DURATION setting.
        submit: Form submit button.

    Note: This form does NOT verify credentials itself — that's the route's
    job. The form only ensures fields are non-empty so the route can safely
    look up the user without worrying about None values.
    """
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


class ChangePasswordForm(FlaskForm):
    """Form for changing the current user's password.

    Used on the user profile page. The route is responsible for verifying
    the current_password against the stored hash before applying the change.

    Fields:
        current_password: User's existing password, verified by the route.
        new_password: Minimum 8 characters.
        confirm_new_password: Must match new_password exactly.
        submit: Form submit button.

    Security note: This form intentionally does NOT validate that the new
    password is different from the current one. Some users may want to
    'rotate' their password to the same value as part of routine hygiene.
    """
    current_password = PasswordField(
        'Current Password',
        validators=[DataRequired(message='Please enter your current password.')]
    )
    new_password = PasswordField(
        'New Password',
        validators=[
            DataRequired(message='New password is required.'),
            Length(min=8, message='Password must be at least 8 characters.')
        ]
    )
    confirm_new_password = PasswordField(
        'Confirm New Password',
        validators=[
            DataRequired(message='Please confirm your new password.'),
            EqualTo('new_password', message='Passwords do not match.')
        ]
    )
    submit = SubmitField('Update Password')