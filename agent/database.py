"""Convertit les outputs du pipeline forecasting en base SQLite interrogeable par l'agent."""
import sqlite3
import pandas as pd
from pathlib import Path

CHEMIN_DB = Path(__file__).parent / "amadeus_forecast.db"
DOSSIER_OUTPUTS = Path(__file__).parent.parent / "outputs"


def construire_base(dossier_outputs: str | Path = DOSSIER_OUTPUTS, chemin_db: str | Path = CHEMIN_DB):
    """Lit fait_reservations.csv et dim_agence.csv, les charge dans SQLite."""
    conn = sqlite3.connect(chemin_db)

    fait = pd.read_csv(f"{dossier_outputs}/fait_reservations.csv")
    dim_agence = pd.read_csv(f"{dossier_outputs}/dim_agence.csv")

    fait.to_sql("fait_reservations", conn, if_exists="replace", index=False)
    dim_agence.to_sql("dim_agence", conn, if_exists="replace", index=False)

    conn.close()
    print(f"Base créée : {chemin_db} ({len(fait)} lignes fait_reservations, {len(dim_agence)} agences)")


if __name__ == "__main__":
    construire_base()