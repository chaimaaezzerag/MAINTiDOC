# MAINTiDOC

Assistant documentaire multimodal et agentique pour une démonstration académique
sur la maintenance industrielle. Aucune commande de machine réelle.

Le code et les données historiques sont préservés ; les nouveaux composants
intégrés utilisent Python 3.11 dans `.venv311`.

## Lancement local

```powershell
.\.venv311\Scripts\python.exe -m src.bootstrap
.\.venv311\Scripts\python.exe -m pytest -q
.\.venv311\Scripts\python.exe -m uvicorn src.api:app --host 127.0.0.1 --port 8010 --no-access-log
```

Le jeton personnel est à ouvrir localement dans `.local/technicien-demo.token`,
puis à utiliser pour les appels authentifiés. Il n'est jamais affiché par les scripts.
Attendre la fin du chargement des modèles avant les questions.
Ollama doit servir `qwen2.5vl:3b` sur 127.0.0.1:11434.

## Documentation

- `docs/INSTALLATION_WINDOWS.md` : installation, modèles, services et restauration.
- `docs/ARCHITECTURE.md` : composants, budgets, sécurité et écarts de stockage.
- `docs/DEMONSTRATION.md` : parcours de démonstration et conditions préalables.
- `docs/CONFORMITE.md` : correspondance au cahier des charges.
- RAPPORT_FINAL_MAINTIDOC.md présente les résultats et limites.
- `requirements.txt` : dépendances directes figées ; `requirements.lock.txt` : résolution complète.

## Corpus et protection

`data/raw/pompes` et `data/raw/vannes` contiennent les PDF originaux.
`data/processed` conserve les résultats existants et les nouveaux catalogues.
`config/document_access.json` définit une politique locale de démonstration.
Les versions documentaires inconnues restent nulles. Aucun document supplémentaire
n'a été téléchargé. Les licences et droits du corpus doivent être confirmés.

Le manifeste historique reste utilisable avec `python -m src.manifest` : il
accepte les PDF ouvrables avec un mot de passe vide, laisse les originaux intacts
et consigne les échecs dans `manifest_errors.csv`. Ne pas relancer sans nécessité
les extractions et embeddings déjà disponibles.

Le mode local NumPy/SQLite est explicitement distinct des services Qdrant,
PostgreSQL et MinIO configurés dans Docker Compose. L'absence de modèle, d'index
CLIP ou de preuve est signalée ; aucune réponse technique n'est présentée comme
vérifiée si les contrôles échouent. Le projet n'est pas déclaré intégralement
conforme : consulter le rapport final avant une soutenance.

## Livrable 1

Les [diagrammes](docs/diagrammes/) sont disponibles. Le corpus local réunit 30 documents pédagogiques sur les pompes industrielles (famille 1) et les vannes industrielles (famille 2). Les supports de démonstration décrivent des équipements fictifs. Le corpus, son inventaire et le journal des prompts restent en attente de diffusion. Deux scans physiques et les relectures humaines restent à compléter.
