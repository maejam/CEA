from fastapi import FastAPI, Body, HTTPException
from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
from typing import List, Dict, Union
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

app = FastAPI()

client = MongoClient("mongodb://mongo:27017/")
db = client["CEA"]
document_collection = db["Document"]

@app.post("/document/")
def create_document(document: Dict):
    new_doc = document_collection.insert_one(document)
    return {"id": str(new_doc.inserted_id)}

@app.get("/document/{document_id}")
def get_document(document_id: str):
    document = document_collection.find_one({"_id": ObjectId(document_id)})
    if document:
        return document
    else:
        raise HTTPException(status_code=404, detail="Document not found")

@app.put("/document/{document_id}")
def update_document(document_id: str, document: Dict):
    result = document_collection.update_one({"_id": ObjectId(document_id)}, {"$set": document})
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

@app.delete("/document/bulk/")
def bulk_delete_documents(documents: List[str]):
    result = document_collection.delete_many({"_id": {"$in": [ObjectId(id) for id in documents]}})
    return {"detail": f"{result.deleted_count} documents deleted"}

@app.delete("/document/bulk_gscholar/")
def bulk_delete_gscholar_documents():
    result = document_collection.delete_many({"_class_id": "Document.Gscholar"})
    return {"detail": f"{result.deleted_count} documents deleted"}

@app.post("/document/bulk/")
def bulk_insert_documents(documents: List[Dict]):
    docs_to_insert = []
    for doc in documents:
        if document_collection.find_one({"url": doc["url"]}) is None:
            docs_to_insert.append(doc)
    if len(docs_to_insert) == 0:
        return {"inserted_ids": []}
    else:
        result = document_collection.insert_many(docs_to_insert)
        return {"inserted_ids": [str(id) for id in result.inserted_ids]}

@app.post("/document/bulk_linkedin/")
def bulk_insert_linkedin_documents(documents: List[Dict] = Body(...)):
    docs_to_insert = []
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    for doc in documents:
        mydoc = {
            "content": doc["content"],
            "author": doc["author"],
            "date": current_date,
            "url": f"https://www.linkedin.com/feed/update/urn:li:activity:{doc['postID']}",
            "notes": {"label": 0},
            "_class_id": "Document.LinkedIn",
        }
        logging.info(mydoc["url"])
        if document_collection.find_one({"url": {"$regex": "^" + mydoc["url"]}}):
            logging.info("Document already in the db")
        else:
            logging.info("--------------------")
            logging.info(mydoc)
            logging.info("--------------------")
            logging.info("Document not in the db")
            docs_to_insert.append(mydoc)
    result = document_collection.insert_many(docs_to_insert)
    return {"inserted_ids": [str(id) for id in result.inserted_ids]}