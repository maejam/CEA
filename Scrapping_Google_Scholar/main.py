from typing import Union
from fastapi import FastAPI
from scholarly import scholarly
from serpapi import GoogleSearch
import json
import pymongo

description = """
CEA GoogleScholar API helps you insert and get GoogleScholar results. 

## Users

You will be able to:

* **Insert data** 
* **Read data**

## API_KEY

You can use this api_key **22ae1c4c9a1b15f10c6b1ed0674a1fe0838cd4428858d52641f3a3537cfbf69f**

"""

app = FastAPI(
    title="CEA GoogleScholar",
    description=description,
    contact={
        "name": "CEA TEAM",
        "email": "maxime.danglot@grenoble-em.com",
    },
)

@app.get("/MongoDB/{keyword}")
def get_from_mongo(keyword: str):
    #--------------- PARTIE MONGO A MODIFIER POUR CEA -----------------
    client = pymongo.MongoClient("mongodb+srv://max:MotDePasse@cluster0.c6tvtyy.mongodb.net/?retryWrites=true&w=majority")
    db = client.gettingStarted
    Research_paper = db.Research_paper #possibilité d'insérer dans d'autres collections
    query = {"snippet": {"$regex": ".*" + keyword + ".*"}}
    response = Research_paper.find(query)
    # -------------------------------------------------------------------

    dico = {}
    for result in response:
        dico[result['title']] = result['snippet']
        
    return json.dumps(dico)


@app.get("/GoogleScholar/{keyword}")
def insert(keyword : str, api_key : str):

    #--------------- PARTIE MONGO A MODIFIER POUR CEA -------------------
    client = pymongo.MongoClient("mongodb+srv://max:MotDePasse@cluster0.c6tvtyy.mongodb.net/?retryWrites=true&w=majority")
    db = client.gettingStarted
    Research_paper = db.Research_paper 
    # -------------------------------------------------------------------
    
    #api_key = "22ae1c4c9a1b15f10c6b1ed0674a1fe0838cd4428858d52641f3a3537cfbf69f" # en argument input

    params = {
        "engine": "google_scholar",
        "q": keyword,
        "api_key": api_key
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    final_result = results['organic_results']

    Research_paper.insert_many(final_result)

    title_list = list()
    for article in final_result:
        title_list.append(article['title'])
    return json.dumps(title_list)