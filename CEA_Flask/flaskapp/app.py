from flask import Blueprint, render_template
from pydantic.error_wrappers import ValidationError

from .models import Document, DocumentShortView


main = Blueprint("main", __name__)


@main.route("/")
@main.route("/home")
def home():
    documents = Document.find(with_children=True).project(DocumentShortView)
    headers = ("", "Type", "Author", "Content", "Date")
    return render_template("home.html", title="Documents", headers=headers, data=documents)


@main.route("/document/<string:doc_id>")
def document(doc_id):
    try:
        document = Document.get(doc_id, with_children=True).run()
    except ValidationError as e:
        return render_template("404.html", error=e)

    return render_template("document.html", document=document)
