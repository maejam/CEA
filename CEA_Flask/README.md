# Installer les librairies
`pip install -r requirements.txt`

# Base de données
Prérequis: Docker installé
1. Télécharger l'image MongoDB depuis le DockerHub: `docker pull mongo`
2. Lancer le container: `docker run -tid --rm mongo`
3. Charger le fichier csv: `python csv_import.py`

# Lancer l'application Flask
1. `python run.py`
2. Le serveur se lance. Cliquer sur le lien qui s'affiche (normalement, `127.0.0.1:5000`)

# Utilisation de l'application
Je n'ai pas encore pris le temps d'ajouter des liens de navigation et des styles.
Il faut visiter directement les urls suivantes:

`/home`: page d'accueil (table avec l'ensemble des posts)  
`/document/<docid>`: la page dédiée à chaque document  
`/register`: formulaire de création de compte  
`/login`: formulaire de connexion  
`/logout`: deconnexion  
`/account`: profil utilisateur  
`/reset_password`: demande d'un nouveau mot de passe (envoie mail avec lien+token vers formulaire).
