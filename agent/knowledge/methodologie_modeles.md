# Méthodologie des modèles de prévision

Ce document décrit comment la prévision des réservations aériennes a été construite : préparation de la série globale, modèles comparés, choix du modèle retenu, prévisions du second semestre 2026, prévision par agence et abandon du modèle LightGBM par agence. Les chiffres viennent du notebook d'analyse (stage.ipynb) et du code du projet (dossier src/).

## Préparation de la série globale

### Construction de la série

- La série globale est la somme mensuelle de la colonne Air Net Bookings, toutes agences confondues (fonction construire_serie_complete dans src/global_series.py).
- Les mois dont le nombre de lignes est anormalement bas (moins de 50 lignes) sont considérés comme des erreurs de collecte : leur valeur est remplacée par une interpolation linéaire. Seul mai 2026 est concerné (5 lignes). Sa valeur interpolée entre avril et juin 2026 est 67 828,5.

### Stationnarité et différenciation

- Test ADF (Dickey-Fuller augmenté) sur la série : statistique -1,0845, p-value 0,7212.
- La p-value est supérieure à 0,05 : la série n'est pas stationnaire. Les modèles SARIMA utilisent donc une différenciation simple et une différenciation saisonnière (d = 1, D = 1).

### Traitement du trou Covid (2020-2023)

- Les données couvrent 2019, puis janvier 2024 à juillet 2026. Il n'y a aucune donnée entre 2020 et 2023.
- SARIMA et Holt-Winters ont besoin d'une série continue : ils sont entraînés uniquement sur la série janvier 2024 - juillet 2026 (31 points mensuels).
- Prophet tolère les trous dans la série : il est entraîné avec 2019 inclus.

### Découpage entraînement / test

- Entraînement : janvier 2024 à janvier 2026 (25 points).
- Test : février à juillet 2026 (6 points).

## Modèles comparés

### Description des modèles

Paramètres tels qu'ils apparaissent dans src/global_models.py :

- **Baseline naïve** : reprend les 6 dernières valeurs de la période d'entraînement comme prévision des 6 mois de test. Elle sert de point de comparaison minimal.
- **Holt-Winters** (lissage exponentiel) : tendance additive, saisonnalité additive, période de 12 mois.
- **SARIMA** : ordres (1,1,1)(1,1,1,12), sans contrainte de stationnarité ni d'inversibilité (enforce_stationarity=False, enforce_invertibility=False).
- **Prophet** : saisonnalité annuelle activée, saisonnalités hebdomadaire et journalière désactivées, changepoint_prior_scale = 0,05. Entraîné avec 2019 inclus.

### Métriques utilisées

- MAE : erreur absolue moyenne, en nombre de réservations.
- RMSE : racine de l'erreur quadratique moyenne, pénalise davantage les grosses erreurs.
- MAPE : erreur absolue moyenne en pourcentage de la valeur réelle.

## Résultats sur la période de test (février-juillet 2026)

| Modèle | MAE | RMSE | MAPE |
|---|---|---|---|
| SARIMA | 6 808,88 | 7 965,01 | 11,30 % |
| Holt-Winters | 7 699,09 | 9 801,44 | 12,74 % |
| Prophet | 8 496,00 | 10 533,39 | 13,92 % |
| Baseline naïve | 12 553,92 | 14 326,29 | 22,03 % |

Sur ce test de 6 mois, SARIMA a la plus petite erreur sur les trois métriques. Les trois modèles font nettement mieux que la baseline naïve.

## Validation glissante

La validation glissante répète l'évaluation sur 3 fenêtres successives de 3 mois, pour vérifier que le classement ne dépend pas d'un seul découpage.

| Modèle | Fenêtre 1 | Fenêtre 2 | Fenêtre 3 | MAE moyenne |
|---|---|---|---|---|
| SARIMA | 8 422,90 | 5 340,40 | 10 243,22 | 8 002,17 |
| Holt-Winters | 7 547,19 | 4 343,84 | 11 452,32 | 7 781,12 |
| Prophet | 4 116,59 | 2 438,46 | 14 825,46 | 7 126,84 |

**Point important : en validation glissante, c'est Prophet qui a la plus petite MAE moyenne (7 126,84), devant Holt-Winters (7 781,12) et SARIMA (8 002,17).** Le classement n'est donc pas le même que sur le test de 6 mois. Prophet est en revanche le modèle le plus instable d'une fenêtre à l'autre : sa MAE va de 2 438,46 à 14 825,46.

## Choix du modèle retenu : SARIMA

### Modèle final

Le modèle retenu est SARIMA (1,1,1)(1,1,1,12). Pour produire les prévisions, il est réentraîné sur toute la série continue, de janvier 2024 à juillet 2026 (fonction prevision_globale_finale dans src/global_forecast.py), avec un horizon de 5 mois (août à décembre 2026).

### Pourquoi SARIMA plutôt que Prophet ou Holt-Winters

Éléments du notebook qui justifient ce choix :

- SARIMA a la meilleure MAE, la meilleure RMSE et la meilleure MAPE sur le test de 6 mois (février-juillet 2026).
- Les résidus de SARIMA ne sont pas autocorrélés (test de Ljung-Box, lags = 5, p = 0,655) : le modèle a capté la structure de la série. Les résidus de Prophet sont autocorrélés (test de Ljung-Box, lags = 12, p = 0,0017) : une partie de la structure n'est pas captée.
- Prophet est le plus instable d'une fenêtre de validation à l'autre (MAE de 2 438 à 14 825), même si sa MAE moyenne est la plus basse.

### Raison finale présentée à l'encadrant

