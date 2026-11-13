# Installation et lancement Windows

Projet principal : `C:\Users\Sasam\OneDrive\Desktop\MAINTiDOC_phase1_correction`.
L'ancien environnement `.venv` Python 3.14 est préservé.
Le travail intégré utilise exclusivement `.venv311` Python 3.11.15.

```powershell
cd C:\Users\Sasam\OneDrive\Desktop\MAINTiDOC_phase1_correction
# Environnement existant préparé :
uv --no-cache pip check --python .venv311\Scripts\python.exe
.\.venv311\Scripts\python.exe -m src.bootstrap
.\.venv311\Scripts\python.exe -m pytest -q
```

Pour recréer un environnement sur une autre machine :

```powershell
uv venv --python 3.11 .venv311
uv --system-certs pip install --python .venv311\Scripts\python.exe -r requirements.lock.txt
```

Ne pas désactiver SSL ni utiliser `--trusted-host`. Le téléchargement PyTorch
sur son index CPU a échoué sur un certificat ; les paquets ont été installés
via l'index PyPI avec TLS vérifié. Le provisionnement Hugging Face utilise
`truststore` pour les certificats du système. Une erreur persistante exige la
configuration du certificat de l'organisation, pas son contournement.

## Modèles, uniquement si absents

```powershell
.\.venv311\Scripts\python.exe -m scripts.provision_models --kind text --cached-only
.\.venv311\Scripts\python.exe -m scripts.provision_models --kind reranker
.\.venv311\Scripts\python.exe -m scripts.provision_models --kind clip-image
.\.venv311\Scripts\python.exe -m scripts.provision_models --kind clip-text
.\.venv311\Scripts\python.exe -m scripts.build_clip_index
```

Chaque modèle provisionné conserve son identifiant, sa révision et sa licence
connue dans `.local/models`. Aucun code distant de modèle n'est exécuté.
Un modèle déjà présent ou un index CLIP existant n'est pas écrasé.
Les modèles incomplets ou inaccessibles doivent être signalés dans le rapport.

## API et interface — deux terminaux

Ollama doit être disponible localement avec `qwen2.5vl:3b`.

```powershell
# Terminal 1 : attendre « Application startup complete ».
.\.venv311\Scripts\python.exe -m uvicorn src.api:app --host 127.0.0.1 --port 8010 --no-access-log
# Terminal 2 :
.\.venv311\Scripts\python.exe -m streamlit run ui/app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

Ouvrir l'interface sur http://127.0.0.1:8501. Ouvrir localement le fichier
`.local/technicien-demo.token` dans un éditeur et copier son contenu dans le champ
mot de passe « Jeton personnel ». Ne pas le publier ni le coller dans les logs.
Le jeton de `lecteur-demo` permet de démontrer les accès refusés.

Les autorisations sont définies dans `config/document_access.json` et
`.local/auth.json`. Le chargement initial peut être long sur OneDrive ; il est
séparé du budget d'une question. Les réponses techniques sont refusées si le
VLM échoue, si la preuve manque ou si la vérification n'est pas concluante.

## Services requis par l'architecture cible

`.env` contient des secrets de démonstration locaux générés, exclus de Git.
Le modèle `.env.example` est vide de secrets. Ne jamais exécuter `docker compose
config` sans `--quiet` dans un journal partagé : cela afficherait ces variables.

```powershell
docker compose config --quiet
docker compose up -d qdrant postgres minio mlflow
# Compléter les variables de connexion de .env puis :
.\.venv311\Scripts\python.exe -m dotenv run -- .\.venv311\Scripts\python.exe -m src.service_storage
```

Le service produit le nom de la collection Qdrant à utiliser dans
`MAINTIDOC_QDRANT_COLLECTION`. Le mode local NumPy est explicitement distinct.
Le profil Compose `app` prépare l'API conteneurisée ; il n'est pas validé tant
que son image et les services n'ont pas été construits puis testés ensemble.
L'interface Streamlit se lance actuellement sur l'hôte Windows.

## Retour arrière

Le ZIP `backup_code_*.zip` contient le code initial. Les fichiers de données
existants n'ont pas été écrasés. Vérifier `audit_data_hashes.json` avant toute
restauration. Arrêter les services sans `docker compose down -v` pour conserver
les volumes. Aucun effacement automatique n'est prévu.

## Points constatés sur cette machine

Le port 8000 est occupé par un autre processus : le projet utilise le port 8010.
Le moteur Docker ne répond pas au contrôle borné à cinq secondes.
Les modèles CLIP sont maintenant provisionnés sans liens symboliques Windows.
L’index complet de 228 pages a réutilisé les 218 vecteurs du premier index.
Les essais Ollama sur CPU aboutissent actuellement à une abstention par délai ;
ils ne prouvent pas une génération nominale fonctionnelle.

Pour tester le backend PostgreSQL des tickets après démarrage des services :

```powershell
$env:MAINTIDOC_TICKET_BACKEND = "postgres"
# Fournir MAINTIDOC_POSTGRES_DSN par le fichier .env local, jamais dans les journaux.
# Relancer ensuite API et client/serveur MCP dans cet environnement.
```

Le mode PostgreSQL ne migre pas automatiquement les tickets fictifs SQLite et
ne revient pas silencieusement à SQLite en cas d’erreur.
