# Pre-requis Base de données
Mongo est up and running sur le port 27017, avec une base CEA et une collection Document
(Voir dossier CEA_mongo)
# Creer votre environnement virtuel en python 3.9
Vous pouvez utiliser conda ou venv
## Avec conda :
Si besoin supprimer l'environnement existant:  
`conda remove -n CEA_Flask --all`  
Puis créer un nouvel environnement:  
`conda create --name CEA_Flask python=3.9`  
`conda activate CEA_Flask`
# Installer les librairies
`pip install -r requirements.txt`
# Lancer l'application Flask
1. `python run.py`
2. Verifier : http://127.0.0.1:5000

# Note
Pour le reset password, la route `/reset_password` n'est pas encore branchée

https://startbootstrap.com/theme/sb-admin-2 est le template utilisé pour le look & feel de l'application.
