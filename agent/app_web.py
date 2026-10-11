"""Interface web Streamlit — Amadeus Forecasting Assistant."""
import base64
import html
import sys
from pathlib import Path
from urllib.parse import quote

import streamlit as st

# "streamlit run agent/app_web.py" ne met que agent/ dans le chemin : on ajoute la racine
RACINE_PROJET = Path(__file__).parent.parent
if str(RACINE_PROJET) not in sys.path:
    sys.path.insert(0, str(RACINE_PROJET))

from agent.graph import construire_agent, poser_question_detaillee  # noqa: E402

DOSSIER_ASSETS = Path(__file__).parent / "assets"
LOGO = DOSSIER_ASSETS / "amadeus_logo.png"
FOND = DOSSIER_ASSETS / "background.jpg"
MESSAGE_ACCUEIL = "Bonjour, comment puis-je vous aider concernant les données de forecasting ?"

st.set_page_config(
    page_title="Amadeus Forecasting Assistant",
    page_icon=str(LOGO) if LOGO.exists() else None,
    layout="centered",
)


def encoder_image_securise(chemin: Path) -> str | None:
    """Encode une image en base64, ou retourne None si le fichier n'existe pas."""
    if not chemin.exists():
        return None
    return base64.b64encode(chemin.read_bytes()).decode()


def motif_routes(anime: bool = False) -> str:
    animation = (
        "<style>path{animation:defile 14s linear infinite}"
        "@keyframes defile{to{stroke-dashoffset:-160}}"
        "@media(prefers-reduced-motion:reduce){path{animation:none}}</style>"
        if anime else ""
    )
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800" '
        'preserveAspectRatio="xMidYMid slice">' + animation +
        '<g fill="none" stroke="#fff" stroke-opacity=".28" stroke-width="2" stroke-dasharray="6 10">'
        '<path d="M-50 620 Q300 180 700 380 T1250 120"/>'
        '<path d="M-50 760 Q400 420 800 620 T1250 380"/>'
        '<path d="M100 -20 Q420 300 860 200 T1250 520"/>'
        '</g>'
        '<g fill="#fff" fill-opacity=".45">'
        '<circle cx="700" cy="380" r="6"/><circle cx="800" cy="620" r="6"/>'
        '<circle cx="860" cy="200" r="6"/><circle cx="1250" cy="120" r="6"/>'
        '</g></svg>'
    )
    return f'url("data:image/svg+xml;utf8,{quote(svg)}")'


def fond_page() -> str:
    """Fond avec l'image background.jpg si présente, sinon un dégradé + motif animé."""
    degrade = "linear-gradient(160deg, #061B3D 0%, #0A4CA8 55%, #2E8BEA 100%)"
    fond_b64 = encoder_image_securise(FOND)
    if fond_b64:
        voile = "linear-gradient(160deg, rgba(6,27,61,.80), rgba(0,94,184,.60))"
        return f'{voile}, url("data:image/jpeg;base64,{fond_b64}")'
    return f"{motif_routes()}, {degrade}"


STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
    --bleu-nuit: #061B3D;
    --bleu-marine: #0A3D91;
    --bleu-amadeus: #005EB8;
    --bleu-vif: #1E7BE0;
    --bleu-ciel: #CFE6FF;
    --bleu-pale: #EAF3FF;
}
html { font-size: 17px; }

.stApp, .stMarkdown, p, li, textarea, label {
    font-family: 'Plus Jakarta Sans', 'Source Sans Pro', sans-serif;
}
.stApp {
    background: __FOND__;
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}
header[data-testid="stHeader"], [data-testid="stBottom"],
[data-testid="stBottom"] > div { background: transparent !important; }
footer { visibility: hidden; }

.block-container {
    max-width: 1000px;
    margin-top: 1.5rem;
    padding: 1.6rem 2rem 7rem 2rem !important;
    background: rgba(255, 255, 255, .95);
    border-radius: 24px;
    box-shadow: 0 24px 60px rgba(3, 20, 50, .40);
}

