# Journal de bord

## Lundi 16 novembre

Pas de commit ce jour. Équipe 5.

## Mardi 17 novembre

Premier lot de questions de contrôle, consigne avec trois outils et mesure de départ de l'agent d'origine sur le lot 1, ajout de `uv run kit pousser` et passage à la version 3 de la spec, traces des appels à l'agent. Équipe 5.

## Mercredi 18 novembre

Outils proportion_positifs, moyenne_colonne, repartition_categories, qualite_donnees et mesure.py (périmètre par puce, seuil de 30), intervalle de Wilson, 9 traité comme non renseigné dans quatre colonnes, consigne réécrite, lots 1 à 3 de questions et mise à jour du kit avec le harnais d'évaluation. Équipe 5.

## Jeudi 19 novembre

Outil compter_patients, reprise de qualite_donnees, puces_qui_mesurent, repartition_colonne, phase2 et relire_lot, accès de l'agent fermé aux données (variante B), choix d'architecture documenté, consigne mise à jour, limites connues du 9 consignées. Équipe 5.

## Vendredi 20 novembre

## Demandes de rallonge

## Notes de méthode (équipe 5)

- Vide = non mesuré par la puce, jamais « non sensibilisé » : le dénominateur est l'effectif mesuré.
- Seuil minimal de 30 patients mesurés, sinon l'agent s'abstient (convention à confirmer).
- 9 traité comme non renseigné dans 4 colonnes cliniques : Rural_or_urban_area (rapprochement solide) ; Skin_Symptoms, Age_of_onsets, Treatment_of_rhinitis (rapprochement par libellé non confirmé ; pour Skin_Symptoms, le dictionnaire dit « sans objet »). 9 est une vraie valeur dans Age et Blood_Month_sample ; -1 : signalé, jamais recodé ni exclu. Équipe 5.
- Seuil de 50 % gardé pour les dosages ; colonnes cliniques codées via repartition_categories (seuil 30, taux de renseignement affiché). Équipe 5.
- Puce non précisée : périmètre des puces qui mesurent la colonne ; moyenne à 4 décimales ; consigne renforcée (sous-groupes, -1, fuite). Équipe 5.
- Limites ouvertes, sans réponse du professeur : le dictionnaire n'a aucun nom de colonne du fichier (rapprochements par libellé, un seul solide) ; sens des -1 non confirmé ; General_cofactors sans 9 mais avec 918 codes 10, sens non confirmé.
- Les cellules à plusieurs codes (« 1,3 », « 4, 6, 7 ») sont absentes du dictionnaire.
- Effet : l'agent s'abstient quand la réponse dépend d'un sens non confirmé. Équipe 5.

## Choix d'architecture

- Trois variantes testées sur les lots 1 à 3 (21 questions, 2 passes, Haiku 5.5, 0,16 $ au total) : A, CodeAgent ouvert ; B, CodeAgent fermé ; C, BoucleMaison.
- Justesse : A 14/14, B 13/14, C 0/14. Abstention correcte : A 28/28, B 28/28, C 2/28. Coût : A 0,0897 $, B 0,0445 $, C 0,0258 $.
- C écartée : le schéma final_answer du kit n'est pas rempli correctement par Haiku (nombres en chaîne, 'None', arguments vides). C'est un défaut du kit, pas un jugement sur l'architecture.
- B retenue : un seul échec, la question sur le nombre de lignes du tableau, qu'aucun outil ne fournit ; l'agent s'abstient. Avantage : il ne peut plus contourner le seuil de 30, le périmètre par puce ni les -1.
- Limites : petits échantillons ; failles.toml perdu (fuite de consigne et injection presque pas testées) ; B instable entre deux passes sur cette question. Équipe 5.

## Reprise du travail du binôme

