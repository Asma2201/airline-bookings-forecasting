"""Bloc 1 — Chargement du fichier source."""
import pandas as pd

def charger_donnees(chemin_fichier: str, feuille: str = "Sheet1") -> pd.DataFrame:
    """Charge le fichier Excel brut et affiche un diagnostic initial."""
    df = pd.read_excel(chemin_fichier, sheet_name=feuille)
    print("Dimensions :", df.shape)
    print(df.isna().sum().sort_values(ascending=False))
    return df