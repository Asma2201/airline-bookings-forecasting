"""Index documentaire (RAG) sur les fichiers markdown de agent/knowledge.

L'index Chroma est construit une seule fois dans agent/chroma_db, puis rechargé.
Pour le reconstruire après une modification des .md : python -m agent.rag --rebuild
"""
import hashlib
import json
import shutil
import sys
import warnings
from pathlib import Path

from chromadb.config import Settings
from langchain_chroma import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.embeddings import FastEmbedEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

DOSSIER_AGENT = Path(__file__).parent
DOSSIER_KNOWLEDGE = DOSSIER_AGENT / "knowledge"
DOSSIER_CHROMA = DOSSIER_AGENT / "chroma_db"
DOSSIER_MODELES = DOSSIER_AGENT / "modeles_embeddings"
FICHIER_EMPREINTE = DOSSIER_CHROMA / "empreinte_corpus.json"

NOM_COLLECTION = "documentation_amadeus"
MODELE_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
TITRES = [("#", "h1"), ("##", "h2"), ("###", "h3")]
SECTIONS_EXCLUES = {"Sources citées"}  # listes d'URL, inutiles pour la recherche
TAILLE_MAX_CHUNK = 1000

_vector_store: Chroma | None = None


def charger_documents() -> list[Document]:
    """Charge tous les .md du dossier knowledge."""
    loader = DirectoryLoader(
        str(DOSSIER_KNOWLEDGE), glob="*.md", loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    return sorted(loader.load(), key=lambda d: d.metadata["source"])


def titre_section(metadata: dict) -> str:
    """Titre le plus précis de la section (### sinon ## sinon #)."""
    return metadata.get("h3") or metadata.get("h2") or metadata.get("h1") or ""


def decouper_documents(documents: list[Document]) -> list[Document]:
    """Découpe par titres, puis par paragraphes si une section dépasse TAILLE_MAX_CHUNK.

    MarkdownHeaderTextSplitter sépare les paragraphes par "  \\n" mais garde les lignes
    d'un tableau jointes par "\\n" : en n'utilisant que "  \\n" comme séparateur,
    un tableau n'est jamais coupé en deux.
    """
    decoupeur_titres = MarkdownHeaderTextSplitter(TITRES, strip_headers=False)
    decoupeur_taille = RecursiveCharacterTextSplitter(
        chunk_size=TAILLE_MAX_CHUNK, chunk_overlap=0, separators=["  \n"], keep_separator=False,
    )
    chunks = []
    for document in documents:
        fichier = Path(document.metadata["source"]).name
        for section in decoupeur_titres.split_text(document.page_content):
            if section.metadata.get("h2") in SECTIONS_EXCLUES:
                continue
            titre = titre_section(section.metadata)
            for morceau in decoupeur_taille.split_text(section.page_content):
                # Le fil d'Ariane (fichier > titres) aide la recherche sur les morceaux découpés
                fil = " > ".join([fichier] + [section.metadata[h] for _, h in TITRES if h in section.metadata])
                chunks.append(Document(
                    page_content=f"[{fil}]\n{morceau.strip()}",
                    metadata={"fichier": fichier, "titre": titre,
                              **{h: section.metadata[h] for _, h in TITRES if h in section.metadata}},
                ))
    return chunks


def empreinte_corpus() -> dict[str, str]:
    """Hash SHA-256 de chaque .md, pour détecter un corpus modifié depuis l'indexation."""
    return {
        f.name: hashlib.sha256(f.read_bytes()).hexdigest()
        for f in sorted(DOSSIER_KNOWLEDGE.glob("*.md"))
    }


def charger_embeddings() -> FastEmbedEmbeddings:
    return FastEmbedEmbeddings(model_name=MODELE_EMBEDDINGS, cache_dir=str(DOSSIER_MODELES))


def _ouvrir_chroma() -> Chroma:
    return Chroma(
        collection_name=NOM_COLLECTION,
        embedding_function=charger_embeddings(),
        persist_directory=str(DOSSIER_CHROMA),
        client_settings=Settings(anonymized_telemetry=False, is_persistent=True,
                                 persist_directory=str(DOSSIER_CHROMA)),
    )


def _construire_index() -> Chroma:
    chunks = decouper_documents(charger_documents())
    store = _ouvrir_chroma()
    store.add_documents(chunks)
    FICHIER_EMPREINTE.write_text(json.dumps(empreinte_corpus(), indent=2), encoding="utf-8")
    print(f"Index documentaire construit : {len(chunks)} passages dans {DOSSIER_CHROMA}")
    return store


def charger_vector_store() -> Chroma:
    """Retourne le vector store, chargé une seule fois par processus.

    Si agent/chroma_db existe, l'index est rechargé tel quel (pas de réindexation,
    donc pas de doublons). Sinon il est construit.
    """
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    if FICHIER_EMPREINTE.exists():
        _vector_store = _ouvrir_chroma()
        empreinte_indexee = json.loads(FICHIER_EMPREINTE.read_text(encoding="utf-8"))
        if empreinte_indexee != empreinte_corpus():
            warnings.warn(
                "Les fichiers de agent/knowledge ont changé depuis l'indexation. "
                "Lancez 'python -m agent.rag --rebuild' pour mettre l'index à jour."
            )
    else:
        # Dossier absent ou indexation interrompue : on repart de zéro
        shutil.rmtree(DOSSIER_CHROMA, ignore_errors=True)
        _vector_store = _construire_index()
    return _vector_store


def reconstruire_index() -> Chroma:
    """Supprime agent/chroma_db et réindexe tous les .md (à lancer quand le corpus change)."""
    global _vector_store
    _vector_store = None
    shutil.rmtree(DOSSIER_CHROMA, ignore_errors=True)
    _vector_store = _construire_index()
    return _vector_store


def rechercher(question: str, k: int = 3) -> list[Document]:
    return charger_vector_store().similarity_search(question, k=k)


if __name__ == "__main__":
    if "--rebuild" in sys.argv:
        reconstruire_index()
    else:
        store = charger_vector_store()
        question = " ".join(a for a in sys.argv[1:]) or "Pourquoi SARIMA plutôt que Prophet ?"
        for doc in store.similarity_search(question, k=3):
            print(f"--- {doc.metadata['fichier']} > {doc.metadata['titre']}\n{doc.page_content}\n")
