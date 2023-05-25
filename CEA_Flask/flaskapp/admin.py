import os
import json

from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go
import plotly.express as px

from flaskapp import create_app
import models_client
from .admin_forms import TrainNewModelForm
from .models import Document, User


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
        os.makedirs("/mlflow/.tmp", exist_ok=True)
        filepath = os.path.join("/mlflow/.tmp", filename)
        dataset.save(filepath)

        # Other fields
        if train_form.experiment_name.data == "":
            experiment = None
        train_size = int(train_form.train_size.data) if train_form.train_size.data % 1 == 0 else train_form.train_size.data
        test_size = int(train_form.test_size.data) if train_form.test_size.data % 1 == 0 else train_form.test_size.data


        run_params = {
                "data": filepath,
                "content_col": train_form.content_col.data or train_form.content_col.render_kw["placeholder"],
                "label_col": train_form.label_col.data or train_form.label_col.render_kw["placeholder"],
                "model_type": train_form.model_type.data,
                "labels": train_form.labels.data,
                "inverse_labels": train_form.inverse_labels.data,
                "experiment": experiment,
                "name": train_form.run_name.data,
                "tags": train_form.run_tags.data,
                "description": train_form.run_description.data
                }
        train_params = {
                "checkpoint": train_form.checkpoint.data or train_form.checkpoint.render_kw["placeholder"],
                "train_only_head": train_form.only_head.data,
                "epochs": train_form.epochs.data,
                "batch_size": train_form.batch_size.data,
                "train_size": train_size or train_form.train_size.render_kw["placeholder"],
                "test_size": test_size or train_form.test_size.render_kw["placeholder"],
                "initial_lr": train_form.initial_lr.data,
                "final_lr": train_form.final_lr.data,
                "class_weight": train_form.class_weight.data or train_form.class_weight.render_kw["placeholder"],
                }
        flash("Your model is training. Check the progression in mlflow.", "success")
        models_client.proxy.relevance_train(run_params, train_params, train_form.evaluate.data)
        return redirect(url_for("admin.models_admin"))

    return render_template("admin_models.html", title="Models Administration", train_form=train_form)

@admin.route("/stats", methods=["GET", "POST"])
@login_required
def stats():
    if not check_is_admin():
        return redirect(url_for("main.home"))

    # Query db and build DataFrame
    docs = Document.find(with_children=True).to_list()
    docs = [doc.as_dict() for doc in docs]
    docs = pd.DataFrame(docs)
    docs["content"].replace("", np.nan, inplace=True)
    docs.dropna(subset=["content"], inplace=True)
    users = User.find().to_list()

    # Fig1
    fig = px.bar(docs, x="author", y="source", barmode='group')
    fig1 = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Counts
    counts = docs.nunique()
    doc_count = counts["content"]
    author_count = counts["author"]

    # Top contributors
    contribs = docs.value_counts("author")
    contribs = contribs.reset_index()
    #Keep top 5 contributors
    contribs = contribs[:10]
    #fig = px.bar(contribs, x="count", y="author", labels={"count": "Number of documents"}, color_discrete_sequence =["#1cc88a"], orientation="h")
    # Do the same but in revers order
    fig = px.bar(contribs[::-1], x="count", y="author", labels={"count": "Number of documents"}, color_discrete_sequence =["#1cc88a"], orientation="h")

    # fig["layout"]["yaxis"]["autorange"] = "reversed"
    fig["layout"]["yaxis"]["range"] = [0, 9]
    contributors = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)



    return render_template(
            "admin_stats.html",
            title="Statistics",
            doc_count=doc_count,
            author_count=author_count,
            user_count=len(users),
            contributors=contributors)
