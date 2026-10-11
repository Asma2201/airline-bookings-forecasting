"""Blocs 33-35 — Prévision finale par agence : multi-horizon (ML) + fallback proportionnel."""
import pandas as pd
import numpy as np
import lightgbm as lgb
from src.agence_features import FEATURES


def prevision_multi_horizon(panel_model_avec_horizons: pd.DataFrame, horizons: range = range(1, 6),
                             date_depart: str = "2026-07-01") -> pd.DataFrame:
    """
    Un modèle LightGBM séparé par horizon (évite l'aplatissement de la récursivité).
    ATTENTION : approche diagnostiquée instable (963 catégories d'agence, ~27k lignes)
    -> à valider avec prevision_proportionnelle() avant usage en production.
    """
    predictions = {}
    for h in horizons:
        data_h = panel_model_avec_horizons.dropna(subset=FEATURES + [f"cible_h{h}"])
        X_h = data_h[FEATURES]
        y_h = np.log1p(data_h[f"cible_h{h}"].clip(lower=0))

        modele = lgb.LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, random_state=42)
        modele.fit(X_h, y_h, categorical_feature=["agence_id"])

        derniere_ligne = panel_model_avec_horizons.sort_values("date").groupby("agence").tail(1)
        pred_log = modele.predict(derniere_ligne[FEATURES])
        pred = np.clip(np.expm1(pred_log), a_min=0, a_max=None)

        mois_cible = pd.Timestamp(date_depart) + pd.DateOffset(months=h)
        predictions[mois_cible] = pd.DataFrame({
            "agence": derniere_ligne["agence"].values, "date": mois_cible, "prevision": pred
        })
    return pd.concat(predictions.values(), ignore_index=True)


def prevision_proportionnelle(panel: pd.DataFrame, prevision_globale: pd.DataFrame,
                               date_poids_min: str = "2025-08-01") -> pd.DataFrame:
    """
    Fallback recommandé : répartit la prévision globale SARIMA (déjà validée)
    selon le poids historique récent de chaque agence.
    Cohérence garantie par construction avec le total global.
    """
    poids = panel[panel["date"] >= date_poids_min].groupby("agence")["air_bookings"].sum()
    poids = poids[poids > 0]
    poids = poids / poids.sum()

    lignes = []
    for date, valeur_globale in prevision_globale["Prévision"].items():
        for agence, part in poids.items():
            lignes.append({"agence": agence, "date": date, "prevision": valeur_globale * part,
                            "methode": "Répartition proportionnelle (SARIMA global)"})
    return pd.DataFrame(lignes)


def verifier_coherence(prevision_par_agence: pd.DataFrame, prevision_globale: pd.DataFrame) -> pd.DataFrame:
    """Compare la somme des prévisions par agence au total global, mois par mois."""
    total_par_mois = prevision_par_agence.groupby("date")["prevision"].sum()
    ecarts = ((total_par_mois.values - prevision_globale["Prévision"].values)
              / prevision_globale["Prévision"].values * 100)
    return pd.DataFrame({
        "total_agences": total_par_mois.values,
        "total_global": prevision_globale["Prévision"].values,
        "ecart_pct": ecarts.round(1),
    }, index=total_par_mois.index)