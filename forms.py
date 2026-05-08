from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp, ValidationError


class SignupForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=20),
            Regexp(
                r"^[A-Za-z0-9_]+$",
                message="Use letters, numbers, and underscores only.",
            ),
        ],
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Regexp(
                r"^[^\s@]+@[^\s@]+\.[^\s@]+$",
                message="Please enter a valid email address.",
            ),
        ],
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password")],
    )

    def validate_password(self, field):
        password = field.data or ""
        if not any(char.isalpha() for char in password) or not any(char.isdigit() for char in password):
            raise ValidationError("Password must include both letters and numbers.")


class LoginForm(FlaskForm):
    identifier = StringField("Username or email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")


class PromptForm(FlaskForm):
    title = StringField("Prompt title", validators=[DataRequired(), Length(max=160)])
    category = SelectField(
        "Category",
        choices=[
            ("Writing", "Writing"),
            ("Coding", "Coding"),
            ("Study", "Study"),
            ("Marketing", "Marketing"),
            ("Research", "Research"),
        ],
    )
    prompt = TextAreaField("Prompt", validators=[DataRequired()])
    notes = TextAreaField("Notes")
    is_public = BooleanField("Public")
