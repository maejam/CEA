"""
Ce script doit être exécuté une seule fois pour initialiser la base de données
a partir du dernier backup.
"""
import json
import zipfile
from pymongo import MongoClient
import logging as log
#Les logs sortent dans le terminal
log.basicConfig(level=log.INFO)

# Se connecter à la base de données mongoDB
client = MongoClient('mongodb://127.0.0.1:27017/')
# Check if DB CEA exist, if it doesn't, create it
db = client['CEA']

# Créer la collection Documents si elle n'existe pas
if 'Document' not in db.list_collection_names():
    log.info("La collection Document n'existe pas, elle va être créée")
    db.create_collection('Document')
    documents = db['Document']
    log.info("Initialisation de la collection Document avec le dernier backup")
    # Charger les données depuis le fichier JSON
    zip_file = zipfile.ZipFile('data/LinkedInPosts_20230107.zip', 'r')
    json_file = zip_file.open('LinkedInPosts_20230107.json', 'r')
    data = json.load(json_file)
    # Remplacer les ObjectId par des strings
    from bson.objectid import ObjectId
    for doc in data:
        if "_id" in doc and "$oid" in doc["_id"]:
            doc["_id"] = ObjectId(doc["_id"]["$oid"])
    # Ajouter un attribut _class_id à chaque document
    # égal à "Document.LinkedIn"
    # //TODO : est-ce que _class_id est adequat pour stocker cette information?
    for doc in data:
        doc["_class_id"] = "Document.LinkedIn"
    # Insérer les données dans la collection Documents
    documents.insert_many(data)
    # Fermer les fichiers et la connexion à la base de données
    json_file.close()
    zip_file.close()
    client.close()
else:
    log.info("La collection Document existe déjà. On ne fait rien.")