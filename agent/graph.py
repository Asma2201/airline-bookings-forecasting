"""Construction de l'agent LangGraph — reçoit une question, interroge la base, répond."""
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_groq import ChatGroq
from agent.database import CHEMIN_DB
from agent.rag import charger_vector_store
from agent.tools import NOM_OUTIL_DOCUMENTATION, charger_toolkit_sql, recherche_documentation

RACINE_PROJET = Path(__file__).parent.parent
load_dotenv(RACINE_PROJET / ".env")

SYSTEM_PROMPT = """Tu es un assistant qui répond à des questions sur les prévisions de \
réservations aériennes d'agences de voyage (données Amadeus). Ne donne jamais un chiffre \
sur les données (volume, nombre d'agences, prévision, intervalle) que tu n'as pas obtenu \
en interrogeant la base avec les outils SQL, même si la documentation le mentionne.

RÈGLE IMPORTANTE : la table fait_reservations contient une ligne "TOTAL_GLOBAL" dans la \
colonne agence, qui représente déjà le total agrégé de toutes les agences. Pour donner \
un volume GLOBAL (toutes agences confondues), filtre TOUJOURS sur agence = 'TOTAL_GLOBAL' \
et ne fais JAMAIS un SUM sans ce filtre, sinon tu comptes chaque réservation deux fois.

La table contient à la fois des données historiques réelles (type_donnee = 'Réel', \
disponibles pour toutes les agences ET pour TOTAL_GLOBAL, sur les années 2019, 2024, \
2025 et jusqu'à juillet 2026) et des prévisions (type_donnee = 'Prévision', pour août à \
décembre 2026). Tu peux donc classer les agences par volume RÉEL historique tout comme \
par volume PRÉVU.

Si la question ne peut pas être répondue avec les données disponibles, dis-le clairement \
plutôt que d'inventer une réponse. Réponds en français, de façon claire et concise.

Tu disposes de deux outils. Le SQL tool donne les chiffres (volumes, agences, prévisions). \
L'outil de documentation donne la méthodologie, les limites, le vocabulaire et \
l'interprétation métier. Pour une question qui demande un chiffre et une explication, appelle \
les deux. Quand tu donnes une explication, précise son statut tel qu'indiqué dans la \
documentation (Confirmé, Observé, Déduction, Hypothèse). Si la documentation ne contient pas \
l'explication, dis-le clairement et n'invente pas de cause. Si tu proposes toi-même une \
explication, présente-la explicitement comme une hypothèse de ta part. Le statut Confirmé \
signifie uniquement validé par l'encadrant ; ne l'utilise que si la documentation l'indique \
explicitement. Un chiffre tiré de la base ou de la documentation n'a pas besoin de statut : \
cite simplement sa source. N'ajoute aucune cause ou justification absente de la \
documentation, sauf en écrivant explicitement 'Hypothèse de ma part :'. Quand la \
documentation liste des causes possibles, cite-les avec leur statut.

Les messages précédents de la conversation servent à comprendre les relances (par \
exemple "et pour octobre ?") ; réinterroge la base pour tout nouveau chiffre. Cite tes \
sources en clair (table SQL, fichier de documentation), sans marqueurs du type 【outil】."""

NB_MESSAGES_HISTORIQUE = 6  # 3 derniers échanges : suffit pour les relances, ménage la limite Groq


def construire_agent(chemin_db: str | Path = CHEMIN_DB):
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY absente : ajoutez-la dans le fichier .env à la racine du projet.")
    if not Path(chemin_db).exists():
        raise FileNotFoundError(
            f"Base {chemin_db} introuvable : lancez 'python main.py' (ou 'python -m agent.database')."
        )
    llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
    charger_vector_store()  # chargé une seule fois (mis en cache), jamais réindexé ici
    tools = charger_toolkit_sql(chemin_db, llm) + [recherche_documentation]
    agent = create_agent(llm, tools, system_prompt=SYSTEM_PROMPT)
    return agent


def _messages_entree(question: str, historique: list[dict] | None) -> list[dict]:
    """Derniers échanges (question / réponse finale, sans les sorties d'outils) + la question."""
    precedents = [
        {"role": m["role"], "content": m["content"]}
        for m in (historique or []) if m["role"] in ("user", "assistant")
    ][-NB_MESSAGES_HISTORIQUE:]
    return precedents + [{"role": "user", "content": question}]


def poser_question(agent, question: str, historique: list[dict] | None = None) -> str:
    return poser_question_detaillee(agent, question, historique)["reponse"]


def poser_question_detaillee(agent, question: str, historique: list[dict] | None = None) -> dict:
    """Comme poser_question, mais renvoie aussi les outils appelés et les sources documentaires.

    historique : messages précédents {"role": "user"|"assistant", "content": ...}, pour
    permettre les relances ("et pour octobre ?").
    """
    resultat = agent.invoke({"messages": _messages_entree(question, historique)})
    # Seuls les messages produits pour la question courante (après le dernier message utilisateur)
    dernier_humain = max(i for i, m in enumerate(resultat["messages"]) if isinstance(m, HumanMessage))
    outils, sources = [], []
    for message in resultat["messages"][dernier_humain + 1:]:
        if isinstance(message, AIMessage):
            outils += [appel["name"] for appel in message.tool_calls]
        elif isinstance(message, ToolMessage) and message.name == NOM_OUTIL_DOCUMENTATION:
            for source in message.artifact or []:
                if source not in sources:
                    sources.append(source)
    return {
        "reponse": resultat["messages"][-1].content,
        "outils": outils,
        "sources": sources,
        "messages": resultat["messages"],
    }
