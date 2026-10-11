# Glossaire métier

Ce glossaire définit les termes utilisés dans le projet et dans la base de l'agent. Pour les notions métier déjà décrites dans interpretation_metier.md (segment aérien, réservations nettes, NDC, code AZ), ce glossaire renvoie vers ce fichier, qui fait référence. En cas de différence, c'est interpretation_metier.md qui s'applique.

## Réservations et indicateurs

### Air Net Bookings (réservations nettes)

Indicateur principal du projet : volume de réservations aériennes nettes, c'est-à-dire réservations moins annulations. Il peut être nul ou négatif (26,1 % de zéros, minimum -1 763). L'unité (segments aériens) et la date prise en compte (date de la transaction, pas date du vol) sont décrites dans interpretation_metier.md, section 1.1, avec leur statut.

### Segment aérien

Unité de comptage des réservations aériennes dans un GDS : un aller simple direct = 1 segment, un aller-retour direct = 2 segments. Définition complète et statut dans interpretation_metier.md, section 1.1.

Attention : le mot "segment" a un autre sens dans la table dim_agence (voir "Segment d'agence" plus bas).

### NDC

Canal de réservation basé sur le standard NDC de l'IATA (distribution moderne). La colonne Air Net Bookings NDC donne les réservations passées par ce canal. Le NDC est marginal dans nos données (99,2 % de zéros, Spearman r = 0,041 avec Air Net Bookings). Définition et statut dans interpretation_metier.md, section 1.2.

### Canal classique

Dans le projet, le canal "Classique" est défini comme le total des réservations aériennes moins les réservations NDC : Classique = Air Net Bookings - Air Net Bookings NDC, avec les valeurs négatives ramenées à 0 (code : fonction construire_fait_canal dans src/export_powerbi.py). Cette définition évite de compter deux fois les réservations NDC. Elle suppose que le NDC est inclus dans le total Air Net Bookings, ce qui reste à vérifier (voir interpretation_metier.md, section 1.2).

## Agences et compagnies

### Agence (Master Account Name)

Agence de voyages cliente d'Amadeus, identifiée par son nom (Master Account Name) et son numéro de compte (Master Account Number). Les données contiennent 963 agences, dont 553 avec au moins 24 mois de données. La base de l'agent contient 552 agences : l'agence sans nom "-" en est exclue (voir limites_donnees.md).

### Office ID

Identifiant d'un bureau (point de vente) d'une agence dans Amadeus. Une agence peut avoir plusieurs Office ID. Le préfixe indique la ville (TUN = Tunis, MIR = Monastir), statut Déduction : voir interpretation_metier.md, section 1.

### Compagnie aérienne (Provider Code, Provider Name)

Compagnie qui opère le vol réservé, identifiée par son code (par exemple TU pour Tunisair) et son nom. Ces colonnes existent dans le fichier source, mais la base de l'agent ne contient aucune donnée par compagnie.

### Code AZ

Le code AZ correspond à ITA Airways pour 2024-2026, même si le libellé affiché est encore "Alitalia". Voir interpretation_metier.md, section 7.

### Segment d'agence (colonne segment de dim_agence)

Classe de taille d'une agence, calculée sur son volume total historique (code : fonction construire_dim_agence dans src/export_powerbi.py) :

| Segment | Règle |
|---|---|
| Petite | 70 % des agences au plus petit volume |
| Moyenne | Entre le quantile 70 % et le quantile 95 % |
| Top 20 | Au-dessus du quantile 95 % |

Attention : malgré son nom, le segment "Top 20" ne contient pas forcément 20 agences. Ce sont les agences au-dessus du quantile 95 % du volume total historique, et non les 20 premières agences. Le nombre d'agences par segment se compte dans la table dim_agence (colonne segment).

## Termes de la base de l'agent

### TOTAL_GLOBAL

Valeur spéciale de la colonne agence dans la table fait_reservations : elle représente le total agrégé de toutes les agences. Pour un volume global, il faut filtrer sur agence = 'TOTAL_GLOBAL' et ne pas additionner les agences.

### type_donnee : Réel et Prévision

- Réel : volume historique observé (2019, puis janvier 2024 à juillet 2026). Mai 2026 est une valeur interpolée pour le total global.
- Prévision : volume prévu pour août à décembre 2026.

### methode

- Historique : donnée réelle.
- SARIMA global : prévision du total global par le modèle SARIMA.
- Répartition proportionnelle (SARIMA global) : prévision par agence obtenue en répartissant la prévision globale selon le poids de l'agence.

### Borne basse et borne haute

Limites de l'intervalle de confiance à 95 % de la prévision SARIMA. Elles ne sont renseignées que pour les prévisions du total global.

### Poids historique et poids de répartition

- poids_historique (table dim_agence) : part de l'agence dans le volume total, calculée sur tout son historique.
- Poids de répartition : part de l'agence calculée sur août 2025 - juillet 2026, utilisée pour répartir la prévision globale. Ce n'est pas la même valeur que poids_historique.

## Termes de modélisation

### SARIMA

Modèle statistique de série temporelle avec saisonnalité. Le modèle retenu est SARIMA (1,1,1)(1,1,1,12) : une différenciation simple, une différenciation saisonnière et une saison de 12 mois. Voir methodologie_modeles.md.

### Holt-Winters

Modèle de lissage exponentiel avec tendance et saisonnalité (ici additives, saison de 12 mois). Utilisé comme modèle de comparaison.

### Prophet

Modèle de prévision développé par Meta, qui tolère les trous dans la série. C'est le seul des modèles comparés qui utilise aussi l'année 2019 : il est entraîné sur 2019 et sur la période 2024-2026, alors que SARIMA et Holt-Winters n'utilisent que 2024-2026.

### Baseline naïve

Prévision de référence minimale : on reprend les dernières valeurs observées. Un modèle utile doit faire mieux qu'elle.

### MAE, RMSE, MAPE

- MAE : erreur absolue moyenne, en nombre de réservations.
- RMSE : racine de l'erreur quadratique moyenne, plus sensible aux grosses erreurs.
- MAPE : erreur absolue moyenne en pourcentage de la valeur réelle.

### Validation glissante

Évaluation répétée sur plusieurs fenêtres de test successives (ici 3 fenêtres de 3 mois), pour vérifier la stabilité d'un modèle.

### Intervalle de confiance (IC) à 95 %

Plage dans laquelle la valeur réelle devrait se trouver avec une probabilité de 95 %, selon le modèle. Plus il est large, moins la prévision est précise.

### Test ADF et différenciation

Le test ADF (Dickey-Fuller augmenté) vérifie si une série est stationnaire. La différenciation consiste à modéliser les variations d'un mois à l'autre (d = 1) et d'une année à l'autre (D = 1) plutôt que les niveaux.

### Test de Ljung-Box

Test qui vérifie si les résidus d'un modèle sont autocorrélés. Des résidus non autocorrélés indiquent que le modèle a capté la structure de la série.
