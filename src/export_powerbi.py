"""Construction des tables finales pour Power BI (modèle en étoile)."""
import pandas as pd
import numpy as np


def construire_fait_reservations(serie_complete: pd.Series, prevision_globale: pd.DataFrame,
                                  prevision_par_agence: pd.DataFrame, panel: pd.DataFrame) -> pd.DataFrame:
    # --- Historique global (TOTAL_GLOBAL) ---
    reel = serie_complete.reset_index()
    reel.columns = ["date", "volume"]
    reel["agence"] = "TOTAL_GLOBAL"
    reel["type_donnee"] = "Réel"
    reel["borne_basse"] = np.nan
    reel["borne_haute"] = np.nan
    reel["methode"] = "Historique"

    # --- Historique réel PAR AGENCE, à partir du panel ---
    reel_par_agence = panel[["agence", "date", "air_bookings"]].copy()
    reel_par_agence = reel_par_agence.rename(columns={"air_bookings": "volume"})
    reel_par_agence["type_donnee"] = "Réel"
    reel_par_agence["borne_basse"] = np.nan
    reel_par_agence["borne_haute"] = np.nan
    reel_par_agence["methode"] = "Historique"

    # --- Prévision globale ---
    glob = prevision_globale.reset_index()
    glob.columns = ["date", "volume", "borne_basse", "borne_haute"]
    glob["agence"] = "TOTAL_GLOBAL"
    glob["type_donnee"] = "Prévision"
    glob["methode"] = "SARIMA global"

    # --- Prévision par agence ---
    agence = prevision_par_agence.rename(columns={"prevision": "volume"}).copy()
    agence["type_donnee"] = "Prévision"
    agence["borne_basse"] = np.nan
    agence["borne_haute"] = np.nan
    if "methode" not in agence.columns:
        agence["methode"] = "Multi-horizon LightGBM"

    cols = ["date", "agence", "volume", "type_donnee", "borne_basse", "borne_haute", "methode"]
    return pd.concat([
        reel[cols],
        reel_par_agence[cols],
        glob[cols],
        agence[cols],
    ], ignore_index=True)


def construire_dim_agence(panel: pd.DataFrame) -> pd.DataFrame:
    dim = panel.groupby("agence").agg(
        volume_total_historique=("air_bookings", "sum"),
        nb_mois_historique=("date", "nunique"),
    ).reset_index()
    dim["poids_historique"] = dim["volume_total_historique"] / dim["volume_total_historique"].sum()
    dim["segment"] = pd.qcut(dim["volume_total_historique"], q=[0, 0.7, 0.95, 1.0],
                              labels=["Petite", "Moyenne", "Top 20"])
    return dim

def construire_fait_canal(panel: pd.DataFrame) -> pd.DataFrame:
    """Table de faits secondaire : volume par agence, mois et canal (NDC vs Classique)."""
    panel = panel.copy()

    # Clip des valeurs négatives (Net Bookings peut être négatif, sans sens business ici)
    panel["air_bookings"] = panel["air_bookings"].clip(lower=0)
    panel["ndc_bookings"] = panel["ndc_bookings"].clip(lower=0)

    # Vraie séparation : "Classique" = total moins NDC, pour éviter le double comptage
    panel["classique_only"] = (panel["air_bookings"] - panel["ndc_bookings"]).clip(lower=0)

    df_canal = panel.melt(
        id_vars=["agence", "date"],
        value_vars=["classique_only", "ndc_bookings"],
        var_name="canal", value_name="volume"
    )
    df_canal["canal"] = df_canal["canal"].map({
        "classique_only": "Classique", "ndc_bookings": "NDC"
    })
    return df_canal

def exporter_tout(fait: pd.DataFrame, dim_agence: pd.DataFrame, dossier_sortie: str):
    fait.to_csv(f"{dossier_sortie}/fait_reservations.csv", index=False, encoding="utf-8-sig")
    dim_agence.to_csv(f"{dossier_sortie}/dim_agence.csv", index=False, encoding="utf-8-sig")