.hero {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 24px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.6rem;
    border-radius: 18px;
    background: __ROUTES_ANIMEES__, linear-gradient(120deg, #1E7BE0 0%, #005EB8 45%, #061B3D 100%);
    background-size: cover;
    box-shadow: 0 10px 28px rgba(0, 94, 184, .35);
}
.hero-logo {
    background: #fff;
    border-radius: 14px;
    padding: 12px 18px;
    line-height: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 130px;
}
.hero-logo img { width: 130px; }
.hero-logo span {
    font-weight: 800;
    color: #005EB8;
    font-size: 1.4rem;
    letter-spacing: -0.02em;
}
.hero-title {
    margin: 0;
    color: #fff;
    font-size: 2.3rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1.15;
}
.hero-subtitle {
    margin: .4rem 0 0 0;
    color: var(--bleu-ciel);
    font-size: 1.2rem;
    font-weight: 500;
}

[data-testid="stChatMessage"] {
    background: #fff;
    border: 1px solid #D6E6FA;
    border-left: 5px solid var(--bleu-vif);
    border-radius: 16px;
    padding: 14px 18px;
    margin-bottom: 14px;
    box-shadow: 0 4px 14px rgba(10, 61, 145, .10);
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    background: linear-gradient(135deg, #1E7BE0, #0A3D91);
    border: none;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) p,
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) li {
    color: #fff;
}
[data-testid="stChatMessageContent"] p,
[data-testid="stChatMessageContent"] li {
    font-size: 1.15rem;
    line-height: 1.65;
}
div[data-testid="stChatMessageAvatarUser"] {
    background-color: #fff !important;
    color: var(--bleu-amadeus) !important;
}
div[data-testid="stChatMessageAvatarAssistant"] {
    background-color: var(--bleu-marine) !important;
}
div[data-testid="stChatMessageAvatarUser"],
div[data-testid="stChatMessageAvatarAssistant"] {
    width: 2.6rem;
    height: 2.6rem;
}

[data-testid="stChatInput"] {
    background: #fff;
    border: 2px solid var(--bleu-vif);
    border-radius: 18px;
    box-shadow: 0 8px 24px rgba(3, 20, 50, .30);
}
[data-testid="stChatInput"] textarea { font-size: 1.1rem; }
[data-testid="stChatInputSubmitButton"] {
    background: var(--bleu-amadeus);
    color: #fff;
    border-radius: 12px;
}
[data-testid="stSpinner"] { font-size: 1.05rem; color: var(--bleu-amadeus); }

.sources {
    margin-top: .8rem;
    padding-top: .6rem;
    border-top: 1px solid #D6E6FA;
    font-size: .9rem;
    color: #3B5B85;
}
.sources p { margin: 0 0 .2rem 0; font-weight: 600; font-size: .9rem; }
.sources ul { margin: 0; padding-left: 1.2rem; }
.sources li { font-size: .9rem; line-height: 1.5; }
</style>
"""


def injecter_style() -> None:
    style = STYLE.replace("__FOND__", fond_page())
    style = style.replace("__ROUTES_ANIMEES__", motif_routes(anime=True))
    st.markdown(style, unsafe_allow_html=True)


def afficher_entete() -> None:
    """Affiche le bandeau avec le logo si disponible, sinon un texte 'AMADEUS' stylisé."""
    logo_b64 = encoder_image_securise(LOGO)
    bloc_logo = (
        f'<div class="hero-logo"><img src="data:image/png;base64,{logo_b64}" alt="Amadeus"></div>'
        if logo_b64 else
        '<div class="hero-logo"><span>AMADEUS</span></div>'
    )
    st.markdown(
        '<div class="hero">'
        f'{bloc_logo}'
        '<div>'
        '<p class="hero-title">Amadeus Forecasting Assistant</p>'
        '<p class="hero-subtitle">Interrogez les prévisions de réservations en langage naturel</p>'
        '</div></div>',
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner="Initialisation de l'assistant...")
def agent_partage():
    """Un seul agent par serveur : l'agent est sans état, l'historique reste dans la session."""
    return construire_agent()


def initialiser_session() -> bool:
    """Prépare l'agent et l'historique ; retourne False (avec un message) si l'agent est indisponible."""
    try:
        st.session_state.agent = agent_partage()
    except (RuntimeError, FileNotFoundError) as erreur:
        st.error(str(erreur))
        return False
    st.session_state.setdefault(
        "historique", [{"role": "assistant", "content": MESSAGE_ACCUEIL}]
    )
    return True


def message_erreur(erreur: Exception) -> str:
    texte = str(erreur)
    if "rate_limit" in texte or "429" in texte:
        return "La limite de requêtes Groq est atteinte. Patientez une minute puis reposez la question."
    if "401" in texte or "invalid_api_key" in texte.lower():
        return "Clé GROQ_API_KEY invalide : vérifiez le fichier .env."
    return f"Une erreur est survenue pendant l'analyse : {texte[:300]}"


def afficher_sources(sources: list[dict]) -> None:
    """Liste les passages de documentation utilisés (fichier + titre), sans doublon."""
    references = list(dict.fromkeys(f"{s['fichier']} > {s['titre']}" for s in sources))
    if not references:
        return
    items = "".join(f"<li>{html.escape(ref)}</li>" for ref in references)
    st.markdown(
        f'<div class="sources"><p>Sources documentaires</p><ul>{items}</ul></div>',
        unsafe_allow_html=True,
    )


def afficher_message(role: str, contenu: str, sources: list[dict] | None = None) -> None:
    with st.chat_message(role):
        st.write(contenu)
        if sources:
            afficher_sources(sources)


def afficher_historique() -> None:
    for message in st.session_state.historique:
        afficher_message(message["role"], message["content"], message.get("sources"))


def traiter_question(question: str) -> None:
    historique = st.session_state.historique[1:]  # sans le message d'accueil
    afficher_message("user", question)

    with st.chat_message("assistant"):
        with st.spinner("Analyse en cours..."):
            try:
                resultat = poser_question_detaillee(st.session_state.agent, question, historique)
            except Exception as erreur:  # limite de débit, réseau, SQL invalide...
                st.error(message_erreur(erreur))
                return  # la question n'est pas ajoutée à l'historique : on peut la reposer
        st.write(resultat["reponse"])
        afficher_sources(resultat["sources"])

    st.session_state.historique.append({"role": "user", "content": question})
    st.session_state.historique.append(
        {"role": "assistant", "content": resultat["reponse"], "sources": resultat["sources"]}
    )


def afficher_barre_laterale() -> None:
    with st.sidebar:
        st.markdown("**Amadeus Forecasting Assistant**")
        st.caption("Chiffres : base SQLite des prévisions. Explications : documentation projet (RAG).")
        if st.button("Nouvelle conversation", use_container_width=True):
            st.session_state.historique = [{"role": "assistant", "content": MESSAGE_ACCUEIL}]
            st.rerun()


def main() -> None:
    injecter_style()
    afficher_entete()
    if not initialiser_session():
        return
    afficher_barre_laterale()
    afficher_historique()

    question = st.chat_input("Posez votre question sur les prévisions...")
    if question:
        traiter_question(question)


main()