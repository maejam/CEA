
import json
import pymongo
from scholarly import scholarly
from serpapi import GoogleSearch

client = pymongo.MongoClient("mongodb+srv://max:MotDePasse@cluster0.c6tvtyy.mongodb.net/?retryWrites=true&w=majority")
db = client.gettingStarted
Research_paper = db.Research_paper

keyword = input("Enter a keyword you want in the summary of the document ")

query = {"snippet": {"$regex": ".*" + keyword + ".*"}}
testtt = Research_paper.find(query)

for result in testtt:
    print("Title : " + result['title'])
    print("Summary :" + result['snippet'])
