# Conformité au cahier des charges

| Exigence | État et preuve/limite |
|---|---|
| 30 à 50 documents autorisés, deux familles | Deux familles, 7 PDF existants ; autorisations de réutilisation à confirmer par le responsable du corpus |
| Réemploi du corpus | 228 pages, 1256 passages, vecteurs (1256,384), contrôle des empreintes des 309 fichiers initiaux |
| Métadonnées et groupes | Catalogue dérivé et ACL explicite ; versions inconnues nulles |
| Paragraphes, pages, figures | Réemploi des passages et inventaires d'images ; catalogue de 511 éléments |
| Tableaux et OCR | 112 tableaux détectés dans un catalogue distinct ; régression de structure sur une table réelle ; OCR non testé, Tesseract absent, aucune page du corpus sans texte |
| Recherche texte | Réemploi de l'encodeur multilingue et des vecteurs ; essai réel enregistré |
| Recherche visuelle CLIP | Deux encodeurs provisionnés, 228 pages indexées, recherche réellement exécutée |
| Fusion et reranking | RRF et CrossEncoder réellement exécutés ; essai combiné 8,375 s après préchargement, sans métrique de qualité généralisable |
| VLM ouvert | Ollama qwen2.5vl:3b disponible sur CPU ; les deux essais API ont expiré et produit une abstention, génération nominale non validée |
| LangChain et LangGraph | Prompts LangChain, graphes explicites et interruption humaine testés |
| Citations et preuves | Vérification sémantique VLM + contrôles déterministes ; tests unitaires et cas du manuel BAX |
| MCP | Serveur et client réels stdio, historique réellement appelé, contrôles serveur et tests d'approbation |
| Interface/API | FastAPI authentifiée, Streamlit, écran testé ; recette visuelle et intégration complète à effectuer |
| Sécurité | ACL, limites, listes d'outils, idempotence et accès refusés testés ; pas de garantie générale de sécurité |
| Budgets | 3 MCP, 6 modèles incluant embeddings/reranking/VLM, 60 s, limites images/contexte, concurrence 1 ; latence réelle à mesurer, démarrage hors budget |
| Qdrant/PostgreSQL/MinIO | Compose et adaptateur de synchronisation ; pas de conformité de production sans tests des services |
| Tickets PostgreSQL | Backend PostgreSQL ajouté ; intégration réelle non testée, mode local SQLite explicite toujours disponible |
| Fine-tuning | Candidats non vérifiés et garde-fous anti-fuite ; aucun entraînement déclaré effectué |
| 150 scénarios | Plan préparé ; annotations indépendantes et exécution complète manquantes |
| MLflow | Configuration et enregistrement prévus dans le script d'entraînement ; aucune expérience d'entraînement inventée |
| CI | Workflow fourni ; tests locaux exécutés, aucun lancement GitHub prétendu |
| Docker | Syntaxe Compose validée ; démarrage des services et images à vérifier |
| Versions/licences | Paquets installés figés ; révisions modèles disponibles ; revue complète des licences du corpus et du déploiement encore requise |
