from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app
from flask_login import login_required, current_user

import models_client


admin = Blueprint("admin", __name__)


def check_is_admin():
    if not current_user.is_admin:
        flash("This page is only accessible to administrators.", "info")
        return False
    return True

@admin.route("/models")
@login_required
def models_admin():
    if not check_is_admin():
        return redirect(url_for("main.home"))
    return render_template("admin_models.html", title="Models Administration")#, mlflow_url=requests.get("http://mlflow:5001".text))

