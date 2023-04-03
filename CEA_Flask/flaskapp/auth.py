from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from flask_mail import Message


from . import bcrypt, login_manager, mail
from .models import User
from .forms import (RegistrationForm, LoginForm, UpdateAccountForm,
                    RequestResetForm, ResetPasswordForm)

auth = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id).run()


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(username=form.username.data, email=form.email.data, password=hashed_pw)
        user.insert()
        flash("Account successfully created. You are now able to log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", title="Register", form=form)


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.find(User.email == form.email.data).first_or_none()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, form.remember.data)
            next_page = request.args.get("next")
            if next_page == url_for("auth.logout"):
                next_page = None
            flash("Successfully Logged In!", "success")
            return redirect(next_page) if next_page else redirect(url_for("main.home"))

        else:
            flash("Login unsuccessful. Please check your email and password.", "danger")

    return render_template("login.html", title="Login", form=form)


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You are now logged out.", "info")
    return redirect(url_for("main.home"))


@auth.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.save()
        flash("Your account has been updated successfully!", "success")
        return redirect(url_for("auth.account"))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template("account.html", title="Account", form=form)


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message("Reset your Password!",
                    sender=current_app.config["MAIL_USERNAME"],
                    recipients=[user.email]
                    )
    msg.body = f""" Please click on the link below to reset your password:
{url_for("auth.reset_token", token=token, _external=True)} """
    mail.send(msg)


@auth.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.find(User.email == form.email.data).first_or_none()
        send_reset_email(user)
        flash("You can now change your password. Check your emails!", "info")
        return redirect(url_for("auth.login"))

    return render_template("reset_request.html", title="Reset Password", form=form)


@auth.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    user = User.check_reset_token(token)
    if not user:
        flash("This token is invalid or expired. Please request a new one.", "warning")
        return redirect(url_for("auth.reset_request"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user.password = hashed_pw
        user.save()
        flash("Your password has been correctly updated. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_token.html", title="Reset Password", form=form)
