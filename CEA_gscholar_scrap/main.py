from fastapi import FastAPI
from serpapi import GoogleSearch
from pickle_utils import save_to_pickle_object, pickle_load_file
import datetime
import requests
import logging

DEBUG = False

description = """
CEA GoogleScholar API helps you insert and get GoogleScholar results. 

## Users

You will be able to:

* **Insert data** 
* **Read data**

## API_KEY

You can use this api_key **22ae1c4c9a1b15f10c6b1ed0674a1fe0838cd4428858d52641f3a3537cfbf69f**

You can use this keyword for test purpose : ecoinnovation

"""

app = FastAPI(
    title="CEA GoogleScholar",
    description=description,
    contact={
        "name": "CEA TEAM",
        "email": "maxime.danglot@grenoble-em.com",
    },
)

def get_list_of_articles(keyword : str, api_key : str):
    if not DEBUG:
        params = {
            "engine": "google_scholar",
            "q": keyword,
            "api_key": api_key
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        #Check if organic_results is in results
        if 'organic_results' in results:
            final_result = results['organic_results']
        else:
            final_result = []
            logging.warning(f"Missing key in {results}")
        # final_result is a list of dict, convert it to a json file
        # save_to_pickle_object(final_result, 'final_result.pkl', './')
    else:
        final_result = pickle_load_file('final_result.pkl', './')


    new_list = []

    for item in final_result:
        try:
            new_dict = {}
            new_dict["url"] = item["link"]
            new_dict["author"] = ", ".join([author["name"] for author in item["publication_info"]["authors"]])
            new_dict["date"] = datetime.datetime.now().strftime("%Y-%m-%d")
            new_dict["content"] = item["snippet"]
            new_dict["_class_id"] = "Document.Gscholar"
            new_list.append(new_dict)
        except KeyError:
            logging.warning(f"Missing key in {item}")
            pass
    return new_list

@app.get("/GoogleScholar/{keyword}")
def get(keyword : str, api_key : str):
    return get_list_of_articles(keyword, api_key)

#Same but after to the insert calling an api
@app.get("/GoogleScholar/insert/{keyword}")
def insert(keyword : str, api_key : str):
    new_list = get_list_of_articles(keyword, api_key)
    url = 'http://crud_api:8000/document/document/bulk/'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }
    response = requests.post(url, json=new_list, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return response.status_code, response.reason


