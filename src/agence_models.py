"""Blocs 30-32 — Entraînement LightGBM/XGBoost et importance des variables."""
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error
from src.agence_features import FEATURES


def entrainer_lightgbm(X_train, y_train, X_test, y_test):
    """Entraîne sur cible log, évalue en échelle réelle."""
    modele = lgb.LGBMRegressor(n_estimators=300, learning_rate=0.05, num_leaves=31, random_state=42)
    modele.fit(X_train, y_train, categorical_feature=["agence_id"])

    pred_log = modele.predict(X_test)
    pred = np.clip(np.expm1(pred_log), a_min=0, a_max=None)
    y_test_reel = np.expm1(y_test)

    mae = mean_absolute_error(y_test_reel, pred)
    return modele, pred, mae


def entrainer_xgboost(X_train, y_train, X_test, y_test):
    import xgboost as xgb
    modele = xgb.XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42)
    modele.fit(X_train, y_train)
    pred = modele.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    return modele, pred, mae


def importance_variables(modele_lgb) -> pd.DataFrame:
    return pd.DataFrame({
        "feature": FEATURES,
        "importance": modele_lgb.feature_importances_
    }).sort_values("importance", ascending=False)