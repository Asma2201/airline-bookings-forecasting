"""Blocs 25-28 — Construction du panel agence x mois + variables exogènes."""
import pandas as pd
import numpy as np

PERIODES_RAMADAN = [
    ("2024-03-01", "2024-04-30"),
    ("2025-03-01", "2025-03-31"),
    ("2026-02-01", "2026-03-31"),
]


def construire_panel(df: pd.DataFrame, historique_min: int = 24) -> pd.DataFrame:
    """Bloc 25 — panel agence x mois, agences avec historique suffisant, agence '-' exclue."""
    panel = df.groupby(["[Master Account Name]", "date"]).agg({
        "Air Net Bookings": "sum", "Air ATLA Confirmed Bookings": "sum",
        "Air Net Bookings NDC": "sum", "Car Net Bookings": "sum",
        "Hotel Net Bkgs": "sum", "Insurance Net Bookings": "sum",
        "Rail Net Bookings": "sum", "Cruise Bookings": "sum",
    }).reset_index()

    panel.columns = ["agence", "date", "air_bookings", "atla_bookings", "ndc_bookings",
                      "car_bookings", "hotel_bookings", "insurance_bookings",
                      "rail_bookings", "cruise_bookings"]

    # Retrait de l'agence non identifiée "-" (Problème 3 diagnostiqué)
    panel = panel[panel["agence"] != "-"]

    historique = panel.groupby("agence")["date"].nunique()
    agences_valides = historique[historique >= historique_min].index
    return panel[panel["agence"].isin(agences_valides)].reset_index(drop=True)


def ajouter_features_calendaires(panel: pd.DataFrame) -> pd.DataFrame:
    """Bloc 26 — mois cyclique, trimestre, saison haute."""
    panel = panel.copy()
    panel["annee"] = panel["date"].dt.year
    panel["mois"] = panel["date"].dt.month
    panel["trimestre"] = panel["date"].dt.quarter
    panel["mois_sin"] = np.sin(2 * np.pi * panel["mois"] / 12)
    panel["mois_cos"] = np.cos(2 * np.pi * panel["mois"] / 12)
    panel["saison_haute"] = panel["mois"].isin([6, 7, 8, 12]).astype(int)
    return panel


def ajouter_lags_et_tendance(panel: pd.DataFrame) -> pd.DataFrame:
    """Bloc 27 — lags 1/2/3/12, moyenne mobile, poids de l'agence."""
    panel = panel.sort_values(["agence", "date"]).copy()
    for lag in [1, 2, 3, 12]:
        panel[f"air_bookings_lag{lag}"] = panel.groupby("agence")["air_bookings"].shift(lag)

    panel["air_bookings_ma3"] = panel.groupby("agence")["air_bookings"].transform(
        lambda x: x.rolling(3, min_periods=1).mean()
    )
    poids = panel.groupby("agence")["air_bookings"].sum()
    panel["poids_agence"] = panel["agence"].map(poids)
    return panel


def ajouter_variables_exogenes(panel: pd.DataFrame, df: pd.DataFrame) -> pd.DataFrame:
    """Bloc 28 — part NDC, mois depuis reprise, Ramadan, nb agences actives."""
    panel = panel.merge(
        df.groupby(["[Master Account Name]", "date"])["Air Net Bookings NDC"].sum().reset_index()
          .rename(columns={"[Master Account Name]": "agence", "Air Net Bookings NDC": "ndc_raw"}),
        on=["agence", "date"], how="left"
    )
    panel["part_ndc"] = panel["ndc_raw"] / (panel["air_bookings"] + 1e-6)
    panel = panel.drop(columns=["ndc_raw"])

    panel["mois_depuis_reprise"] = (panel["date"].dt.year - 2024) * 12 + panel["date"].dt.month - 1

    panel["ramadan"] = 0
    for debut, fin in PERIODES_RAMADAN:
        masque = (panel["date"] >= debut) & (panel["date"] <= fin)
        panel.loc[masque, "ramadan"] = 1

    agences_actives = df.groupby("date")["[Master Account Name]"].nunique().rename("nb_agences_actives")
    panel = panel.merge(agences_actives, on="date", how="left")
    return panel


def pipeline_panel(df: pd.DataFrame) -> pd.DataFrame:
    """Enchaîne la construction complète du panel avec toutes ses features."""
    panel = construire_panel(df)
    panel = ajouter_features_calendaires(panel)
    panel = ajouter_lags_et_tendance(panel)
    panel = ajouter_variables_exogenes(panel, df)
    return panel