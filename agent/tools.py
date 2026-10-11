"""Outils exposés à l'agent LLM pour interroger les données de forecasting."""
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_core.tools import tool

from agent.rag import charger_vector_store

NOM_OUTIL_DOCUMENTATION = "recherche_documentation"
CONSIGNE_PASSAGES = (
    "Passages de la documentation. Appuie-toi uniquement sur leur contenu. Un statut "
    "(Confirmé, Observé, Déduction, Hypothèse) ne s'applique que s'il est écrit dans le "
    "passage : n'en attribue pas aux chiffres SQL ni aux passages qui n'en indiquent pas. "
    "Confirmé signifie validé par l'encadrant, pas simplement présent dans la documentation."
)


def charger_toolkit_sql(chemin_db: str, llm):
    """Retourne un toolkit LangChain capable d'écrire et exécuter du SQL sur la base."""
    db = SQLDatabase.from_uri(f"sqlite:///{chemin_db}")
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    return toolkit.get_tools()


@tool(NOM_OUTIL_DOCUMENTATION, response_format="content_and_artifact")
def recherche_documentation(question: str) -> tuple[str, list[dict]]:
    """Utilise cet outil pour la méthodologie, les limites du modèle, le vocabulaire métier et l'interprétation métier (vacances, fêtes, crises, événements qui expliquent les pics et les baisses). Pour les volumes précis d'un mois, d'une agence ou d'une compagnie, utilise le SQL tool. Pour une question qui demande à la fois un chiffre et une explication, appelle les deux outils."""
    passages = charger_vector_store().similarity_search(question, k=3)
    if not passages:
        return "Aucun passage trouvé dans la documentation.", []

    # Le LLM reçoit le texte ; la liste des sources (artifact) sert à l'affichage Streamlit
    texte = CONSIGNE_PASSAGES + "\n\n" + "\n\n".join(
        f"Source : {p.metadata['fichier']} > {p.metadata['titre']}\n{p.page_content}" for p in passages
    )
    sources = [
        {"fichier": p.metadata["fichier"], "titre": p.metadata["titre"], "texte": p.page_content}
        for p in passages
    ]
    return texte, sources
