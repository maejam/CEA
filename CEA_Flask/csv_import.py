import csv

from flaskapp.db import init_db
from flaskapp.models import LinkedIn


init_db("172.17.0.2:27017", "CEA")

with open("LinkedInPosts_20220521_2.csv", "r") as f:
    for row in csv.reader(f, delimiter=","):
        if row[0] != "" and row[0] != "author":
            doc = LinkedIn(author=row[0], content=row[1])
            doc.save()
