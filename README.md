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


