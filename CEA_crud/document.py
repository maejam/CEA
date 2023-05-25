from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from bson.objectid import ObjectId
from pydantic import BaseModel
import datetime
# Define or import List, Dict, and Union
from typing import List, Dict, Union

app = FastAPI()

client = MongoClient("mongodb://mongo:27017/")
db = client["CEA"]
document_collection = db["Document"]

class Document(BaseModel):
    url: str
    content: str
    links: List[str]
    author: str
    date: str
    img: List[str]
    comments: List[str]
    note: int
    doc_id: int
    DistilbertForClassification_v1: float
    notes: Dict[str, Union[int, float]]
    _class_id: str

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