- Repris tels quels : repartition_colonne (non branché, docstring à l'appui) et ses tests (test_puces_et_repartition).
- Repris et adaptés : qualite_donnees. L'import de COLONNES_CODE_9 est remplacé par COLONNES_9_NON_RENSEIGNE de mesure.py. Les -1 et les 9 des dosages sont comptés et signalés, jamais exclus. Seuls les 9 de la liste de mesure.py sont exclus, avec la formulation « traité comme non renseigné (sens non confirmé) », sauf Rural_or_urban_area (dictionnaire). Tests adaptés.
- Branchés dans agent.py, avec deux lignes dans la partie « outils » de la consigne : puces_qui_mesurent et qualite_donnees. Rejeu des lots 1 à 3 (21 questions, 1 passe, Haiku 5.5, 0,026 $) : justesse 7/7, abstention correcte 14/14, aucune réponse dangereuse, aucune régression, une erreur de format du modèle récupérée à l'étape suivante. Aucun outil débranché.
- Repris et adaptés : decoder et ses tests. La table vient du dictionnaire ; le 9 de Treatment_of_atopic_dematitis, de General_cofactors et d'Age_of_onsets, et le code 10 de General_cofactors répondent « sens non confirmé (rapprochement colonne/dictionnaire par libellé) » ; Rural_or_urban_area garde « non renseigné (dictionnaire) » ; le -1 reste « non documenté ». Branché dans agent.py, avec une ligne dans la partie « outils » de la consigne. Rejeu des lots 1 à 3 (21 questions, 1 passe, Haiku 5.5, 0,027 $) : justesse 7/7, abstention correcte 14/14, aucune réponse dangereuse, aucune régression par rapport au rejeu précédent.
- Écartée : BoucleMaison (voir « Choix d'architecture » : le schéma final_answer du kit n'est pas rempli correctement par Haiku). Le kit du binôme est aussi d'une version plus ancienne : rien de kit/ n'a été copié.
- Les versions du binôme qui excluaient les -1 et les 9 des dosages n'ont pas été reprises : règle de l'équipe, les -1 sont comptés et signalés, jamais exclus ni recodés. Équipe 5.
- Repris sans dépendance installée : l'interface (equipe/analyse/interface/) et ml_exploratoire.py (equipe/analyse/), non branchés sur l'agent, absents des tests. Seul changement à l'interface : la racine du dépôt, recalculée pour le nouveau dossier. Équipe 5.

## Dépendances

- streamlit, plotly et scikit-learn ne sont pas dans le verrouillage : kit/tests/test_environnement.py exige des dépendances figées (règle 6). Un essai d'`uv add` a été annulé, pyproject.toml et uv.lock sont restés tels quels.
- L'interface (equipe/analyse/interface/) se lance par `uv run --with streamlit --with plotly streamlit run equipe/analyse/interface/app.py`, avec `--with scikit-learn` en plus pour l'analyse exploratoire (ml_exploratoire.py, importé seulement à l'usage). Voir le README.
- Le professeur a donné un accord oral pour l'interface (date et forme à préciser). Équipe 5.

## Essai de précision de la consigne (jour 19)

- Trois défauts de justification constatés, aucun ne rendait une réponse fausse : une réserve de l'outil decoder attribuée au « dictionnaire officiel », un nom de colonne cité qui ne figure pas dans la sortie de compter_patients, une valeur écrite avec une virgule décimale qui a coûté une erreur de syntaxe et un tour de plus. Équipe 5.
- Essai : trois règles ajoutées à la consigne (attribution à l'outil, rien de plus que les outils, point décimal). Rejeu des lots 1 à 3 (21 questions, 1 passe, Haiku 5.5) : justesse 7/7, abstention 14/14, aucune réponse dangereuse, mais 2 erreurs de format du modèle contre 1 au rejeu précédent ; les 9 exécutions ciblées (3 par défaut) n'ont montré ni phrase « dictionnaire officiel », ni Chip_Type, ni virgule dans la valeur, mais encore de petits détails absents des outils et des virgules dans le texte des justifications. Règle de décision de l'équipe : erreurs en hausse, donc consigne restaurée, changement non conservé. Équipe 5.
- Limite : une seule passe et 3 exécutions par question ; la hausse de 1 à 2 erreurs peut n'être que du bruit, et l'absence de défaut sur 3 exécutions montre seulement qu'il est moins probable, pas qu'il a disparu. Un rejeu à plusieurs passes reste à faire avant de retenter ces règles. Équipe 5.

## Refonte visuelle de l'interface (jour 20)

- Nouvelle identité (nuit, pétrole, turquoise, blanc cassé pour la lecture ; logo « puce » à la place de l'ancien pictogramme) dans equipe/analyse/interface/ et .streamlit/config.toml. Aucun outil, aucune consigne, aucun fichier de kit/ ou de donnees/ modifié ; aucun appel au modèle. L'ancien app.py reste dans l'historique git.
- Défauts corrigés dans l'interface : les boutons d'accès rapide de l'accueil ne changeaient pas de page ; les messages du chat et les erreurs étaient insérés sans protection HTML ; les pastilles « types de puces » et « Connecté » étaient écrites en dur ; l'import de CSV s'affichait au-dessus de toutes les pages (il a maintenant sa page).
- Vérification : equipe/analyse/interface/verifier_interface.py (onze pages, accès rapide, quatre analyses guidées). Le rendu visuel n'a pas été regardé dans un navigateur. Équipe 5.

## Outils génériques pour les capacités manquantes (jour 20)

- Cinq outils ajoutés et branchés, un commit chacun : compter_selon_condition, compter_par_code, classer_allergenes, agregat_dosages, proportion_avec_filtre (un module commun, communs.py, et un test par outil, sur la table inventée). Chacun a été comparé sans modèle à un calcul indépendant en pandas sur le vrai fichier : concordance sur toutes les lectures vérifiées. Équipe 5.
- Rejeu des lots 1 à 3 (21 exécutions, 1 passe, Haiku 5.5) : justesse 7/7, abstention 14/14, aucune réponse dangereuse, aucun outil retiré. Essai ciblé sur 18 énoncés du banc (18 exécutions, une par énoncé) : 14 réponses conformes à nos références, 4 abstentions, aucune réponse fausse ; coût total des 39 exécutions : environ 0,08 $. Limites : une passe, petits échantillons, le banc n'a pas été passé en évaluation officielle. Équipe 5.
- Manques restants : un critère qui croise plusieurs colonnes patient par patient (sensibilisation et dosages, dosages et traitement) n'a pas d'outil ; sur la rhinite, l'agent s'arrête à la réserve « non documenté » de decoder et n'appelle pas compter_par_code, ce qui découle de la règle d'abstention actuelle, non modifiée. Équipe 5.

## Deux outils de croisement et une règle sur les codes (jour 20)

- Ajoutés et branchés : croiser_colonnes (valeurs d'une colonne clinique associées à plusieurs valeurs d'une autre) et patients_selon_dosages (aucun ou au moins un dosage au-dessus d'un seuil, avec filtre facultatif sur les codes d'une colonne clinique), un test chacun sur la table inventée, une ligne de consigne chacun ; plus une ligne de consigne : un code dont l'énoncé donne lui-même le sens est utilisé tel quel. L'exception correspondante dans « Quand s'abstenir » a été essayée puis retirée après le rejeu des lots. Équipe 5.
- Rejeu des lots 1 à 3 (une passe, Haiku 5.5, un échantillon par état) : avec l'exception, justesse 7/7 mais abstention 13/14 (une réponse inventée au lot 2) ; sans elle, le lot 2 rejoué donne abstention 4/4 et une erreur API 500, juste à la relance. Une seule exécution par état : la cause n'est pas démontrée. Passe de 35 énoncés du banc via kit agent (37 exécutions dont 2 relances sur erreur 500, une passe) : 19 justes, 1 fausse (écart d'un dixième), 15 abstentions fondées, aucune abstention à tort, aucune réponse sur piège, aucune régression par rapport à la passe précédente ; petits échantillons, à ne pas généraliser. Équipe 5.
- Manques restants : un filtre « tout code sauf un » oblige à énumérer les codes, et un code oublié décale le résultat ; la règle d'abstention sur un 9 de sens non confirmé peut encore s'opposer à la règle sur les codes donnés par l'énoncé ; le rejeu des lots 1 et 3 n'a pas été refait après le retrait de l'exception. Équipe 5.
