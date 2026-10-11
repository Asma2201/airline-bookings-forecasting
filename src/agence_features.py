"""Bloc 29 — Encodage, nettoyage final, split, cibles multi-horizon."""
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder

FEATURES = [
    "agence_id", "mois_sin", "mois_cos", "trimestre", "saison_haute",
    "air_bookings_lag1", "air_bookings_lag2", "air_bookings_lag3", "air_bookings_lag12",
    "air_bookings_ma3", "poids_agence",
    "hotel_bookings", "car_bookings", "insurance_bookings",
    "part_ndc", "mois_depuis_reprise", "ramadan", "nb_agences_actives",
]


def preparer_panel_model(panel: pd.DataFrame) -> tuple[pd.DataFrame, LabelEncoder]:
    """Nettoyage, clip des négatifs, encodage agence, cible log."""
    lag_cols = [c for c in panel.columns if "lag" in c]
    panel_model = panel.dropna(subset=lag_cols).copy()

    panel_model["air_bookings"] = panel_model["air_bookings"].clip(lower=0)
    for col in lag_cols + ["air_bookings_ma3"]:
        panel_model[col] = panel_model[col].clip(lower=0)

    encodeur = LabelEncoder()
    panel_model["agence_id"] = encodeur.fit_transform(panel_model["agence"])

    panel_model["air_bookings_log"] = np.log1p(panel_model["air_bookings"])
    panel_model = panel_model.replace([np.inf, -np.inf], np.nan)
    panel_model = panel_model.dropna(subset=FEATURES + ["air_bookings_log"])
    return panel_model, encodeur


def split_train_test(panel_model: pd.DataFrame, n_mois_test: int = 3):
    date_limite = panel_model["date"].max() - pd.DateOffset(months=n_mois_test)
    train = panel_model[panel_model["date"] <= date_limite]
    test = panel_model[panel_model["date"] > date_limite]
    return (train[FEATURES], np.log1p(train["air_bookings"]),
            test[FEATURES], np.log1p(test["air_bookings"]))


def ajouter_cibles_horizon(panel_model: pd.DataFrame, horizons: range = range(1, 6)) -> pd.DataFrame:
    """Crée cible_h1 à cible_h5 : valeur réelle à horizon h mois plus tard, par agence."""
    panel_model = panel_model.sort_values(["agence", "date"]).copy()
    for h in horizons:
        panel_model[f"cible_h{h}"] = panel_model.groupby("agence")["air_bookings"].shift(-h)
    return panel_model