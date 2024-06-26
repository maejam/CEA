from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import Optional, DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from flask_login import current_user

from .models import User


class RatingForm(FlaskForm):
    rating = IntegerField(
            "Rating",
            validators=[NumberRange(min=1, max=4)],
            description="Rate this document from 1 (best) to 4 (worst)."
            )
    rate = SubmitField("RATE")


class SummaryForm(FlaskForm):
    max_words = IntegerField(
            "Maximum number of words:",
            validators=[Optional(), NumberRange(min=30, max=1000)],
            render_kw={"placeholder": 500},
            )
    summarize = SubmitField("SUMMARIZE")


class RegistrationForm(FlaskForm):
    username = StringField(
            "Username",
            validators=[DataRequired(), Length(min=3, max=25)]
            )
    email = StringField(
            "Email",
            validators=[DataRequired(), Email()]
            )
    password = PasswordField(
            "Password",
            validators=[DataRequired()]
            )
    confirm_password = PasswordField(
            "Confirm Password",
            validators=[DataRequired(), EqualTo("password")]
            )
    submit = SubmitField("Sign Up!")

    def validate_username(self, username):
        user = User.find(User.username == username.data).first_or_none()
        if user:
            raise ValidationError("This name is already taken. Please choose a different one.")

    def validate_email(self, email):
        user = User.find(User.email == email.data).first_or_none()
        if user:
            raise ValidationError("That email is already registered. Please enter a different one.")


class LoginForm(FlaskForm):
    email = StringField(
            "Email",
            validators=[DataRequired(), Email()]
            )
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class UpdateAccountForm(FlaskForm):
    username = StringField(
            "Username",
            validators=[DataRequired(), Length(min=3, max=25)]
            )
    email = StringField(
            "Email",
            validators=[DataRequired(), Email()]
            )
    submit = SubmitField("Update Account")

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.find(User.username == username.data).first_or_none()
            if user:
                raise ValidationError("This name is already taken. Please choose a different one.")

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.find(User.email == email.data).first_or_none()
            if user:
                raise ValidationError("That email is already registered. Please enter a different one.")


class RequestResetForm(FlaskForm):
    email = StringField(
            "Email",
            validators=[DataRequired(), Email()]
            )
    submit = SubmitField("Change Password")

    def validate_email(self, email):
        user = User.find(User.email == email.data).first_or_none()
        if user is None:
            raise ValidationError("There is no account registered with this adress.")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
            "Password",
            validators=[DataRequired()]
            )
    confirm_password = PasswordField(
            "Confirm Password",
            validators=[DataRequired(), EqualTo("password")]
            )
    submit = SubmitField("Reset Password")
