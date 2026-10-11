"""Tests de l'agent (SQL + RAG).

Lancement depuis la racine du projet :
    python tests/test_agent.py                         # contrôles hors ligne + toutes les questions
    python tests/test_agent.py --hors-ligne            # uniquement les contrôles sans appel au LLM
    python tests/test_agent.py --question 14           # une seule question (n° 1 à 15)
    python tests/test_agent.py --question 3 --question 7 --pause 60

--pause fixe le nombre de secondes entre deux questions (20 par défaut), pour rester
sous la limite de débit de Groq en offre gratuite (8 000 tokens par minute,
200 000 tokens par jour : une série complète en consomme environ 60 000).

Les questions appellent Groq : les réponses ne sont pas strictement déterministes.
Les contrôles OK / KO sont des heuristiques, à relire avec les réponses affichées.
"""
import argparse
import re
import sqlite3
import sys
import time
from pathlib import Path

RACINE = Path(__file__).parent.parent
sys.path.insert(0, str(RACINE))

from agent.graph import CHEMIN_DB, construire_agent, poser_question_detaillee  # noqa: E402
from agent.rag import charger_documents, charger_vector_store, decouper_documents  # noqa: E402
from agent.tools import NOM_OUTIL_DOCUMENTATION  # noqa: E402

SQL, DOC, MIXTE, NON_DOCUMENTE, DONNEE_ABSENTE = "sql", "doc", "mixte", "non_documente", "donnee_absente"

# Motifs indiquant que l'agent reconnaît ne pas avoir l'information
MOTIF_ABSENCE = re.compile(
    r"pas (de données|d'information|documenté|disponible|dans la (base|documentation))|"
    r"ne (contient|dispose|mentionne|figure|comporte|peux) pas|"
    r"aucune (donnée|information|mention|colonne|table)|aucun (champ|chiffre|élément)|"
    r"(n'est|il est) pas possible|impossible d|"
    r"n'est pas (documenté|mentionné|disponible|couvert)|n'(y )?a pas de données",
    re.IGNORECASE,
)
MOTIF_SEPTEMBRE = re.compile(r"59[\s  .,]?20[0-9]")

QUESTIONS = [
    # --- Questions chiffrées : SQL tool ---
    (SQL, "Quel est le volume global prévu pour septembre 2026 ?", MOTIF_SEPTEMBRE),
    (SQL, "Quelle est l'agence qui a le plus gros volume réel de réservations sur tout l'historique ?", None),
    (SQL, "Combien d'agences sont dans le segment Top 20 ?", re.compile(r"\b28\b")),
    (SQL, "Quel est le volume total réel de réservations en 2025, toutes agences confondues ?",
     re.compile(r"838[\s  .,]?458")),
    (SQL, "Quelle est la prévision de décembre 2026 pour le total global, avec son intervalle de confiance ?",
     re.compile(r"72[\s  .,]?57[0-9]")),
    # --- Donnée absente de la base : l'agent doit le dire sans inventer ---
    (DONNEE_ABSENTE, "Quelle est la compagnie la plus réservée ?", MOTIF_ABSENCE),
    # --- Questions documentaires : RAG tool ---
    (DOC, "Pourquoi avoir choisi SARIMA plutôt que Prophet ?", None),
    (DOC, "Quelles sont les limites du modèle ?", None),
    (DOC, "Pourquoi le LightGBM par agence a-t-il été abandonné ?", None),
    (DOC, "Quel est l'effet attendu de la crise Tunisair en 2025 ?", re.compile(r"hypoth", re.IGNORECASE)),
    (DOC, "Pourquoi les fêtes musulmanes ne tombent-elles pas au même mois chaque année ?", None),
    # --- Questions mixtes : SQL + RAG ---
    (MIXTE, "Quel est le volume de mars 2026 et quels événements peuvent l'expliquer ?", None),
    (MIXTE, "Pourquoi 2025 est-il plus bas que 2019, et de combien ?", None),
    (MIXTE, "Quelle est la prévision de novembre 2026 et est-elle fiable ?", None),
    # --- Information non documentée : ne pas inventer ---
    (NON_DOCUMENTE, "Quel est l'effet de la Coupe du monde 2026 sur les réservations ?", MOTIF_ABSENCE),
]


def outils_sql(outils: list[str]) -> bool:
    return any(nom.startswith("sql_db") for nom in outils)


def outil_doc(outils: list[str]) -> bool:
    return NOM_OUTIL_DOCUMENTATION in outils


def verifier_outils(categorie: str, outils: list[str]) -> bool:
    if categorie == SQL:
        return outils_sql(outils)
    if categorie == DOC:
        return outil_doc(outils)
    if categorie == MIXTE:
        return outils_sql(outils) and outil_doc(outils)
    if categorie == NON_DOCUMENTE:
        return outil_doc(outils)
    return True  # DONNEE_ABSENTE : seul le contenu de la réponse compte


