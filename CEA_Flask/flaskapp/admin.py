import os

from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from flaskapp import create_app
import models_client
from .admin_forms import TrainNewModelForm


admin = Blueprint("admin", __name__)


def check_is_admin():
    if not current_user.is_admin:
        flash("This page is only accessible to administrators.", "info")
        return False
    return True

@admin.route("/models", methods=["GET", "POST"])
@login_required
def models_admin():
    if not check_is_admin():
        return redirect(url_for("main.home"))
    train_form = TrainNewModelForm()
    if train_form.validate_on_submit():
        # data
        dataset = train_form.data.data
        filename = secure_filename(dataset.filename)
        flash(str(type(dataset)))
        # dataset.save(os.path.join(
        #     current_app.instance_path, "dataset", filename))

        # None defaults


        run_params = {
                "data": dataset,
                "content_col": train_form.content_col.data or train_form.content_col.render_kw["placeholder"],
                "label_col": train_form.label_col.data or train_form.label_col.render_kw["placeholder"],
                "model_type": train_form.model_type.data,
                "labels": train_form.labels.data,
                "inverse_labels": train_form.inverse_labels.data,
                "experiment": train_form.experiment_name.data,
                "name": train_form.run_name.data,
                "tags": train_form.run_tags.data,
                "description": train_form.run_description.data
                }
        train_params = {
                "checkpoint": train_form.checkpoint.data or train_form.checkpoint.render_kw["placeholder"],
                "train_only_head": train_form.only_head.data,
                "epochs": train_form.epochs.data,
                "batch_size": train_form.batch_size.data,
                "train_size": train_form.train_size.data or train_form.train_size.render_kw["placeholder"],
                "test_size": train_form.test_size.data or train_form.test_size.render_kw["placeholder"],
                "initial_lr": train_form.initial_lr.data,
                "final_lr": train_form.final_lr.data,
                "class_weight": train_form.class_weight.data or train_form.class_weight.render_kw["placeholder"],
                }
        flash(f"Your model is training. Check the training progression in mlflow.\n run_params={run_params} \n train_params={train_params}", "success")
        return redirect(url_for("auth.login"))

    return render_template("admin_models.html", title="Models Administration", train_form=train_form)

@admin.route("/stats", methods=["GET", "POST"])
@login_required
def stats():
    from .models import Document
    import numpy as np
    import pandas as pd
    import json
    import plotly
    import plotly.graph_objects as go
    import plotly.express as px
    if not check_is_admin():
        return redirect(url_for("main.home"))

    # Query db and build DataFrame
    docs = Document.find(with_children=True).to_list()
    docs = [doc.as_dict() for doc in docs]
    docs = pd.DataFrame(docs)
    docs["content"].replace("", np.nan, inplace=True)
    docs.dropna(subset=["content"], inplace=True)

    # Fig1
    fig = px.bar(docs, x="author", y="source", barmode='group')
    fig1 = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Fig2
    fig = px.bar(docs, x="source", y="author", barmode='group')
    fig2 = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Doc count
    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode = "number+delta",
        value = len(docs),
        domain = {'row': 0, 'column': 1}))
    fig3 = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


    return render_template("admin_stats.html", title="Statistics", fig1=fig1, fig2=fig2, fig3=fig3)
