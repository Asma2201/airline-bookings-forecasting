"""Blocs 16-20 — Modèles globaux (baseline, HW, SARIMA, Prophet) et comparaison."""
import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error


def baseline_naive(train: pd.Series, n_test: int) -> np.ndarray:
    return train.iloc[-n_test:].values


def entrainer_holt_winters(train: pd.Series, n_test: int):
    modele = ExponentialSmoothing(train, trend="add", seasonal="add", seasonal_periods=12).fit()
    return modele, modele.forecast(n_test)


def entrainer_sarima(train: pd.Series, n_test: int, order=(1, 1, 1), seasonal_order=(1, 1, 1, 12)):
    modele = SARIMAX(train, order=order, seasonal_order=seasonal_order,
                      enforce_stationarity=False, enforce_invertibility=False).fit(disp=False)
    pred = modele.get_forecast(steps=n_test).predicted_mean
    return modele, pred


def entrainer_prophet(serie_complete: pd.Series, train: pd.Series, n_test: int,
                       changepoint_prior_scale: float = 0.05):
    train_dates = serie_complete.index[serie_complete.index <= train.index.max()]
    train_complet = serie_complete.loc[
        serie_complete.index.isin(train_dates) | (serie_complete.index < train.index.min())
    ]
    df_prophet = train_complet.reset_index()
    df_prophet.columns = ["ds", "y"]

    modele = Prophet(yearly_seasonality=True, weekly_seasonality=False,
                      daily_seasonality=False, changepoint_prior_scale=changepoint_prior_scale)
    modele.fit(df_prophet)

    futur = modele.make_future_dataframe(periods=n_test, freq="MS")
    forecast = modele.predict(futur)
    return modele, df_prophet, forecast


def calculer_metriques(reel, predit, nom: str) -> dict:
    mae = mean_absolute_error(reel, predit)
    rmse = np.sqrt(mean_squared_error(reel, predit))
    mape = np.mean(np.abs((reel - predit) / reel)) * 100
    return {"Modèle": nom, "MAE": round(mae, 2), "RMSE": round(rmse, 2), "MAPE (%)": round(mape, 2)}


def comparer_modeles(test, baseline_pred, pred_hw, pred_sarima, pred_prophet) -> pd.DataFrame:
    return pd.DataFrame([
        calculer_metriques(test.values, baseline_pred, "Baseline naïve"),
        calculer_metriques(test.values, pred_hw.values, "Holt-Winters"),
        calculer_metriques(test.values, pred_sarima.values, "SARIMA"),
        calculer_metriques(test.values, pred_prophet.values, "Prophet"),
    ]).sort_values("MAPE (%)")