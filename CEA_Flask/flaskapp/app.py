from flask import Blueprint, render_template, flash, render_template, request, redirect, url_for
from flask_login import login_required
from pydantic.error_wrappers import ValidationError
from bunnet.operators import Exists

from .models import Document, DocumentShortView
from .forms import RatingForm, SummaryForm
from models_client import proxy


main = Blueprint("main", __name__)


@main.route("/")
@main.route("/home")
@login_required
def home():
    documents = (Document.find(
                            Exists(Document.content),
                            Exists(Document.author),
                            with_children=True)
                            .aggregate([
                                {"$addFields": {"lastPred": {"$last": "$predictions.prediction"}}},
                                {"$addFields": {"prediction": {"$last": "$lastPred"}}},
                                ],
                                projection_model=DocumentShortView
                                )
                        .to_list())
    documents = [doc.as_dict() for doc in documents]
    headers = ("", "Type", "Author", "Content", "Date", "Score")
    return render_template("home.html", title="Documents", headers=headers, data=documents)


@main.route("/document/<string:doc_id>", methods=["GET", "POST"])
@login_required
def document(doc_id):
    try:
        document = Document.get(doc_id, with_children=True).run()
    except ValidationError as e:
        return render_template("404.html", error=e)
    rating_form = RatingForm()
    summary_form = SummaryForm()

    if rating_form.rate.data and rating_form.validate_on_submit():
        document.note = rating_form.rating.data
        document.save()
        flash("Your rating for this document has been saved!", "success")
        return redirect(url_for("main.document", doc_id=doc_id))
    if summary_form.summarize.data and summary_form.validate_on_submit():
        summary_form.max_words.data = summary_form.max_words.data or summary_form.max_words.render_kw["placeholder"]
        summary = proxy.summary_predict(document.content, 30, summary_form.max_words.data, 't5-small')
        summary = summary[0].get("summary_text")
        rating_form.rating.data = document.note
    elif request.method == "GET":
        rating_form.rating.data = document.note
        if "summary" not in locals():
            summary = None
    return render_template("document.html", document=document, rating_form=rating_form, summary_form=summary_form, summary=summary)
