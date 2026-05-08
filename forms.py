from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class SignupForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password")],
    )


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
