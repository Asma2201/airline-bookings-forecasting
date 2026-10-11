# Interprétation métier des volumes de réservations aériennes

Ce document sert de base de connaissances métier pour l'agent. Chaque explication indique son statut :
- **Confirmé** : validé par l'encadrant.
- **Observé** : visible dans les données (pic ou baisse au bon moment).
- **Déduction** : conclusion logique à partir du fonctionnement du secteur, non confirmée officiellement.
- **Hypothèse** : événement réel et sourcé, mais son effet sur nos volumes n'est pas encore vérifié.
- **À compléter** : information manquante.

Quand l'agent utilise ce document, il doit citer le statut de l'explication. Si un mouvement n'est pas expliqué ici, il doit le dire au lieu d'inventer une cause.

---

## 1. Périmètre des données

- Source : données de réservations Amadeus (GDS) pour des agences de voyages situées en Tunisie.
- Les Office ID commencent par un code de ville (TUN = Tunis, MIR = Monastir). Statut : Déduction.
- Granularité : mensuelle. La date de chaque ligne est le dernier jour du mois (agrégation).
- Dimensions : agence (Master Account Name, Office ID), compagnie aérienne (Provider Name, Provider Code).
- Années disponibles : 2019, 2024, 2025 et 2026 de janvier à juillet. **Les années 2020 à 2023 ne sont pas dans les données.**
- Taille : 555 714 lignes, 963 agences, dont 553 avec au moins 24 mois de données. Une agence sans nom ("-") regroupe 10 910 lignes. Statut : Observé.
- **Mai 2026 est incomplet** (5 lignes seulement, contre plus de 5 000 pour les autres mois). Sa valeur (67 828,5) a été remplacée par une interpolation linéaire entre avril et juin 2026 : ce n'est pas un volume réel. Statut : Observé.
- Les colonnes Car, Insurance, Rail et Cruise sont à zéro sur près de 100 % des lignes, Hotel sur 99,2 % : le projet porte sur l'aérien. Statut : Observé.

### 1.1 Ce que mesure Air Net Bookings

- **Unité : segments aériens nets.** Statut : Déduction. Un GDS comme Amadeus est rémunéré par les compagnies aériennes pour chaque segment réservé. Ses indicateurs commerciaux comptent donc en segments : un aller simple direct = 1 segment, un aller-retour direct = 2 segments, un aller-retour avec escale = 4 segments. "Net" signifie segments réservés moins segments annulés. Le caractère "net" est confirmé par les données : 26,1 % des lignes valent zéro et certaines valeurs sont négatives (minimum -1 763), ce qui n'est possible que si les annulations sont soustraites. Statut : Observé.
- **Date : date de la transaction (réservation ou annulation), pas date du vol.** Statut : Déduction. Un volume "net" soustrait les annulations au moment où elles ont lieu, ce qui n'a de sens que sur la date de transaction. L'indicateur mesure l'activité commerciale de l'agence dans le mois. Conséquence : les pics de réservations précèdent les pics de voyages.
- Test de vérification : si le pic annuel tombe en mai-juin plutôt qu'en juillet-août, la date est bien celle de la réservation.

### 1.2 Autres colonnes

- **Air Net Bookings NDC** : réservations passées via le canal NDC (standard IATA de distribution moderne). Statut : Déduction. Le NDC est encore marginal : 99,2 % des lignes valent zéro, et sa corrélation avec Air Net Bookings est très faible (Spearman r = 0,041). Statut : Observé. À vérifier : si une ligne a une valeur NDC supérieure à Air Net Bookings, alors le NDC n'est pas inclus dans le total.
- **Air Net Bookings EAC** et **Air ATLA Confirmed Bookings** : signification non connue. Elles valent zéro sur 100 % des lignes : elles sont exclues de l'analyse. Statut : Observé.

## 2. Principe général d'interprétation

Selon l'encadrant, les pics et les baisses du volume de réservations s'expliquent généralement par des événements exogènes majeurs : crises sanitaires (Covid-19), météo, vacances scolaires, crises économiques ou géopolitiques. Statut : Confirmé (encadrant).

