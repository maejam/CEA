from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from bson.objectid import ObjectId
from pydantic import BaseModel
import datetime
from typing import List, Dict, Union
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

app = FastAPI()

client = MongoClient("mongodb://mongo:27017/")
db = client["CEA"]
document_collection = db["Document"]

class Document(BaseModel):
    url: Optional[str] = None
    content: str
    links: Optional[List[str]] = None
    author: str
    date: str
    img: Optional[List[str]] = None
    comments: Optional[List[str]] = None
    note: Optional[int] = None
    doc_id: Optional[int] = None
    DistilbertForClassification_v1: Optional[float] = None
    notes: Optional[Dict[str, Union[int, float]]] = None
    _class_id: Optional[str] = None

class DocumentInDB(Document):
    id: str

@app.post("/document/")
def create_document(document: Document):
    new_doc = document_collection.insert_one(document.dict())
    return {"id": str(new_doc.inserted_id)}

@app.get("/document/{document_id}")
def get_document(document_id: str):
    document = document_collection.find_one({"_id": ObjectId(document_id)})
    if document:
        return document
    else:
        raise HTTPException(status_code=404, detail="Document not found")

@app.put("/document/{document_id}")
def update_document(document_id: str, document: Document):
    result = document_collection.update_one({"_id": ObjectId(document_id)}, {"$set": document.dict()})
    if result.modified_count:
        return {"detail": "Document updated"}
    else:
        raise HTTPException(status_code=404, detail="Document not found")

@app.delete("/document/{document_id}")
def delete_document(document_id: str):
    document = document_collection.find_one({"_id": ObjectId(document_id)})
    if document:
        document_collection.delete_one({"_id": ObjectId(document_id)})
        return {"detail": "Document deleted"}
    else:
        raise HTTPException(status_code=404, detail="Document not found")

@app.post("/document/bulk/")
def bulk_insert_documents(documents: List[Document]):
    docs = [doc.dict() for doc in documents]
    result = document_collection.insert_many(docs)
    return {"inserted_ids": [str(id) for id in result.inserted_ids]}

from fastapi import FastAPI, Body
from typing import List, Dict

@app.post("/document/bulk_linkedin/")
def bulk_insert_linkedin_documents(documents: List[Dict] = Body(...)):
    docs = [doc for doc in documents]
    docs_to_insert = []
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    for doc in docs:
        #Create a new empty document, of type Document, with only mandatory fields
        #content, author and date
        mydoc =  {}
        mydoc["content"] = doc["content"]
        mydoc["author"] = doc["author"]
        mydoc["date"] = current_date

        mydoc["url"] = "https://www.linkedin.com/feed/update/urn:li:activity:" + doc["postID"]
        mydoc["notes"] = {"label":0}
        mydoc["_class_id"] = "Document.LinkedIn"
        logging.info(mydoc["url"])
        if document_collection.find_one({"url": {"$regex": "^" + mydoc["url"]}}):
            logging.info("Document already in the db")
        else:
            doc["_class_id"] = "Document.LinkedIn"
            logging.info("--------------------")
            logging.info(mydoc)
            logging.info("--------------------")
            logging.info("Document not in the db")
            docs_to_insert.append(mydoc)
    result = document_collection.insert_many(docs_to_insert)
    #return {"status": "not implemented"}
    return {"inserted_ids": [str(id) for id in result.inserted_ids]}