"""Blocs 2-4 — Typage, correction de l'anomalie de collecte, valeurs manquantes."""
import pandas as pd
import numpy as np

MEASURE_COLS = [
    "Air Net Bookings", "Air ATLA Confirmed Bookings",
    "Air Net Bookings EAC", "Air Net Bookings NDC",
    "Car Net Bookings", "Hotel Net Bkgs",
    "Insurance Net Bookings", "Rail Net Bookings", "Cruise Bookings",
]
CAT_COLS = [
    "[Master Account Number]", "[Master Account Name]",
    "[Office ID]", "[Provider Name]", "[Provider Code]",
]


def corriger_types(df: pd.DataFrame) -> pd.DataFrame:
    """Bloc 3 — reconstruit la colonne date et type les colonnes."""
    df = df.copy()
    df["date"] = pd.to_datetime(
        df["KEY_F_MD_DATE.Calendar.Year"].astype(str) + "-" +
        df["KEY_F_MD_DATE.Calendar.Month"].astype(str),
        format="%Y-%b", errors="coerce",
    )
    for col in CAT_COLS:
        if col in df.columns:
            df[col] = df[col].astype("category")

    measure_cols = [c for c in MEASURE_COLS if c in df.columns]
    df[measure_cols] = df[measure_cols].apply(pd.to_numeric, errors="coerce")
    return df


def nettoyer_valeurs_manquantes(df: pd.DataFrame) -> pd.DataFrame:
    """Bloc 4 — NaN des mesures -> 0, lignes sans date/agence -> exclues."""
    df = df.copy()
    measure_cols = [c for c in MEASURE_COLS if c in df.columns]
    df[measure_cols] = df[measure_cols].fillna(0)
    return df.dropna(subset=["date", "[Master Account Number]"])


def detecter_mois_anomalie(df: pd.DataFrame, seuil: int = 50) -> pd.Index:
    """Mois avec un nombre de lignes anormalement bas (collecte incomplète)."""
    lignes_par_mois = df.groupby("date").size()
    return lignes_par_mois[lignes_par_mois < seuil].index


def pipeline_nettoyage(df: pd.DataFrame) -> pd.DataFrame:
    """Enchaîne les 3 étapes de nettoyage."""
    df = corriger_types(df)
    df = nettoyer_valeurs_manquantes(df)
    return df