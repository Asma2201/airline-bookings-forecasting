"""Blocs 14-15 — Série globale, décomposition, préparation train/test."""
import pandas as pd
import numpy as np
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
from src.cleaning import detecter_mois_anomalie


def construire_serie_complete(df: pd.DataFrame, seuil: int = 50) -> pd.Series:
    """Agrège Air Net Bookings par mois, corrige les mois suspects par interpolation."""
    mois_suspects = detecter_mois_anomalie(df, seuil)
    serie = df.groupby("date")["Air Net Bookings"].sum().sort_index()
    serie.loc[serie.index.isin(mois_suspects)] = np.nan
    return serie.interpolate(method="linear")


def decomposer_serie(serie: pd.Series, period: int = 12):
    """Bloc 14 — retourne l'objet de décomposition (tendance/saisonnalité/résidu)."""
    return seasonal_decompose(serie, model="additive", period=period)


def tester_stationnarite(serie: pd.Series) -> dict:
    stat, p_value = adfuller(serie.dropna())[:2]
    return {"statistic": stat, "p_value": p_value, "stationnaire": p_value < 0.05}


def preparer_train_test(serie_complete: pd.Series, date_debut: str = "2024-01-01",
                         n_test: int = 6):
    """Bloc 15 — retourne (serie_continue, train, test)."""
    serie_continue = serie_complete.loc[date_debut:].asfreq("MS")
    train = serie_continue.iloc[:-n_test]
    test = serie_continue.iloc[-n_test:]
    return serie_continue, train, test