Règles de lecture :
- Les réservations précèdent le voyage. Pour un événement prévisible (vacances, fêtes, pèlerinage), l'effet sur les réservations apparaît en général dans les semaines ou mois qui précèdent l'événement.
- Pour un choc soudain (crise, conflit, perturbation d'une compagnie), l'effet est immédiat et peut inclure des annulations, qui font baisser les réservations nettes.
- Si une baisse touche presque toutes les agences et compagnies le même mois, la cause est probablement externe et générale. Si elle touche une seule compagnie ou une seule agence, la cause est probablement propre à cette compagnie ou à cette agence.

## 3. Référence pré-Covid et reprise

- 2019 est la dernière année avant le Covid-19. Elle sert de référence de niveau "normal".
- La chute de 2020-2021 n'est pas visible dans nos données, puisque ces années sont absentes.
- Comparer 2024 et 2025 à 2019 permet de mesurer la reprise : niveau retrouvé, dépassé ou non atteint, par agence et par compagnie.

**Constat : les volumes ne reviennent pas au niveau de 2019, ils continuent de baisser.** Statut : Observé.

| Période | Air Net Bookings | En % de 2019 (même période) |
|---|---|---|
| 2019, année complète | 1 392 569 | 100 % |
| 2024, année complète | 989 882 | 71,1 % |
| 2025, année complète | 838 458 | 60,2 % |
| 2026, janvier à juillet | 434 236 (mai interpolé) | 53,1 % |

Sur janvier-juillet, 2026 représente 89,4 % de 2025. Aucun mois de 2024 à 2026 n'atteint le niveau du même mois de 2019.

Causes possibles, non vérifiées (statut : Hypothèse) : crise opérationnelle de Tunisair en 2025 (voir section 6), déplacement d'une partie des ventes vers la vente directe des compagnies ou vers d'autres canaux que le GDS, perte ou départ de certaines agences. Il faut les tester par compagnie et par agence avant de les présenter comme des explications.

## 4. Calendrier des grandes vacances

Les grandes vacances d'été sont le principal moteur saisonnier du voyage. Comme les réservations précèdent le voyage, l'effet attendu est une hausse des réservations dans les mois précédant le début des vacances. Statut de l'effet : Hypothèse.

### 4.1 Tunisie (marché principal de nos agences)

| Année | Fin de l'année scolaire | Rentrée scolaire |
|---|---|---|
| 2019 | Samedi 29 juin 2019 | Mardi 17 septembre 2019 (retardée à cause de la présidentielle anticipée du 15 septembre) |
| 2024 | Samedi 29 juin 2024 | Lundi 16 septembre 2024 |
| 2025 | Samedi 28 juin 2025 | Lundi 15 septembre 2025 |
| 2026 | Mardi 30 juin 2026 | Mardi 15 septembre 2026 |

Sources : Tekiano, Kapitalis, Gnet, Tunisie Numérique, AllAfrica.

### 4.2 France (principale destination et première communauté tunisienne à l'étranger)

| Année | Début des vacances d'été | Rentrée scolaire |
|---|---|---|
| 2019 | Samedi 6 juillet 2019 | Lundi 2 septembre 2019 |
| 2024 | Samedi 6 juillet 2024 | Lundi 2 septembre 2024 |
| 2025 | Samedi 5 juillet 2025 | Lundi 1er septembre 2025 |
| 2026 | Samedi 4 juillet 2026 | Mardi 1er septembre 2026 |

Sources : L'Écho touristique, L'Étudiant, Onisep. Les dates d'été sont les mêmes pour les zones A, B et C.

### 4.3 Autres marchés (périodes approximatives, identiques d'une année à l'autre à quelques jours près)

- **Italie** : de mi-juin à mi-septembre, selon les régions.
- **Espagne** : de fin juin à mi-septembre, selon les régions.
- **Allemagne** : vacances échelonnées par Land, de fin juin à mi-septembre.
- **Royaume-Uni (Angleterre)** : de fin juillet à début septembre.
- **Turquie** : de mi ou fin juin à début septembre.
- **Pays du Golfe** : de fin juin ou juillet à fin août, selon les pays.
- **Amérique du Nord** : de fin juin à fin août ou début septembre.
- **Hémisphère sud (Australie, Afrique du Sud, Amérique du Sud)** : les grandes vacances tombent en décembre-janvier.

Statut des dates : Déduction, à vérifier au cas par cas si un marché devient important dans l'analyse.

## 5. Autres vacances et fêtes récurrentes

### 5.1 Vacances scolaires tunisiennes hors été

Ces périodes peuvent générer des voyages courts (familles, étudiants). Statut de l'effet : Hypothèse.

- **2019** : vacances d'hiver du 17 décembre 2018 au 1er janvier 2019 ; mi-trimestre du 4 au 10 février 2019 ; printemps du 18 au 31 mars 2019 ; une semaine du 6 au 12 mai 2019 ; mi-trimestre du 28 octobre au 3 novembre 2019 ; hiver du 16 décembre 2019 au 1er janvier 2020.
- **2024** : hiver du 17 décembre 2023 au 1er janvier 2024 ; mi-trimestre du 5 au 11 février 2024 ; printemps du 16 au 31 mars 2024 ; mi-trimestre du 28 octobre au 3 novembre 2024 ; hiver du 23 décembre 2024 au 5 janvier 2025.
- **2025** : mi-trimestre du 3 au 9 février 2025 ; printemps et Aïd el-Fitr du 24 mars au 6 avril 2025 ; mi-trimestre du 27 octobre au 2 novembre 2025 ; hiver du 22 décembre 2025 au 4 janvier 2026.
- **2026** : mi-trimestre du 2 au 8 février 2026 ; printemps, fête de l'Indépendance et Aïd el-Fitr du 16 au 29 mars 2026.

### 5.2 Pâques (vacances de printemps en Europe)

Pâques change de date chaque année, ce qui déplace les vacances de printemps européennes entre mars et avril. Statut de l'effet : Hypothèse.
- 2019 : 21 avril.
- 2024 : 31 mars.
- 2025 : 20 avril.
- 2026 : 5 avril.

### 5.3 Fêtes religieuses musulmanes

Elles suivent le calendrier lunaire et avancent d'environ 11 jours par an. Elles ne tombent donc pas au même mois en 2019 et en 2024-2026, ce qui peut créer des écarts entre années pour un même mois. Statut de l'effet : Hypothèse.

Dates approximatives (à confirmer selon l'annonce officielle de chaque année) :
- 2019 : Ramadan environ du 6 mai au 4 juin ; Aïd el-Fitr environ le 4-5 juin ; Aïd el-Adha environ le 11-12 août.
- 2024 : Ramadan environ du 11 mars au 9 avril ; Aïd el-Fitr environ le 10 avril ; Aïd el-Adha environ le 16 juin.
- 2025 : Ramadan environ du 1er au 29 mars ; Aïd el-Fitr environ le 30-31 mars ; Aïd el-Adha environ le 6 juin.
- 2026 : Ramadan environ du 18 février au 19 mars ; Aïd el-Fitr environ le 20 mars ; Aïd el-Adha environ le 26-27 mai.

### 5.4 Omra et Hajj

- **Omra** : environ 120 000 Tunisiens ont accompli la Omra en 2025. La saison 2026 a été lancée le 16 juillet 2026, avec un objectif d'environ 135 000 pèlerins selon la Fédération tunisienne des agences de voyages (source : Webdo). Les agences proposent des formules spécifiques pendant Rajab, Chaabane et le Ramadan. La Omra utilise des vols réguliers réservés par les agences : elle apparaît probablement dans nos données. Statut : Déduction.
- **Hajj** : en 2025, départs des pèlerins tunisiens à partir du 18 mai et retours entre le 12 et le 25 juin (source : Tunisair, via L'Économiste maghrébin). Le Hajj passe par des vols spéciaux affrétés dans un programme encadré par l'État, avec un quota fixe de pèlerins. Ces vols ne sont probablement pas vendus par les agences via le GDS : le Hajj n'apparaît probablement pas dans nos données. Statut : Déduction.

## 6. Événements par année

### 2019 (année de référence pré-Covid)

- **25 juillet 2019 : décès du président Béji Caïd Essebsi**, suivi d'une élection présidentielle anticipée en septembre-octobre 2019. Effet attendu : faible. Statut : Hypothèse.
- **23 septembre 2019 : faillite du voyagiste Thomas Cook.** Environ 45 hôtels tunisiens touchés et 4 500 touristes britanniques présents en Tunisie au moment de la faillite (sources : Le Brief, Jeune Afrique). Ce choc concerne surtout le tourisme entrant organisé par voyagiste : effet probablement faible sur les réservations des agences tunisiennes. Statut : Hypothèse.
- **Décembre 2019 : grèves des transports en France** contre la réforme des retraites. Effet attendu : perturbations ponctuelles sur les vols vers la France. Statut : Hypothèse.

### 2024 (reprise post-Covid)

- **Jeux Olympiques de Paris (26 juillet au 11 août 2024).** Effet attendu : attraction de voyageurs vers Paris, mais évitement possible par les voyageurs habituels à cause des prix et de l'affluence. Statut : Hypothèse.
- **Inflation et hausse du prix des billets d'avion.** Effet attendu : frein à la demande, surtout pour les voyages de loisirs. Statut : Hypothèse.
- **Tensions au Moyen-Orient et en mer Rouge.** Effet attendu : évitement de certaines destinations. La crise de la mer Rouge touche surtout le transport maritime : l'effet sur l'aérien est probablement indirect. Statut : Hypothèse.

### 2025 (normalisation et contraintes de capacité)

- **Crise opérationnelle de Tunisair.** Flotte opérationnelle tombée à une dizaine d'avions, ponctualité d'environ 48 % en juin 2025, retards pouvant atteindre 24 heures et annulations en pleine haute saison (sources : APA News, Le Courrier de l'Atlas). La situation s'est fortement dégradée à partir du 26 juin 2025 (source : Kapitalis). Un plan de sauvetage a été adopté le 31 janvier 2025 (source : La Presse). Effet attendu : baisse des réservations sur TU et report possible vers d'autres compagnies (par exemple Turkish Airlines, ITA Airways). Statut : Hypothèse, à vérifier en comparant la part de TU dans le total en 2025.
- **Retards de livraison d'avions (Boeing et Airbus).** Effet attendu : capacité limitée sur certaines lignes. Statut : Hypothèse.
- **Juin 2025 : conflit Israël-Iran.** À partir du 13 juin 2025, fermeture des espaces aériens de l'Iran, d'Israël, de l'Irak et de la Jordanie, et suspension de nombreux vols vers le Moyen-Orient (sources : Air Journal, L'Écho touristique). Effet attendu : perturbation des vols vers le Golfe et le Moyen-Orient. Statut : Hypothèse.
- **Vagues de chaleur en Europe du Sud (été 2025).** Effet attendu : report d'une partie des voyages vers le printemps et l'automne. Statut : Hypothèse.

### 2026 (janvier à juillet)

- **Reprise progressive de Tunisair.** Au printemps 2026, le ministre des Transports indiquait 12 avions en exploitation, avec un objectif de 16 en juin (source : Visa Algérie). Effet attendu : stabilisation ou reprise des réservations sur TU. Statut : Hypothèse.
- **Pâques le 5 avril 2026 et Aïd el-Fitr autour du 20 mars 2026**, avec des vacances tunisiennes de printemps du 16 au 29 mars 2026 (voir section 5).
- **Fluctuations du prix du carburant et des taux de change.** Effet attendu : variation du prix des billets, donc de la demande. Statut : Hypothèse.

## 7. Point de vigilance : code AZ

Certaines lignes récentes affichent "Alitalia Societa Aerea Italiana Spa" avec le code AZ. Alitalia a cessé ses activités le 15 octobre 2021. Le code AZ est aujourd'hui utilisé par ITA Airways, son successeur (sources : Wikipédia, IATA). Le libellé vient probablement d'une table de référence non mise à jour. Il faut interpréter AZ comme ITA Airways pour 2024-2026.

## 8. Anomalies observées dans les données

À compléter après analyse : pour chaque pic ou baisse significatif, indiquer la période, le sens, l'ampleur, les agences et compagnies concernées, l'événement associé et le statut (Observé ou Confirmé).

## 9. Sources de référence pour compléter ce document

- IATA (https://www.iata.org/) : rapports sur les capacités aériennes, le coût du carburant et les baisses de trafic liées aux conflits régionaux.
- Copernicus Climate Change Service (https://climate.copernicus.eu/) : historique des vagues de chaleur, tempêtes et anomalies climatiques.
- Sites gouvernementaux et calendriers scolaires officiels : vacances, jours fériés et ponts d'une année sur l'autre.

## Sources citées

- Tekiano, calendrier scolaire tunisien 2018-2019 : https://www.tekiano.com/2018/07/20/tunisie-calendrier-des-vacances-scolaires-et-jours-feries-de-lannee-2018-2019/
- Kapitalis, calendrier scolaire tunisien 2019-2020 : https://kapitalis.com/tunisie/2019/08/09/tunisie-calendrier-des-jours-feries-et-vacances-de-lannee-scolaire-2019-2020/
- Gnet, calendrier scolaire tunisien 2023-2024 : https://news.gnet.tn/tunisie-le-ministere-de-leducation-fixe-le-calendrier-des-vacances-de-lannee-scolaire-2023-2024/
- Tekiano, calendrier scolaire tunisien 2023-2024 : https://www.tekiano.com/2023/09/04/jours-feries-en-tunisie-et-calendrier-des-vacances-scolaires-pour-lannee-2023-2024/
- La Presse de Tunisie, vacances scolaires 2024-2025 : https://www.lapresse.tn/2024/10/25/tunisie-details-des-vacances-scolaires-pour-lannee-2024-2025/
- Tunisie Numérique, rentrée 2024 : https://www.tunisienumerique.com/les-dates-des-vacances-scolaires-et-universitaires-2024-2025/
- Tunisie Numérique, calendrier scolaire 2025-2026 : https://www.tunisienumerique.com/tunisie-rentree-scolaire-2025-2026-le-calendrier-officiel-devoile/
- AllAfrica, vacances scolaires 2025-2026 : https://fr.allafrica.com/stories/202507250266.html
- AllAfrica, rentrée scolaire 2026-2027 : https://fr.allafrica.com/stories/202609010204.html
- L'Écho touristique, calendrier scolaire français 2023-2026 : https://www.lechotouristique.com/article/vacances-scolaires-le-calendrier-2023-2024-enfin-publie
- L'Étudiant, vacances scolaires 2025-2026 : https://www.letudiant.fr/lifestyle/vacances-scolaires-2025-2026-calendrier-dates-et-jours-feries.html
- Onisep, vacances scolaires 2026-2027 : https://www.onisep.fr/vacances-scolaires-2026-2027
- Webdo, saison Omra 2026 : https://www.webdo.tn/fr/actualite/national/omra-2026-la-nouvelle-saison-souvre-avec-un-objectif-de-135-000-pelerins-tunisiens/401158/
- L'Économiste maghrébin, Hajj 2025 : https://www.leconomistemaghrebin.com/2025/05/19/pelerinage-2025-tunisair-assure-44-vols-aller-retour/
- Wikipédia, élection présidentielle tunisienne de 2019 : https://fr.wikipedia.org/wiki/%C3%89lection_pr%C3%A9sidentielle_tunisienne_de_2019
- Le Brief, faillite de Thomas Cook : https://www.lebrief.ma/2751-faillite-de-thomas-cook-impact-economique-sur-la-tunisie-et-le-maroc/
- Jeune Afrique, Thomas Cook en Tunisie : https://www.jeuneafrique.com/833311/economie-entreprises/tourisme-en-tunisie-premiers-incidents-et-inquietude-apres-la-faillite-de-thomas-cook/
- APA News, crise Tunisair : https://fr.apanews.net/news/tunisie-crise-majeure-a-tunisair/
- Le Courrier de l'Atlas, crise Tunisair : https://www.lecourrierdelatlas.com/tunisair-en-crise-retards-turbulence-manageriale-et-chute-boursiere/
- Kapitalis, crise Tunisair juin 2025 : https://kapitalis.com/tunisie/2025/07/02/tunisair-au-bord-du-gouffre-%E2%94%82-trois-jours-de-chaos-retards-monstres-passagers-abandonnes/
- La Presse, plan de sauvetage Tunisair : https://lapresse.tn/2025/10/24/tunisair-prepare-larrivee-de-huit-nouveaux-avions-malgre-les-retards-de-financement/
- Visa Algérie, reprise Tunisair 2026 : https://www.visa-algerie.com/flotte-renforcee-retards-reduitstunisair-commence-a-sortir-la-tete-de-leau/
- Air Journal, fermeture des espaces aériens juin 2025 : https://www.air-journal.fr/2025-06-13-frappes-israeliennes-en-iran-a-nouveau-la-fermeture-de-lespace-aerien-au-moyen-orient-5263387.html
- L'Écho touristique, vols Europe-Moyen-Orient juin 2025 : https://www.lechotouristique.com/article/crise-israel-iran-le-point-sur-les-vols-entre-leurope-et-le-moyen-orient
- Wikipédia, ITA Airways : https://en.wikipedia.org/wiki/ITA_Airways
- IATA, ITA Airways (code AZ) : https://www.iata.org/en/about/members/airline-list/ita-airways/565/
