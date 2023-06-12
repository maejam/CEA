import os
import json
import xmlrpc
import shutil

from flask import Blueprint, render_template, url_for, flash, redirect, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go
import plotly.express as px
from bunnet.operators import Exists

from flaskapp import create_app
import models_client
from .admin_forms import SettingsForm, TrainNewModelForm, RegisterModelForm
from .models import Document, User, Prediction, DocumentForModelsView


admin = Blueprint("admin", __name__)


def check_is_admin():
    if not current_user.is_admin:
        flash("This page is only accessible to administrators.", "info")
        return False
    return True

# Redirect /swaggers to template admin_swaggers.html
@admin.route("/swaggers", methods=["GET", "POST"])
@login_required
def swaggers():
    if not check_is_admin():
        return redirect(url_for("main.home"))
    return render_template("admin_swaggers.html", title="Swaggers")

@admin.route("/models", methods=["GET", "POST"])
@login_required
def models_admin():
    if not check_is_admin():
        return redirect(url_for("main.home"))

    settings_form = SettingsForm()
    train_form = TrainNewModelForm()
    register_form = RegisterModelForm()
    try:
        shutil.rmtree("/mlflow/.tmp")
    except FileNotFoundError:
        pass


    if settings_form.predict_all.data and settings_form.validate_on_submit():
        try:
            run_id = models_client.proxy.get_production_run_id()
        except Exception as e:
            flash(f"The following error occured. Nothing has been written to the database. {e}", "danger")
            return redirect(url_for("admin.models_admin"))

        # Get all ungraded docs from db
        docs = Document.find(
                    Exists(Document.content, True),
                    Document.content != "",
                    Document.predictions.run_id != run_id,
                    with_children=True).to_list()
        contents = [doc.content for doc in docs]

        # Compute predictions
        batch_size = settings_form.batch_size.data or settings_form.batch_size.render_kw["placeholder"]
        try:
            predictions = []
            for batch_id in range(0, len(contents), batch_size):
                batch = contents[batch_id: batch_id+batch_size]
                batch_preds = models_client.proxy.relevance_predict(batch, True)
                predictions.extend(batch_preds)
        except Exception as e:
            flash(f"The following error occured. Nothing has been written to the database.{e}", "danger")
            return redirect(url_for("admin.models_admin"))

        # Write to db
        for idx, doc in enumerate(docs):
            if not doc.predictions: doc.predictions = []
            prediction = Prediction(run_id=run_id, prediction=predictions[idx])
            doc.predictions.append(prediction)
        try:
            [doc.save() for doc in docs]
        except Exception as e:
            flash(f"The following error occured. Nothing has been written to the database. {e}", "danger")
            return redirect(url_for("admin.models_admin"))

        if len(docs) != 0:
            flash(f"{len(docs)} predictions have been successfully written to the database.", "success")
        else:
            flash("There is no document to grade with the current Production model.", "info")
        return redirect(url_for("admin.models_admin"))


    if settings_form.empty_bin.data and settings_form.validate_on_submit():
        try:
            gc = models_client.proxy.gc()
            if str(gc["stdout"]) != "" and str(gc["stderr"]) == "":
                flash(f"The recycle bin is now empty. {gc['stdout']}", "success")
            elif str(gc["stderr"]) == "":
                flash(f"There is nothing to delete from Mlflow.", "info")
            else:
                flash(f"An error occured. {gc['stderr']}", "warning")
        except Exception as e:
            flash(f"The following error occured: {e}", "danger")
        return redirect(url_for("admin.models_admin"))


    def fields_in_common(form):
        # Dataloader
        if form.dataloader.data == "fromdb":
            docs = Document.find(
                    Exists(Document.note, True),
                    Exists(Document.content, True),
                    Exists(Document.author, True),
                    Document.note != 0,
                    Document.content != "",
                    Document.author != "",
                    with_children=True).project(DocumentForModelsView).to_list()
            docs = [doc.as_dict() for doc in docs]
        else:
            dataset = form.datafile.data
            filename = secure_filename(dataset.filename)
            os.makedirs("/mlflow/.tmp", exist_ok=True)
            docs = os.path.join("/mlflow/.tmp", filename)
            dataset.save(docs)

        try:
            train_size = int(form.train_size.data) if form.train_size.data % 1 == 0 else float(form.train_size.data)
        except TypeError:
            train_size = None
        try:
            test_size = int(form.test_size.data) if form.test_size.data % 1 == 0 else float(form.test_size.data)
        except TypeError:
            test_size = None

        experiment = None if form.experiment_name.data == "" else form.experiment_name.data

        if "," in form.class_weight.data:
            weights = form.class_weight.data.split(",")
            class_weight = {str(k): float(weights[k]) for k in range(form.labels.data)}
        else:
            class_weight = form.class_weight.data or form.class_weight.render_kw["placeholder"]
        if form.run_tags.data == "":
            tags_dict = None
        else:
            tags = form.run_tags.data.split(",")
            tags_dict = {"run_type": "trained" if form is train_form else "registered"}
            for tag in tags:
                tag = tag.split(":")
                tags_dict[tag[0]] = tag[1]
        return docs, train_size, test_size, experiment, class_weight, tags_dict

    if train_form.train.data and train_form.validate_on_submit():
        docs, train_size, test_size, experiment, class_weight, tags_dict = fields_in_common(train_form)

        run_params = {
                "data": docs,
                "content_col": train_form.content_col.data or train_form.content_col.render_kw["placeholder"],
                "label_col": train_form.label_col.data or train_form.label_col.render_kw["placeholder"],
                "model_type": train_form.model_type.data,
                "labels": train_form.labels.data,
                "inverse_labels": train_form.inverse_labels.data,
                "experiment": experiment,
                "name": train_form.run_name.data,
                "tags": tags_dict,
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
                "class_weight": class_weight,
                }
        try:
            models_client.proxy.relevance_train(run_params, train_params, train_form.evaluate.data)
        except xmlrpc.client.Fault as err:
            flash(f"The following error occured on the server side {err}", "danger")
            return redirect(url_for("admin.models_admin"))

        flash("Your model has been trained successfully.", "success")
        return redirect(url_for("admin.models_admin"))


    if register_form.register.data and register_form.validate_on_submit():
        docs, train_size, test_size, experiment, class_weight, tags_dict = fields_in_common(register_form)

        # Model
        basepath = "/mlflow/.tmp"
        os.makedirs(os.path.join(basepath, "model"), exist_ok=True)
        model = register_form.modelfile.data
        filename = secure_filename(model.filename)
        model.save(os.path.join(basepath, "model", filename))

        config = register_form.configfile.data
        filename = secure_filename(config.filename)
        config.save(os.path.join(basepath, "model", filename))

        # Artifacts
        artifactspath = os.path.join(basepath, "artifacts")
        os.makedirs(artifactspath, exist_ok=True)
        for artifact in register_form.artifacts.data:
            filename = secure_filename(artifact.filename)
            if filename:
                artifact.save(os.path.join(artifactspath, filename))

        run_params = {
                "data": docs,
                "content_col": register_form.content_col.data or register_form.content_col.render_kw["placeholder"],
                "label_col": register_form.label_col.data or register_form.label_col.render_kw["placeholder"],
                "model_type": register_form.model_type.data,
                "labels": register_form.labels.data,
                "inverse_labels": register_form.inverse_labels.data,
                "experiment": experiment,
                "name": register_form.run_name.data,
                "tags": tags_dict,
                "description": register_form.run_description.data
                }
        register_params = {
                "directory": basepath,
                "base_ckpt": register_form.checkpoint.data or register_form.checkpoint.render_kw["placeholder"],
                "test_size": test_size or register_form.test_size.render_kw["placeholder"],
                "batch_size": register_form.batch_size.data,
                "parameters": {
                    "epochs": register_form.epochs.data,
                    "class_weight": class_weight,
                    "train_only_head": register_form.only_head.data,
                    "train_size": train_size or register_form.train_size.render_kw["placeholder"],
                    "initial_lr": register_form.initial_lr.data,
                    "final_lr": register_form.final_lr.data,
                    }
                }

        try:
            models_client.proxy.relevance_register(run_params, register_params, register_form.evaluate.data, register_form.only_head.data)
        except xmlrpc.client.Fault as err:
            flash(f"The following error occured on the server side {err}", "danger")
            return redirect(url_for("admin.models_admin"))

        flash("Your model has been registered successfully.", "success")
        return redirect(url_for("admin.models_admin"))

    else:
        if request.method == "POST":
            flash("Correct all errors on the form below to train your model.", "danger")

    return render_template("admin_models.html", title="Models Administration", settings_form=settings_form, train_form=train_form, register_form=register_form)


