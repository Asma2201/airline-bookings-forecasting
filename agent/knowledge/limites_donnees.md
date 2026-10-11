# Limites des données et du modèle

Ce document liste les limites connues des données Amadeus et des prévisions. L'agent doit s'y référer quand on lui demande si une prévision est fiable, ou pourquoi un chiffre doit être lu avec prudence. Pour l'interprétation métier des mouvements (vacances, fêtes, crises), voir interpretation_metier.md.

## Résumé des principales limites du modèle et des données

- Série courte : seulement 31 points mensuels continus (janvier 2024 à juillet 2026) pour la série globale.
- Trou 2020-2023 : aucune information sur la chute et la reprise post-Covid.
- Qualité des données : mai 2026 interpolé, février et juillet 2026 sans nom d'agence, lignes multiples par clé métier non expliquées, agence sans nom "-".
- Volumes en baisse continue par rapport à 2019, causes non vérifiées.
- Intervalles de confiance très larges au-delà de 2 mois (novembre 2026 : 137,3 % de la prévision) et forte divergence entre SARIMA et Holt-Winters (jusqu'à 25 081 réservations en octobre 2026).
- Le modèle global n'intègre aucune variable exogène (vacances, fêtes, crises).
- Répartition par agence : poids fixes calculés sur une période incomplète, volume des agences exclues redistribué, pas d'intervalle de confiance par agence.
- Pas de données par compagnie aérienne dans la base de l'agent.

Chaque point est détaillé dans les sections suivantes.

## Volume et continuité des données

### Série courte

- La série globale continue ne compte que 31 points mensuels (janvier 2024 à juillet 2026).
- Les modèles SARIMA et Holt-Winters sont entraînés sur 25 points seulement (janvier 2024 à janvier 2026) pour la phase de test. C'est peu pour estimer une saisonnalité annuelle : on dispose d'à peine plus de deux cycles de 12 mois.
- Conséquence visible : la recherche des ordres SARIMA par AIC n'est pas exploitable (ajustement dégénéré), voir methodologie_modeles.md.

### Trou Covid 2020-2023

- Les années 2020, 2021, 2022 et 2023 sont absentes des données.
- On n'a donc aucune information sur la chute des réservations pendant le Covid ni sur le rythme de la reprise.
- 2019 ne peut pas être raccordée à 2024 dans une série continue : SARIMA et Holt-Winters n'utilisent pas 2019. Seul Prophet l'utilise.

### Baisse continue par rapport à 2019

Les volumes ne reviennent pas au niveau de 2019 et baissent d'année en année :

| Période | Air Net Bookings | En % de 2019 (même période) |
|---|---|---|
| 2019, année complète | 1 392 569 | 100 % |
| 2024, année complète | 989 882 | 71,1 % |
| 2025, année complète | 838 458 | 60,2 % |
| 2026, janvier à juillet | 434 236 | 53,1 % |

Sur janvier-juillet, 2026 représente 89,4 % de 2025. Constat : Observé.

Les causes de cette baisse ne sont pas vérifiées. Les pistes listées dans interpretation_metier.md (section 3) ont toutes le statut Hypothèse : crise opérationnelle de Tunisair en 2025, déplacement d'une partie des ventes vers la vente directe des compagnies ou vers d'autres canaux que le GDS, perte ou départ de certaines agences. Elles doivent être testées par compagnie et par agence avant d'être présentées comme des explications.

## Qualité des données sources

### Mai 2026 incomplet et interpolé

- Mai 2026 ne compte que 5 lignes, contre plus de 5 000 pour les autres mois.
- Dans la série globale, sa valeur est remplacée par une interpolation linéaire entre avril et juin 2026 : 67 828,5. Ce n'est pas un volume réel.
- Au niveau agence, mai 2026 n'est pas interpolé : les 5 lignes présentes totalisent 0 réservation dans le panel.

### Février et juillet 2026 sans nom d'agence

- En février 2026 (5 580 lignes) et en juillet 2026 (5 018 lignes), toutes les lignes ont un nom d'agence vide ("-"). Le numéro de compte (Master Account Number) vaut aussi "-". L'Office ID, lui, est renseigné (658 Office ID distincts en février, 652 en juillet). Statut : Observé (vérifié en exécutant le code du projet sur le fichier source).
- Ces deux mois sont bien présents dans la série globale (52 206 en février, 52 105 en juillet), mais ils sont absents du panel par agence et donc des données réelles par agence de la base de l'agent.
- Conséquence : pour 2026, la somme des volumes réels par agence est inférieure au total global.
- Il serait peut-être possible de retrouver l'agence de ces lignes à partir de l'Office ID, en utilisant la correspondance Office ID - agence des autres mois. Statut : Déduction, non testé.
- Raison de l'absence du nom d'agence dans l'export pour ces deux mois : A COMPLETER.

### Agence sans nom ("-")

- Une agence sans nom ("-") regroupe 10 910 lignes. Elle est exclue du modèle par agence.
- L'essentiel de ces lignes correspond à février et juillet 2026 (10 598 lignes sur 10 910) : "-" n'est donc pas une vraie agence mais surtout l'absence de nom d'agence sur ces deux mois. Les autres lignes "-" sont dispersées sur 2019, 2024, 2025 et 2026 (quelques lignes par mois).
- Écart 553 / 552 : le notebook compte 553 agences avec au moins 24 mois de données, la base de l'agent en contient 552. L'écart vient de l'agence "-" : elle a 33 mois de données, donc elle est comptée dans les 553, puis elle est retirée du panel. Statut : Observé (vérifié).

### Lignes multiples par clé métier

- 275 452 lignes ont la même clé métier (année, mois, Master Account Number, Office ID, Provider Code) sans être des doublons exacts.
- Elles sont additionnées lors de l'agrégation.
- La raison de ces lignes multiples n'est pas connue : A COMPLETER.

### Valeurs nulles, négatives et colonnes vides

- Air Net Bookings contient 26,1 % de zéros et des valeurs négatives (minimum -1 763) : c'est un volume net des annulations.
- ATLA et EAC : 100 % de zéros, colonnes exclues.
- NDC : 99,2 % de zéros, corrélation de Spearman avec Air Net Bookings r = 0,041.
- Car, Insurance, Rail, Cruise : environ 100 % de zéros. Hotel : 99,2 % de zéros.

## Limites de la prévision globale

### Fiabilité de la prévision de chaque mois (août à décembre 2026)

L'incertitude grandit avec l'horizon. Pour savoir si la prévision d'un mois est fiable, il faut regarder la largeur de son intervalle de confiance à 95 % (exprimée en % de la prévision SARIMA) :

- **Août 2026** : prévision 77 067, intervalle de 62 217 à 91 918, largeur 38,5 %. C'est l'intervalle le plus étroit du semestre.
- **Septembre 2026** : prévision 59 203, intervalle de 38 591 à 79 815, largeur 69,6 %.
- **Octobre 2026** : prévision 90 693, intervalle de 64 935 à 116 450, largeur 56,8 %. C'est aussi le mois où SARIMA et Holt-Winters divergent le plus (25 081 réservations).
- **Novembre 2026** : prévision 43 351, intervalle de 13 593 à 73 108, largeur 137,3 %. **Novembre 2026 est le mois le moins fiable** : l'intervalle est plus large que la prévision elle-même.
- **Décembre 2026** : prévision 72 575, intervalle de 38 758 à 106 392, largeur 93,2 %.

Au-delà de 2 mois, les intervalles sont très larges. Les bonnes métriques de SARIMA (meilleure MAE, RMSE et MAPE sur le test février-juillet 2026) justifient le choix du modèle, mais elles ne rendent pas fiable chaque mois prévu : la prévision d'un mois doit toujours être lue avec son intervalle de confiance.

### Divergence entre modèles

SARIMA et Holt-Winters divergent jusqu'à 25 081 réservations (octobre 2026). La prévision mois par mois est fragile.

### Pas de variable exogène

Le modèle global SARIMA n'intègre aucune variable exogène : ni vacances, ni fêtes, ni crises. Il reproduit la tendance et la saisonnalité observées en 2024-2026. Un événement nouveau (crise, conflit, changement de calendrier des fêtes) n'est pas anticipé par le modèle.

## Limites de la répartition par agence

### Poids calculés sur août 2025 - juillet 2026

- Le poids de chaque agence est la somme de ses réservations depuis le 1er août 2025 (code : src/agence_forecast.py, paramètre date_poids_min = "2025-08-01").
- Sur ces 12 mois, seuls 9 mois contiennent réellement des données par agence : février 2026 et juillet 2026 sont absents du panel (nom d'agence vide), et mai 2026 ne compte que 5 lignes pour un total de 0 réservation.
- Les poids reposent donc sur août 2025 à janvier 2026, mars, avril et juin 2026.
- Seules les agences dont la somme est strictement positive reçoivent une prévision : 531 agences sur les 552 du panel. Les 21 autres n'ont pas de prévision : 11 ont une somme nulle ou négative sur la période, 10 n'ont aucune donnée sur la période.

### Redistribution du volume des agences exclues

- Le panel exclut l'agence "-" et les agences avec moins de 24 mois de données.
- La prévision globale SARIMA, elle, inclut tout le volume, y compris celui de ces agences exclues.
- Comme la répartition force la somme des agences à égaler la prévision globale, le volume des agences exclues est redistribué entre les agences du panel, au prorata de leur poids. Les prévisions par agence sont donc probablement légèrement surestimées. Statut : Déduction (conséquence du code, non mesurée agence par agence).
- Ordre de grandeur, calculé en exécutant le code du projet : entre août 2025 et juin 2026 (hors février et mai), la part du volume global qui n'est pas dans le panel va de 1,75 % à 3,39 % selon le mois.

### Autres limites de la répartition

- Le poids d'une agence est fixe pour tous les mois prévus : pas de saisonnalité propre à l'agence, pas de tendance propre à l'agence.
- Pas d'intervalle de confiance par agence.
- Le poids utilisé pour la répartition n'est pas la colonne poids_historique de la table dim_agence : poids_historique est calculé sur tout l'historique de l'agence, alors que la répartition utilise août 2025 - juillet 2026.

## Données absentes de la base de l'agent

### Pas de données par compagnie aérienne

- La base de l'agent (amadeus_forecast.db) contient seulement deux tables : fait_reservations (volumes réels et prévus par agence et pour le total global) et dim_agence (caractéristiques des agences).
- Il n'y a aucune donnée par compagnie aérienne (Provider Code, Provider Name) dans la base, même si le fichier source en contient.
- Conséquence : les hypothèses liées à une compagnie, par exemple l'effet de la crise de Tunisair en 2025, ne peuvent pas être vérifiées avec l'outil SQL. Elles restent au statut Hypothèse.
- Le fichier outputs/fait_canal.csv (répartition NDC / classique par agence et par mois) existe mais n'est pas chargé dans la base de l'agent.

### Autres points à connaître pour interroger la base

- Les données réelles par agence ne couvrent que les 552 agences du panel : la somme des agences n'est pas égale au total global (agence "-", petites agences, février et juillet 2026).
- Pour un volume global, il faut utiliser la ligne agence = 'TOTAL_GLOBAL'.
