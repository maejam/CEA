#Load content of example.json in my_json
import json
with open('example.json', mode='r', encoding='utf-8') as f:
    my_json = json.load(f)

# ATTENTION : c'est crud_api:8000 et non pas localhost:8000 qu'il faut utiliser dans les conteneurs
# Call api localhost:8001/document/bulk_insert_linkedin with my_json as body
import requests
r = requests.post('http://localhost:8001/document/document/bulk_linkedin/', json=my_json)
print(r.status_code)
print(r.text)

