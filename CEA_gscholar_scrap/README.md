## Avec conda pour lancer en local:
Si besoin supprimer l'environnement existant:  
`conda remove -n CEA_gscholar_scrap --all`  
Puis créer un nouvel environnement:  
`conda create --name CEA_gscholar_scrap python=3.9`  
`conda activate CEA_gscholar_scrap`
# Installer les librairies
`pip install -r requirements.txt`

# Scrapping_Google_Scholar

Tout se passe dans le "main".

# Code push and retrieve local host

on lance le serveur uvicorn avec cette commande.

uvicorn main:app --reload --port 8001


on accède au swagger via :

http://127.0.0.1:8001/docs


