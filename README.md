### Les Services
- CEA_mongo : lancement de la BD Mongo, eventuellement reprise depuis dernier backup  
- CEA_Flask : IHM  
- CEA_linkedin_scrap : Recuperation posts  
- Scrapping_Google_Scholar : Recuperation posts Google scholar
- CEA_crud : une proposition de service rest api pour les user et les documents

###  Lancement de l'application
Pour lancer l'appli:
<pre>
docker-compose -f docker-compose.yml --env-file dev.env up
</pre>

En cas de changements dans le code, il faut reconstruire les containers :
<pre>
docker compose -f docker-compose.yml --env-file dev.env up --build
</pre>

Pour lancer en local sur un poste de dev :  
remplacer dev.env par dev.env.local  
<pre>
docker-compose -f docker-compose.yml --env-file dev.env.local up  
docker compose -f docker-compose.yml --env-file dev.env.local up --build
</pre>
Et acceder à l'appli sur http://localhost:5000

### Acces services
Swagger UI  
http://localhost:8000/user/docs    
http://localhost:8000/document/docs  (en cours de dev) 

### User admin
Ceci est une solution temporaire pour administrer l'application.   

Dans CEA_mongo/init_db__if_empty.py, on cree en dur un user admin
username = "admin"  
email = "admin@local.host"  
password = "admin123" (modifier le mot de passe dans CEA_mongo/init_db__if_empty.py )
is_admin = true

Lors de chaque deploiement :

1/ Modifier ce mot de passe dans CEA_mongo/init_db__if_empty.py
2/ Lancer l'application une premier fois via docker-compose 
3/ Commenter le bloc de code dans CEA_mongo/init_db__if_empty.py qui modifie le mot de passe

### Repo "deploy"
Ce qui a été fait pour initialiser le repo "deploy" :
<pre>
git clone git@github.com:e-gava-org/CEA_CFR_deploy.git
cd CEA_CFR_deploy/
git remote add upstream git@github.com:e-gava/CEA_CFR.git
git fetch upstream
git merge upstream/main
git push origin main
</pre>
Ce qu'il faut faire pour les mises à jour :  

1 - Si vous n'avez pas le repo "CEA_CFR_deploy" en local :
<pre>
git clone git@github.com:e-gava-org/CEA_CFR_deploy.git
cd CEA_CFR_deploy/
</pre>

2  - Dans tous les cas
<pre>
git remote add upstream git@github.com:e-gava-org/CEA_CFR.git
git fetch upstream
git checkout main
git merge upstream/main
git push origin
</pre>
