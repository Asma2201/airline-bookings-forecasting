# config.py — à la racine
from pathlib import Path

RACINE_PROJET = Path(__file__).parent
CHEMIN_DONNEES_BRUTES = RACINE_PROJET / "data" / "raw" / "Data_stage.xlsx"
CHEMIN_OUTPUTS = RACINE_PROJET / "outputs"