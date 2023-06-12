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

### Ajouter une route qui supprime tous les documents dans l'attribut date est un attribut donné, par exemple "2023-06-11"
@app.delete("/document/date/{date}")
def delete_document_date(date: str):
    result = document_collection.delete_many({"date": date})
    return {"detail": f"{result.deleted_count} documents deleted"}


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
    logging.info("/document/bulk_linkedin/")
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
        # Affiche le contenu des attributs du doc , sauf pour contenu, ou on tronque le contenu à 10 caractères, si il en fait plus, et sinon on le laisse as is
        logging.info("--------------------")
        logging.info("Document to insert:")
        for key, value in mydoc.items():
            if key == "content":
                logging.info(f"{key}: {value[:10]}")
            else:
                logging.info(f"{key}: {value}")

        if document_collection.find_one({"url": {"$regex": "^" + mydoc["url"]}}):
            logging.info("Document already in the db")
        else:
            logging.info("--------------------")
            logging.info(mydoc)
            logging.info("--------------------")
            logging.info("Document not in the db, append it to document to insert")
            docs_to_insert.append(mydoc)
    if len(docs_to_insert) == 0:
        return {"inserted_ids": []}
    else:
        result = document_collection.insert_many(docs_to_insert)
        return {"inserted_ids": [str(id) for id in result.inserted_ids]}

# Mettre à jour la date de tous les documents qui n'ont pas le format de date "YYYY-MM-DD"
# en utilisant la date YYYY-MM-DD passée en paramètre
@app.put("/document/date/{date}")
def update_document_date(date: str):
    """
        Mettre à jour la date de tous les documents qui n'ont pas le format de date "YYYY-MM-DD"
        en utilisant la date YYYY-MM-DD passée en paramètre
    """
    if not isinstance(date, str):
        raise HTTPException(status_code=400, detail="Date must be a string")
    if not date:
        raise HTTPException(status_code=400, detail="Date must not be empty")
    if not date[0:4].isdigit() or not date[5:7].isdigit() or not date[8:10].isdigit():
        raise HTTPException(status_code=400, detail="Date must have the format YYYY-MM-DD")
    if len(date) != 10:
        raise HTTPException(status_code=400, detail="Date must have the format YYYY-MM-DD")
    result = document_collection.update_many({"date": {"$not": {"$regex": "^\d{4}-\d{2}-\d{2}$"}}}, {"$set": {"date": date}})
    return {"detail": f"{result.modified_count} documents updated"}