# ---------------------------------------------------------------------------
# Contrôles hors ligne (sans LLM)
# ---------------------------------------------------------------------------

def controles_hors_ligne() -> bool:
    print("=" * 80 + "\nCONTRÔLES HORS LIGNE\n" + "=" * 80)
    resultats = []

    conn = sqlite3.connect(CHEMIN_DB)
    volume = conn.execute(
        "SELECT volume FROM fait_reservations WHERE agence = 'TOTAL_GLOBAL' "
        "AND type_donnee = 'Prévision' AND date = '2026-09-01'"
    ).fetchone()[0]
    conn.close()
    resultats.append(("Prévision SQL septembre 2026 ~ 59 200", abs(volume - 59_200) < 100, f"{volume:,.1f}"))

    chunks = decouper_documents(charger_documents())
    nb_index = charger_vector_store()._collection.count()
    resultats.append(("Index rechargé sans doublon", nb_index == len(chunks), f"{nb_index} / {len(chunks)}"))
    resultats.append((
        "Section 'Sources citées' non indexée",
        not any(c.metadata.get("h2") == "Sources citées" for c in chunks), "",
    ))
    tableaux_coupes = [
        c for c in chunks
        if c.page_content.split("\n")[1:2] and c.page_content.split("\n")[1].startswith("|")
        and "|---" not in c.page_content
    ]
    resultats.append(("Aucun tableau coupé", not tableaux_coupes, f"{len(tableaux_coupes)} morceau(x) orphelin(s)"))

    for nom, ok, detail in resultats:
        print(f"[{'OK' if ok else 'KO'}] {nom} {detail}")
    return all(ok for _, ok, _ in resultats)


# ---------------------------------------------------------------------------
# Questions à l'agent
# ---------------------------------------------------------------------------

def interroger(agent, question: str, essais: int = 3) -> dict:
    """Pose la question, avec nouvel essai en cas de limite de débit Groq."""
    for essai in range(essais):
        try:
            return poser_question_detaillee(agent, question)
        except Exception as erreur:  # limite de débit, erreur réseau...
            if essai == essais - 1:
                raise
            print(f"   (erreur : {str(erreur)[:120]} - nouvel essai dans 30 s)")
            time.sleep(30)


def tester_questions(numeros: set[int] | None = None, pause: float = 20) -> bool:
    agent = construire_agent()
    bilan = []
    for numero, (categorie, question, motif) in enumerate(QUESTIONS, start=1):
        if numeros and numero not in numeros:
            continue
        if bilan:
            time.sleep(pause)  # ménage la limite de débit de Groq
        print("\n" + "=" * 80 + f"\nQ{numero} [{categorie}] {question}\n" + "=" * 80)
        try:
            resultat = interroger(agent, question)
        except Exception as erreur:
            print(f"[KO] erreur de l'agent : {str(erreur)[:300]}")
            bilan.append((numero, categorie, False))
            continue
        outils = resultat["outils"]

        print("Outils appelés :", ", ".join(outils) or "aucun")
        for source in resultat["sources"]:
            extrait = source["texte"].split("\n", 1)[-1][:200].replace("\n", " ")
            print(f"  - Passage : {source['fichier']} > {source['titre']}\n      {extrait}...")
        print(f"\nRéponse :\n{resultat['reponse']}\n")

        ok_outils = verifier_outils(categorie, outils)
        ok_contenu = motif.search(resultat["reponse"]) is not None if motif else True
        print(f"[{'OK' if ok_outils else 'KO'}] outils attendus ({categorie})")
        if motif:
            print(f"[{'OK' if ok_contenu else 'KO'}] contenu attendu ({motif.pattern[:60]})")
        bilan.append((numero, categorie, ok_outils and ok_contenu))

    print("\n" + "=" * 80 + "\nBILAN\n" + "=" * 80)
    for numero, categorie, ok in bilan:
        print(f"Q{numero:<3} {categorie:<15} {'OK' if ok else 'KO'}")
    return all(ok for _, _, ok in bilan)


def lire_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tests de l'agent Amadeus (SQL + RAG).")
    parser.add_argument("--question", type=int, action="append", choices=range(1, len(QUESTIONS) + 1),
                        metavar="N", help="numéro de la question à lancer (option répétable)")
    parser.add_argument("--pause", type=float, default=20, help="secondes entre deux questions")
    parser.add_argument("--hors-ligne", action="store_true", help="contrôles sans appel au LLM")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = lire_arguments()
    succes = controles_hors_ligne()
    if not arguments.hors_ligne:
        numeros = set(arguments.question) if arguments.question else None
        succes = tester_questions(numeros, arguments.pause) and succes
    sys.exit(0 if succes else 1)
