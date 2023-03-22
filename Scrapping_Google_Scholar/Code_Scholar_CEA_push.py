import requests
import json
import pymongo
from scholarly import scholarly
from serpapi import GoogleSearch


#Connexion à la base mongo (Cluster ATLAS)
client = pymongo.MongoClient("mongodb+srv://max:MotDePasse@cluster0.c6tvtyy.mongodb.net/?retryWrites=true&w=majority")

#Creation d'une nouvelle database dans mon cluster
db = client.gettingStarted

#Création d'une nouvelle collection
Research_paper = db.Research_paper

CEA_request = input("""Entrer une recherche Google Scholar (Ex : csr nuclear)""")

params = {
  "engine": "google_scholar",
  "q": CEA_request,
  "api_key": "22ae1c4c9a1b15f10c6b1ed0674a1fe0838cd4428858d52641f3a3537cfbf69f"
}

search = GoogleSearch(params)
results = search.get_dict()
test = results['organic_results']

Research_paper.insert_many(test)


