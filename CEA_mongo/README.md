# Base de données
Prérequis: Docker installé
1. Télécharger l'image MongoDB depuis le DockerHub: `docker pull mongo`
2. Lancer le container: `docker run -tid -p 27017:27017 --rm mongo`
3. Lancer init_db_if_empty.py