# Matrice de validation — avant corrections

Référence : CAHIER_DES_CHARGES_REFERENCE.md, issue du texte officiel fourni.

| Exigence du professeur | Implémentation | Test | Résultat constaté | Élément manquant |
|---|---|---|---|---|
| Fidélité documentaire | src/evidence_check.py | tests/test_runtime.py | 56 tests de la suite précédente ; nouvelle validation requise | Liaisons terme-repère et erreurs de verdict du modèle à renforcer |
| RAG texte/image, RRF, reranker | src/retrieval.py + index CLIP | reports/multimodal_retrieval_smoke.json | Exécuté au passage précédent ; à rejouer | Réponse nominale VLM non validée |
| Réponse multimodale dans 60 s | src/ollama_client.py + workflow.py | Essais réels Ollama/API | Sonde actuelle OK : 8,875 s dont chargement 8,300 s | Optimiser contexte et allocation de délai |
| MCP et approbation | src/mcp_server.py + approval_flow.py | Tests unitaires et parcours HTTP réel précédent | Réussi au passage précédent ; régression à rejouer | Intégration PostgreSQL à valider |
| Contrôles d’accès et interface | src/security.py + api.py + ui/app.py | Tests réels HTTP + AppTest | Réussi au passage précédent ; à rejouer | Recette graphique et erreurs à étendre |
| Qdrant/PostgreSQL/MinIO/MLflow | compose.yaml + service_storage.py | docker info + intégration | Service Docker constaté arrêté | Démarrage et intégration réels |
| Fine-tuning et comparaison | scripts/train_reranker.py + evaluate_rankings.py | Triplets et classements vérifiés | 1256 candidats non vérifiés ; aucun entraînement | Annotations et expérience réelles |
| Évaluation environ 150 scénarios | data/evaluation/scenario_plan.jsonl | Scénarios annotés | Plan uniquement, non exécuté | Cas concrets et évaluation |
| Livrables et soutenance | README + docs + rapports | Contrôle documentaire et commandes | Documentation existante | Mettre à jour preuves et verdict final |
