# RAPPORT FINAL MAINTiDOC — état du 29 octobre 2026

**Le projet n'est pas déclaré terminé ni intégralement conforme.** Les composants
locaux ci-dessous ont été intégrés et vérifiés ; la génération nominale VLM,
les services Docker et l'expérimentation supervisée restent non validés.

Projet principal : `C:\Users\Sasam\OneDrive\Desktop\MAINTiDOC_phase1_correction`.
Référence : cahier des charges officiel transmis dans la conversation le 29/10/2026.

## 1. Protection et état initial

- Sauvegarde initiale vérifiée : `backup_code_20261029_095812.zip`, 32 fichiers de code/configuration.
- Les 309 fichiers de données initiaux sont inchangés, vérifiés par SHA-256.
- Aucun PDF, embedding, index, image ou résultat initial n'a été supprimé ou remplacé.
- Corpus existant : 7 PDF, deux familles, 228 pages extraites, 1 256 passages,
  embeddings textuels de dimension 384. Aucun nouveau document téléchargé.
- L'ancien environnement `.venv` Python 3.14 est conservé. L'intégration utilise
  `.venv311` Python 3.11.15 ; aucun import depuis l'environnement Miniconda global.
- Les changements ont été faits dans le dossier principal, sans mélange avec
  l'ancien projet Codex situé dans Documents/ChatGPT.

## 2. Composants implémentés et vérifiés

| Composant | Preuve et portée |
|---|---|
| Recherche textuelle sur corpus autorisé | Réemploi effectif des vecteurs existants et de l'encodeur multilingue ; contrôle d'alignement (1256,384) |
| Recherche visuelle multilingue CLIP | Deux encodeurs provisionnés ; index 228 pages x 512 dimensions ; les 218 premiers vecteurs ont été réutilisés et seules 10 pages supplémentaires encodées |
| RRF et reranking CrossEncoder | Recherche combinée réellement exécutée en 8,375 s après préchargement ; classement et citations conservés dans `reports/multimodal_retrieval_smoke.json` |
| Catalogue et tableaux | Nouveau catalogue de 511 éléments existants ; catalogue enrichi de 623 éléments dont 112 tableaux détectés automatiquement, avec cellules et contexte ; extraction automatique à relire avant usage technique |
| Références et Evidence Check | Pydantic strict, vérification sémantique par affirmation, contrôle des extraits exacts, citations, repères, couverture des phrases, terminologie bilingue ; tests locaux sur une page réelle et modèles simulés |
| LangGraph | États et transitions explicites ; deux graphes dont interruption et reprise pour approbation ; parcours testé avec doublures de modèles |
| MCP réel | Client/serveur stdio, trois outils fictifs, autorisation serveur, jetons liés au contenu/utilisateur, expiration et idempotence ; essais réels réussis |
| API FastAPI | Authentification, quotas, accès aux sources, analyse, historique et parcours de tickets ; HTTP réel : santé 200, source autorisée 200, source interdite 403, historique MCP 200 |
| Streamlit | Trois onglets question/sources, historique et tickets ; tests AppTest, purge au changement d'identité ; serveur répond réellement sur 8501 |
| Sessions | Historique en mémoire, dix tours maximum, expiration après trente minutes, séparation par utilisateur et session testée |
| Budgets et sécurité | Six appels modèle au total, embeddings/reranking/VLM inclus ; trois MCP ; 60 s par demande ; limite d'image/contexte/tokens, concurrence 1, quotas ; destinations Ollama fixes et redirections interdites |
| Dépendances et préparation | 25 dépendances directes figées, résolution complète de 166 distributions, `uv pip check` compatible ; Docker Compose validé syntaxiquement ; CI fournie |

Les versions inconnues des documents restent `null`. Les groupes de
`config/document_access.json` sont une politique de démonstration explicitement
configurée, pas des métadonnées déduites ou des autorisations légales inventées.
Les révisions et licences déclarées des modèles se trouvent dans
`reports/model_provenance.json`. Les métadonnées de licence des dépendances sont
conservées dans `reports/dependency_licenses.json` ; cela ne remplace pas une
revue de compatibilité de toutes les licences et des droits du corpus.

## 3. Résultats d'exécution réels

- Dernière suite : **56 tests, 0 échec, 0 erreur, 0 ignoré**.
  Console : 7,75 secondes ; durée XML JUnit : 7.744 secondes.
- Syntaxe vérifiée sur 54 fichiers Python ; aucun module ancien à effet de bord
  n'a été importé uniquement pour vérifier sa syntaxe.
- Historique MCP réel : un appel, 2,016 s.
- Tickets MCP réels : création du ticket fictif 1, répétition retournant le même
  identifiant, contenu modifié refusé ; trois appels, 6,39 s.
- Parcours HTTP réel : préparation, interruption LangGraph, approbation simulée
  par le test (`confirmed=True`), création via MCP du ticket fictif 2 et répétition
  idempotente. Aucune intervention réelle ni connexion à une machine.
- Recherche froide initiale : 95,437 s. Cela dépasse le budget d'une question.
  Le préchargement a donc été déplacé avant l'ouverture de l'API.
- Recherche multimodale après préchargement : 8,375 s, sans composant manquant.
- Essai API multimodal : abstention par `TimeoutError`, 22,75 s ; un appel VLM
  tenté selon le compteur de cette version initiale de l'essai.
- Essai API texte seul avec compteurs définitifs : abstention par `TimeoutError`,
  22,234 s ; trois appels au total (embedding, reranking, VLM).
