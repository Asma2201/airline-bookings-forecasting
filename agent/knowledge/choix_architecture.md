# Choix d'architecture du projet et de l'agent

Ce document décrit comment le projet est organisé : pipeline de prévision, base de données, agent conversationnel et interface. Il décrit ce qui existe dans le code. Les justifications qui n'apparaissent pas dans le code sont marquées "A COMPLETER".

## Pipeline de prévision

### Enchaînement des étapes

Le script main.py enchaîne :

1. Chargement du fichier Excel source (data/raw/Data_stage.xlsx) et nettoyage (typage, reconstruction de la date, valeurs manquantes à 0).
2. Construction de la série globale mensuelle et prévision SARIMA de référence (août à décembre 2026).
3. Construction du panel agence x mois.
4. Prévision par agence par répartition proportionnelle de la prévision globale.
5. Vérification de cohérence entre la somme des agences et le total global.
6. Export des tables pour Power BI.

Le code est découpé en modules dans le dossier src/ (chargement, nettoyage, série globale, modèles globaux, panel agence, variables, modèles agence, prévision agence, export).

### Exports et dashboard Power BI

- Les exports sont des fichiers CSV dans le dossier outputs/, organisés en modèle en étoile : fait_reservations (volumes réels et prévus), dim_agence (caractéristiques des agences), fait_canal (volumes NDC et classique par agence et par mois).
- Contenu et usage du dashboard Power BI : A COMPLETER.

## Base de données de l'agent

- Base SQLite : agent/amadeus_forecast.db.
- Construite par agent/database.py à partir de outputs/fait_reservations.csv et outputs/dim_agence.csv. fait_canal.csv n'y est pas chargé.
- Tables : fait_reservations (date, agence, volume, type_donnee, borne_basse, borne_haute, methode) et dim_agence (agence, volume_total_historique, nb_mois_historique, poids_historique, segment).
- Justification du choix de SQLite : A COMPLETER.

## Agent conversationnel

### Modèle de langage

- Fournisseur : Groq, via la bibliothèque langchain-groq.
- Modèle : openai/gpt-oss-120b, température 0 (réponses aussi stables que possible).
- La clé d'API est lue dans le fichier .env (variable GROQ_API_KEY).
- Justification du choix de Groq et de ce modèle : A COMPLETER.

### Orchestration

- L'agent est un agent à outils construit avec LangChain et LangGraph (fonction construire_agent dans agent/graph.py). Le modèle décide à chaque étape s'il appelle un outil ou s'il répond.
- Un prompt système impose de n'utiliser que les chiffres obtenus en interrogeant la base, de filtrer sur TOTAL_GLOBAL pour un volume global, et de dire clairement quand une question ne peut pas être traitée.
- Justification du choix de LangGraph : A COMPLETER.

### Outils de l'agent

- Outils SQL (SQLDatabaseToolkit de LangChain) : lister les tables, lire leur schéma, vérifier une requête, exécuter une requête sur la base SQLite. Ils donnent les chiffres.
- Outil de documentation (recherche_documentation) : recherche dans les fichiers markdown du dossier agent/knowledge. Il donne la méthodologie, les limites, le vocabulaire et l'interprétation métier.
- Pour une question qui demande un chiffre et une explication, l'agent appelle les deux.

### Recherche documentaire (RAG)

- Corpus : les fichiers markdown du dossier agent/knowledge (interpretation_metier.md, methodologie_modeles.md, limites_donnees.md, glossaire_metier.md, choix_architecture.md).
- Découpage par titres (#, ##, ###), puis par paragraphes si une section est trop longue ; les tableaux ne sont pas coupés.
- Modèle d'embeddings : paraphrase-multilingual-MiniLM-L12-v2, exécuté avec fastembed (version ONNX, sans PyTorch). Il est multilingue, adapté à un corpus en français, et léger en mémoire, ce qui compte pour un déploiement sur Streamlit Cloud (environ 1 Go de RAM).
- Base vectorielle : Chroma, persistante dans agent/chroma_db. L'index est construit une seule fois puis rechargé ; il doit être reconstruit quand les fichiers markdown changent (python -m agent.rag --rebuild).
- L'outil renvoie 3 passages, chacun avec sa source (fichier et titre), affichée sous la réponse dans l'interface.

## Interface

- Interface web Streamlit : agent/app_web.py (bandeau Amadeus, historique de conversation, affichage des sources documentaires).
- Interface en ligne de commande pour les tests rapides : agent/app.py.
- Déploiement envisagé : Streamlit Cloud (environ 1 Go de RAM). Le fichier requirements.txt contient uniquement les dépendances de l'application ; les dépendances du pipeline de prévision sont dans requirements-pipeline.txt.
- Justification du choix de Streamlit : A COMPLETER.
