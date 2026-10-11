import pandas as pd
from config import CHEMIN_DONNEES_BRUTES, CHEMIN_OUTPUTS
from src.data_loading import charger_donnees
from src.cleaning import pipeline_nettoyage
from src.global_series import construire_serie_complete, preparer_train_test
from src.global_forecast import prevision_globale_finale
from src.agence_panel import pipeline_panel
from src.agence_features import preparer_panel_model, split_train_test, ajouter_cibles_horizon
from src.agence_forecast import prevision_proportionnelle, verifier_coherence
from src.export_powerbi import (
    construire_fait_reservations,
    construire_dim_agence,
    construire_fait_canal,
    exporter_tout,
)
from agent.database import construire_base

def run():
    print("1. Chargement...")
    df = charger_donnees(CHEMIN_DONNEES_BRUTES)
    df = pipeline_nettoyage(df)

    print("2. Série globale + prévision de référence...")
    serie_complete = construire_serie_complete(df)
    serie_continue, train, test = preparer_train_test(serie_complete)
    prevision_globale = prevision_globale_finale(serie_continue)

    print("3. Panel par agence...")
    panel = pipeline_panel(df)
    panel_model, _ = preparer_panel_model(panel)

    print("4. Prévision par agence (proportionnelle, méthode validée)...")
    prevision_agence = prevision_proportionnelle(panel, prevision_globale)

    print("5. Vérification de cohérence...")
    print(verifier_coherence(prevision_agence, prevision_globale))

    print("6. Export Power BI...")
    fait = construire_fait_reservations(serie_complete, prevision_globale, prevision_agence, panel)
    dim_agence = construire_dim_agence(panel)
    fait_canal = construire_fait_canal(panel)

    exporter_tout(fait, dim_agence, CHEMIN_OUTPUTS)
    fait_canal.to_csv(f"{CHEMIN_OUTPUTS}/fait_canal.csv", index=False, encoding="utf-8-sig")

    print("7. Base SQLite de l'agent...")
    construire_base(CHEMIN_OUTPUTS)

    print("Terminé.")

if __name__ == "__main__":
    run()