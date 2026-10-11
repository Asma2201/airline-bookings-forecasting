"""Agent en ligne de commande (python -m agent.app), avec mémoire de la conversation."""
from agent.graph import construire_agent, poser_question_detaillee


def main():
    agent = construire_agent()
    historique = []
    print("Agent prêt. Tape 'exit' pour quitter, 'reset' pour une nouvelle conversation.\n")

    while True:
        question = input("Question : ").strip()
        if not question:
            continue
        if question.lower() == "exit":
            break
        if question.lower() == "reset":
            historique = []
            print("Nouvelle conversation.\n")
            continue
        try:
            resultat = poser_question_detaillee(agent, question, historique)
        except Exception as erreur:  # limite de débit Groq, réseau...
            print(f"\nErreur : {str(erreur)[:300]}\n")
            continue
        print(f"\nRéponse : {resultat['reponse']}")
        for source in resultat["sources"]:
            print(f"  - Source : {source['fichier']} > {source['titre']}")
        print()
        historique += [{"role": "user", "content": question},
                       {"role": "assistant", "content": resultat["reponse"]}]


if __name__ == "__main__":
    main()
