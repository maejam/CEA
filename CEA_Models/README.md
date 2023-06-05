### Fonctionnement général
Le service CEA_Models s'appuit sur Mlflow afin d'assurer la tracabilité et
l'évaluation des modèles de prédiction de la pertinence des documents.
Un service de résumé de documents est également proposé.

L'API RPC est accessible sur le port 3000. Les fonctions disponibles sont
décrites dans `api.py`.

### Lors du premier déploiement de l'appli
1. Entrainer ou enregistrer un modèle.
2. Se rendre sur l'interface de Mlflow. Le modèle ajouté apparait dans la liste 
des runs. Cliquer dessus, puis dans la partie `artifacts` en bas, sélectionné le
`model` et cliquer sur `Register Model` à droite.
3. Cliquer sur `Create new model` puis le nommer `relevance` et enfin cliquer sur 
`Register`
4. Se rendre dans l'onglet `Models` (tout en haut de l'interface)
5. Cliquer sur la nouvelle version du modèle de pertinence (`Version 1`), puis 
changer le `Stage` pour `Production`

Toutes les prédictions se feront désormais à partir de cette version.

### Lors de la prédiction
Seuls les documents non évalués par le modèle actuellement en Production seront 
notés. Ce processus peut être gourmand en ram. Le champs `batch_size` permet de
gérer ce problème.

### Ajouter des metrics, des artifacts
Dans le ficher `relevance.py`, la méthode `evaluate` de la classe DocumentRelevanceRun,
à pour résponsabiliter d'ajouter des metrics et artifacts aux runs.
Ajouter des metrics scikit-learn au dictionnaire `metrucs_dict` sous fome de tuples
`(nom_fonction, {paramètres}, nom_à_logguer)`.
Pour les artifacts, tout fichier enregistrer dans `self.tmp_directory` sera loggué.


