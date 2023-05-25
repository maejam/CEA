from flask import Blueprint, render_template
from flask_login import login_required
from pydantic.error_wrappers import ValidationError

from .models import Document, DocumentShortView


main = Blueprint("main", __name__)


@main.route("/")
@main.route("/home")
@login_required
def home():
    #//TODO : Find a more efficient way to filter documents
    documents = Document.find(with_children=True).project(DocumentShortView)
    # modify to get only document with content that is not empty
    filtered_documents = [doc for doc in documents if doc.content and doc.author]
    headers = ("", "Type", "Author", "Content", "Date","Note")
    return render_template("home.html", title="Documents", headers=headers, data=filtered_documents)


@main.route("/document/<string:doc_id>")
@login_required
def document(doc_id):
    try:
        document = Document.get(doc_id, with_children=True).run()
    except ValidationError as e:
        return render_template("404.html", error=e)

    return render_template("document.html", document=document)
