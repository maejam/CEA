# curl -X 'DELETE' \
#   'http://localhost:8001/document/document/646fc7613fc2fa7de5f07d1e' \
#   -H 'accept: application/json'
# ATTENTION : c'est crud_api:8000 et non pas localhost:8000 qu'il faut utiliser dans les conteneurs
import requests
list_id_to_delete = ["646fc875cc7f92ff72658736","646fc875cc7f92ff72658737","646fc875cc7f92ff72658738","646fc875cc7f92ff72658739","646fc875cc7f92ff7265873a","646fc875cc7f92ff7265873b","646fc875cc7f92ff7265873c","646fc875cc7f92ff7265873d","646fc875cc7f92ff7265873e","646fc875cc7f92ff7265873f"]
for id_to_delete in list_id_to_delete:
    r = requests.delete('http://localhost:8001/document/document/'+id_to_delete)
    print(r.status_code)
    print(r.text)