- Ollama charge qwen2.5vl:3b sur CPU, VRAM constatée à zéro. **Aucune réponse
  nominale complète de génération + vérification sémantique n'a été validée en réel.**

Les tests de modèles simulés prouvent les transitions et contrôles du code,
**pas** la qualité sémantique réelle du VLM. Les deux essais API constituent
seulement des essais de robustesse et de délai, pas une évaluation statistique.
Aucune exactitude, Recall/nDCG/MRR de corpus, latence p95 ou amélioration de
fine-tuning n'est inventée. Les objectifs 90 % et p95 < 30 s ne sont pas acquis.

## 4. Fonctionnalités partielles ou bloquées

1. **Génération nominale VLM** : disponible via Ollama mais délais dépassés sur
   ce CPU. Le prototype s'abstient correctement ; il ne fournit pas encore la
   réponse technique nominale attendue dans les budgets. Il faut optimiser et
   benchmarker le matériel/inférence sans élargir silencieusement les budgets.
2. **Qdrant, PostgreSQL et MinIO** : configurations et adaptateur de
   synchronisation fournis ; le moteur Docker ne répond pas au contrôle borné
   à cinq secondes, malgré la tentative de démarrage de Docker Desktop. Aucun
   déploiement de conteneur ni test intégré de ces services n'est déclaré réussi.
3. **Tickets PostgreSQL** : backend implémenté avec verrou transactionnel et
   validation partagée ; choix explicite, aucun repli SQLite silencieux. Non testé
   contre un vrai serveur. Le mode local vérifié utilise SQLite. Il n'y a pas de
   migration automatique des deux tickets fictifs déjà créés.
4. **MinIO à l'ouverture** : le client de synchronisation existe, mais l'API
   ouvre encore les fichiers locaux autorisés. Ce point doit être intégré et testé.
5. **Fine-tuning** : 1256 candidats de triplets sont préparés,
   **zéro triplet vérifié**. Questions, pertinence et difficulté restent à annoter.
   Les scripts refusent les données non vérifiées et les fuites entre documents.
   Aucun entraînement ni modèle adapté n'a été produit. MLflow est prévu dans le
   script d'entraînement mais aucune expérience réelle n'est déclarée exécutée.
6. **Évaluation complète** : plan de 150 scénarios non annotés, zéro scénario
   annoté de ce plan exécuté. Les 56 tests logiciels sont distincts
   de ce jeu de recette. Comparaison des trois rerankers et évaluation humaine
   des réponses encore nécessaires.
7. **OCR** : chemin d'ingestion préparé, Tesseract absent et OCR non validé.
   Aucune des 228 pages existantes n'est totalement dépourvue de texte extrait.
8. **Corpus** : 7 PDF contre 30 à 50 proposés ; documents autorisés supplémentaires
   et confirmation des droits de réutilisation à fournir par le responsable.
9. **Recette graphique** : Streamlit est testé et répond en HTTP ; la capture
   visuelle du navigateur n'a pas pu être rattachée par l'outil de navigation.
   La recette humaine de l'affichage des photos et des pages reste à effectuer.
10. **Sécurité de production** : identité fictive locale, pas d'OIDC, rotation
    automatique, chiffrement de la base locale ou rate limiter distribué. Pas de
    garantie générale contre les injections à partir de ces seuls tests.
11. **CI et images Docker** : configuration présente, aucune exécution GitHub ni
    construction d'images/recette de déploiement prétendue réalisée.

## 5. Lancer et vérifier

Les deux services locaux ont été lancés et vérifiés : interface
`http://127.0.0.1:8501`, API `http://127.0.0.1:8010/health`.
Le port 8000 appartenait à un autre processus ; il a été laissé intact.

```powershell
cd C:\Users\Sasam\OneDrive\Desktop\MAINTiDOC_phase1_correction
.\.venv311\Scripts\python.exe -m src.bootstrap
.\.venv311\Scripts\python.exe -m pytest -q --junitxml=reports/tests.xml
uv --no-cache pip check --python .venv311\Scripts\python.exe
```

Pour relancer les services s'ils sont arrêtés, dans deux terminaux séparés :

```powershell
.\.venv311\Scripts\python.exe -m uvicorn src.api:app --host 127.0.0.1 --port 8010 --no-access-log
.\.venv311\Scripts\python.exe -m streamlit run ui/app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

Attendre la fin du préchargement. Ouvrir localement le fichier
`.local/technicien-demo.token` dans un éditeur, puis saisir le jeton dans
l'interface. Ne pas publier son contenu. Le compte `lecteur-demo` permet de
vérifier les refus d'accès. Les secrets et jetons locaux sont exclus de Git et
des rapports ; ils n'ont pas été affichés dans les sorties.

## 6. Préparer la démonstration complète

1. Vérifier les tests et les empreintes des fichiers d'origine.
2. Résoudre le démarrage Docker et exécuter la synchronisation des services.
3. Valider la génération nominale et l'analyse d'une photographie dans les budgets.
4. Compléter les annotations et droits du corpus ; entraîner puis comparer les
   rerankers sur des documents disjoints avec les résultats réellement obtenus.
5. Exécuter et annoter les 150 scénarios ; mesurer médiane, p95, ressources et
   qualité des citations ; consigner aussi les échecs.
6. Suivre `docs/DEMONSTRATION.md` : source/image, clarification, accès refusé,
   injection, historique MCP et ticket approuvé. Présenter les limites réelles.

Les résultats machine détaillés sont dans `reports/verification_summary.json`,
`reports/tests.xml`, `reports/live_services.json`, `reports/live_ticket_flow.json`,
`reports/mcp_ticket_smoke.json` et les essais API/recherche du même dossier.
