"""Prévision finale globale SARIMA — sert de référence de cohérence pour le forecasting par agence."""
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX


def prevision_globale_finale(serie_continue: pd.Series, horizon: int = 5,
                              order=(1, 1, 1), seasonal_order=(1, 1, 1, 12)) -> pd.DataFrame:
    """Réentraîne SARIMA sur toute la série et prédit `horizon` mois futurs."""
    modele = SARIMAX(serie_continue, order=order, seasonal_order=seasonal_order,
                      enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)

    forecast = modele.get_forecast(steps=horizon)
    resultat = forecast.predicted_mean.to_frame(name="Prévision")
    intervalle = forecast.conf_int()
    resultat["Borne basse"] = intervalle.iloc[:, 0]
    resultat["Borne haute"] = intervalle.iloc[:, 1]
    return resultat