- CEA_mongo : lancement de la BD Mongo, eventuellement reprise depuis dernier backup  
- CEA_Flask : IHM  
- CEA_linkedin_scrap : Recuperation posts  
- Scrapping_Google_Scholar : Recuperation posts Google scholar 

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

### Repo "deploy"
Ce qui a été fait pour initialiser le repo "deploy" :
<pre>
git clone git@github.com:e-gava/CEA_CFR_deploy.git
cd CEA_CFR_deploy/
git remote add upstream git@github.com:e-gava/CEA_CFR.git
git fetch upstream
git merge upstream/main
git push origin main
</pre>
Ce qu'il faut faire pour les mises à jour :  

1 - Si vous n'avez pas le repo "CEA_CFR_deploy" en local :
<pre>
git clone git@github.com:e-gava/CEA_CFR_deploy.git
cd CEA_CFR_deploy/
</pre>

2  - Dans tous les cas
<pre>
git remote add upstream git@github.com:e-gava/CEA_CFR.git
git fetch upstream
git checkout main
git merge upstream/main
git push origin
</pre>