@admin.route("/stats", methods=["GET", "POST"])
@login_required
def stats():
    if not check_is_admin():
        return redirect(url_for("main.home"))

    # Query db and build DataFrame
    documents = Document.find(
            Exists(Document.author),
            Exists(Document.content),
            Document.author != "",
            Document.content != "",
            with_children=True).to_list()

    docs = [doc.as_dict() for doc in documents]
    for doc in docs:
        # We keep the last prediction only, if it exists
        try:
            doc["prediction"] = doc["predictions"][-1].prediction[-1] * 100
        except TypeError:
            doc["prediction"] = np.nan
        doc.pop("predictions")
    docs = pd.DataFrame(docs)
    docs["content"].replace("", np.nan, inplace=True)
    docs.dropna(subset=["content"], inplace=True)
    docs["note"].replace(0, np.nan, inplace=True)
    users = User.find().to_list()

    # Counts
    counts = docs.nunique()
    doc_count = len(docs)
    author_count = counts["author"]
    note_count = doc_count - len(docs[docs["note"].isna()])
    pc_note = round(note_count / doc_count * 100, 2)

    # Top contributors
    contribs = docs.value_counts("author")
    contribs = contribs.reset_index()
    contribs["author_short"] = contribs["author"].apply(lambda x: x[0:20])
    top10 = contribs[:10]
    fig = px.bar(top10[::-1], x="count", y="author_short", hover_data=["author", "count"], labels={"count": "Number of documents", "author_short": "author"}, color_discrete_sequence =["#1cc88a"], orientation="h")
    contributors = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Histos
    fig = px.histogram(docs, x="note", labels={"note": "Grades"}, color_discrete_sequence=["#3abacd"])
    grades_histo = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    fig = px.histogram(docs, x="prediction", labels={"prediction": "Predictions"}, color_discrete_sequence=["#3abacd"])
    preds_histo = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    # Best authors by grade and pred (only keep top10 contributors)
    group_by_auth = docs[docs["author"].isin(top10["author"])].groupby(["author"])
    group_by_auth = group_by_auth[["note", "prediction"]].mean()
    group_by_auth = group_by_auth.reset_index()
    group_by_auth["author_short"] = group_by_auth["author"].apply(lambda x: x[0:20])
    group_by_auth["note"] = group_by_auth["note"].round(2)
    group_by_auth["prediction"] = group_by_auth["prediction"].round(2)
    fig = px.bar(group_by_auth, x="note", y="author_short", color_continuous_scale="greens_r", color="note", hover_data=["author", "note"], labels={"note": "Average grade", "author_short": "author"})
    best_grade_auth = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    fig = px.bar(group_by_auth, x="prediction", y="author_short", color_continuous_scale="greens", color="prediction", hover_data=["author", "prediction"], labels={"prediction": "Average predicted score", "author_short": "author"})
    best_pred_auth = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template(
            "admin_stats.html",
            title="Statistics",
            doc_count=doc_count,
            author_count=author_count,
            user_count=len(users),
            note_count=note_count,
            pc_note=pc_note,
            contributors=contributors,
            grades_histo=grades_histo,
            preds_histo=preds_histo,
            best_grade_auth=best_grade_auth,
            best_pred_auth=best_pred_auth,
            )
