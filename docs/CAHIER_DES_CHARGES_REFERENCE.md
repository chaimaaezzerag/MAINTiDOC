# Référence du cahier des charges fourni

Source : texte officiel fourni par l'utilisateur dans cette conversation le 29 octobre 2026.
Cette synthèse distingue les exigences fonctionnelles des choix possibles et objectifs proposés.

## Exigences fonctionnelles

- Assistant documentaire, jamais pilotage de machine ni diagnostic garanti.
- Questions françaises, photographies, documents PDF ; réponses sourcées et clarification.
- Ingestion texte, paragraphes, tableaux, pages, figures ; OCR local des scans.
- Identifiant/version/page/élément/famille/groupes autorisés ; versions inconnues non inventées.
- Recherche textuelle et visuelle sur corpus autorisé, fusion, reranking et VLM ouvert.
- LangChain et LangGraph : transitions, budgets, historique et interruption humaine.
- MCP : get_equipment_history, get_open_tickets et create_ticket ; contrôle serveur.
- Tickets fictifs uniquement ; approbation exacte liée à l'utilisateur/contenu, idempotence.
- FastAPI et Streamlit : authentification, sources autorisées, photo et validation du ticket.
- Prompts versionnés, sorties Pydantic, vérification du soutien réel de chaque affirmation.
- Gestion de l'insuffisance, des contradictions, des photos illisibles et des injections.
- Fine-tuning ciblé d'un reranker multilingue ; séparation documentaire des ensembles.
- Comparaisons sans reranker / initial / adapté ; nDCG@5, MRR@10 et qualité des réponses.
- Qdrant, PostgreSQL et MinIO prévus dans l'architecture de stockage ; MLflow et Compose.
- Tests unitaires/intégration/sécurité, CI, versions figées, documentation et limites.

## Budgets imposés au prototype

3 appels MCP maximum, 6 appels modèle maximum, 60 secondes automatiques par demande,
hors attente humaine ; tailles images/contexte/tokens bornées, quotas et limites de ressources.

## Cadrage et objectifs proposés (pas des résultats acquis)

30 à 50 documents autorisés, deux familles ; 800 à 1500 triplets vérifiés ; environ
150 scénarios répartis en 40 textuels, 30 visuels, 20 MCP, 20 incertitude,
20 autorisations/approbations et 20 injections. Objectifs : au moins 90 % de
citations soutenant leurs affirmations ; aucune fuite/ticket non approuvé dans
les tests ; p95 sous 30 s pour les demandes simples. Le GPU 24 Go est une cible
à benchmarker, pas un matériel constaté. Qwen2.5-VL-7B, Transformers/vLLM et
BGE-M3 sont donnés comme choix possibles ; le projet existant utilise Qwen 3B
via Ollama et un encodeur multilingue comparable de dimension 384.

## Livrables

Cadrage/architecture, dépôt documenté et reproductible, prototype, jeu de test
annoté et résultats, comparaison avant/après adaptation, fiche des limites,
scénario de démonstration et préparation de soutenance. Aucun objectif proposé
ne doit être présenté comme atteint sans mesure réelle.