A COMPLETER.

### Diagnostic des résidus

Le premier résidu de SARIMA (janvier 2024, 99 600) est un effet de démarrage de la différenciation : le modèle n'a pas encore d'historique pour ce premier point. Ce n'est pas une anomalie des données.

### Recherche des ordres par AIC

Une recherche des ordres p et q (de 0 à 2) par le critère AIC a été tentée, mais elle n'est pas exploitable : les AIC valent exactement 2 fois le nombre de paramètres (6, 8, 10...). C'est le signe d'un ajustement dégénéré, dû au faible nombre de points (25) combiné à une double différenciation. Les ordres (1,1,1)(1,1,1,12) ont donc été gardés par défaut.

## Prévisions du second semestre 2026

### Prévisions SARIMA avec intervalle de confiance à 95 %

| Mois | Prévision | Borne basse | Borne haute | Largeur IC | Écart vs moyenne 2019 | Holt-Winters |
|---|---|---|---|---|---|---|
| Août 2026 | 77 067 | 62 217 | 91 918 | 38,5 % | -33,6 % | 56 211 |
| Septembre 2026 | 59 203 | 38 591 | 79 815 | 69,6 % | -49,0 % | 67 826 |
| Octobre 2026 | 90 693 | 64 935 | 116 450 | 56,8 % | -21,8 % | 65 611 |
| Novembre 2026 | 43 351 | 13 593 | 73 108 | 137,3 % | -62,6 % | 54 590 |
| Décembre 2026 | 72 575 | 38 758 | 106 392 | 93,2 % | -37,5 % | 48 408 |

- La largeur de l'intervalle de confiance est exprimée en pourcentage de la prévision.
- L'écart est calculé par rapport à la moyenne mensuelle de 2019 (116 047).
- L'incertitude grandit avec l'horizon. **Novembre 2026 est le mois le moins fiable** (intervalle de 137,3 % de la prévision).

### Divergence entre SARIMA et Holt-Winters

SARIMA et Holt-Winters divergent jusqu'à 25 081 réservations (octobre 2026). La prévision mois par mois est donc fragile : il vaut mieux lire les prévisions comme un ordre de grandeur et regarder les intervalles de confiance.

### Version lissée

Une version lissée des prévisions (moyenne mobile centrée sur 3 mois) est aussi calculée : 68 135 (août), 75 654 (septembre), 64 415 (octobre), 68 873 (novembre), 57 963 (décembre). Les chiffres stockés dans la base de l'agent sont les prévisions SARIMA non lissées.

## Prévision par agence : répartition proportionnelle

### Méthode retenue

La prévision par agence n'est pas produite par un modèle propre à chaque agence. Elle répartit la prévision globale SARIMA entre les agences (fonction prevision_proportionnelle dans src/agence_forecast.py) :

1. Pour chaque agence du panel, on calcule la somme de ses réservations (Air Net Bookings) depuis le 1er août 2025, soit la période août 2025 - juillet 2026.
2. On garde uniquement les agences dont cette somme est strictement positive, et on divise chaque somme par le total : on obtient le poids de l'agence.
3. Pour chaque mois prévu, la prévision de l'agence = prévision globale SARIMA du mois x poids de l'agence.

Dans la base de l'agent, ces lignes ont la méthode "Répartition proportionnelle (SARIMA global)". 531 agences reçoivent une prévision.

### Propriétés de la méthode

- La somme des prévisions par agence est égale à la prévision globale, par construction (vérifié par la fonction verifier_coherence).
- Le poids d'une agence est le même pour tous les mois prévus : la méthode ne donne pas de saisonnalité propre à chaque agence.
- Les agences n'ont pas d'intervalle de confiance individuel (bornes vides dans la base).
- Les limites de cette méthode sont détaillées dans limites_donnees.md.

## Modèle LightGBM par agence (construit, évalué, puis abandonné)

### Données et variables du modèle

- Panel agence x mois : 963 agences, 41 409 lignes.
- 18 variables : identifiant agence, mois en sinus et cosinus, trimestre, saison haute (juin, juillet, août, décembre), retards de 1, 2, 3 et 12 mois, moyenne mobile sur 3 mois, poids historique de l'agence, réservations hôtel, voiture et assurance, part NDC, mois depuis la reprise, indicateur Ramadan, nombre d'agences actives.
- Cible transformée en log1p, valeurs négatives ramenées à 0.
- Un modèle séparé par horizon de prévision (1 à 5 mois).

### Raisons de l'abandon

a) **Incohérence avec la prévision globale.** La somme des prévisions par agence s'écarte de la prévision SARIMA de -62,3 % (août), -84,0 % (septembre), -100,0 % (octobre), +0,5 % (novembre) et -86,5 % (décembre). En octobre, les prévisions sont proches de zéro pour toutes les grandes agences.

b) **Cible très asymétrique.** La médiane est de 2 réservations par agence et par mois, pour une moyenne d'environ 69 : la plupart des agences sont très petites et quelques grandes agences concentrent le volume.

c) **Forte cardinalité de l'identifiant agence.** 963 modalités ; LightGBM affiche un avertissement sur le nombre de catégories.

Le modèle a été remplacé par la répartition proportionnelle de la prévision globale SARIMA (voir plus haut).

### Métriques du notebook à ne pas utiliser

Les métriques affichées dans le notebook pour LightGBM (MAE 2,88), XGBoost (MAE 0,16) et le premier contrôle de cohérence (écart de 3 027,8 %) ne sont pas fiables : elles mélangent l'échelle logarithmique et l'échelle réelle. Elles ne doivent pas être citées comme résultats.
