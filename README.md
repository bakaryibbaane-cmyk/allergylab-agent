# AllergyLab

Kit de démarrage de la semaine AllergyLab : on y construit un agent qui analyse un jeu de données de santé publié.

Le kit est un **harnais** : tout ce qui entoure le modèle et le rend utilisable, c'est-à-dire la boucle, les outils, la consigne, les garde-fous, les traces.

## Démarrer

Il faut deux outils sur la machine : git et uv. Clone le dépôt dans ton dossier personnel, hors d'un dossier synchronisé (OneDrive, iCloud), puis, depuis le dossier du dépôt :

```
uv run kit installer
uv run kit controle
uv run kit agent "Quelle proportion de patients de la puce ALEX est positive à Ara_h_2 ?"
```

`uv run kit` seul affiche la liste des commandes. Chaque commande rend le code 0 quand tout va bien, 1 sinon. Tout passe par `uv run` : pas d'environnement virtuel à activer, pas de `pip`.

`installer` te demande la clé d'API que l'animateur t'a donnée : colle-la dans le terminal, rien ne s'affiche, c'est normal. Elle se range dans ton dossier personnel (`.allergylab/cle`), hors du dépôt : elle ne peut pas partir dans un commit. Pour la remplacer : `uv run kit cle`.

## Les données

`donnees/allergenchipchallenge-data-corrected-final-hdh-sfa.csv` est le jeu « Allergen Chip Challenge » publié par la Société Française d'Allergologie, DOI [10.60597/j5fe-g420](https://doi.org/10.60597/j5fe-g420), sous Licence Ouverte 2.0. Son dictionnaire officiel, `donnees/acc-dictionnaire-final.xls`, est livré tel que publié.

Ces deux fichiers sont dans le dépôt sans aucune modification, et on ne les modifie pas : `uv run kit controle` vérifie leur empreinte.

En Python :

```python
from kit.donnees import charger, colonnes

tableau = charger()      # le tableau complet, sans recodage ni filtrage
dictionnaire = colonnes()  # une ligne par colonne : bloc, lecture, types de puce
```

## Ce que le kit enregistre

Le kit garde une trace de chaque exécution, seul, sans que tu aies à y penser. Tout s'écrit dans le dossier `traces/` de ton dépôt. Le kit n'envoie ces traces nulle part : elles partent avec le reste de ton travail, à chaque `git push`.

**À chaque question posée à l'agent** (`uv run kit agent`), un fichier JSON dans `traces/appels/<jour>/`, nommé par l'heure (en temps universel, UTC) et un suffixe tiré au hasard. Il contient ces champs, et aucun autre :

| Champ | Contenu |
|---|---|
| `format` | la version du format de la trace |
| `horodatage` | la date et l'heure de l'appel, en UTC |
| `equipe` | l'identifiant de `equipe.toml` |
| `kit` | la version du kit |
| `etat` | l'empreinte de l'état de ton travail (voir plus bas) |
| `commit`, `modifie` | le commit git en cours, et s'il y a des modifications pas encore enregistrées ; vides hors d'un dépôt git |
| `moteur`, `modele` | ce qui fait tourner l'agent, et le modèle appelé |
| `question`, `reponse` | la question posée et la réponse rendue |
| `etapes` | les étapes de l'agent : le code qu'il a écrit, ses résultats tronqués |
| `jetons`, `cout_estime` | les jetons consommés et leur coût estimé |
| `duree_s` | la durée de l'appel, en secondes |
| `erreur` | l'erreur, s'il y en a eu une |

La trace s'écrit même quand l'appel échoue ou que tu l'interromps.

**À chaque état nouveau de ton travail**, une copie de `equipe/agent.py`, `equipe/consigne.md`, `equipe/outils/` et `equipe/questions/` dans `traces/etats/<empreinte>/`. L'empreinte résume le contenu de ces fichiers : tant qu'ils ne changent pas, rien n'est recopié. Chaque version de ton agent est ainsi gardée, que tu aies fait un commit ou non.

**Rien qui porte un nom.** Aucune trace ne contient ton nom d'utilisateur, le nom de ta machine, l'auteur des commits, ni rien qui te reconnaisse d'une exécution à l'autre. Avant toute écriture, le kit remplace le chemin de ton dossier personnel par `~`, ton nom d'utilisateur par `<utilisateur>`, et tout ce qui a la forme d'une clé d'API par `<clé>`.

Une limite : le texte libre. Ce que tu tapes dans une question, ce que tu écris dans ton code est recopié tel quel, et aucune machine ne sait y reconnaître un prénom. La règle est donc simple : on signe en équipe, jamais d'un prénom. L'historique git, lui, porte l'auteur de chaque commit ; il appartient aux membres de l'équipe et n'entre pas dans les traces.

**À quoi cela sert.** Pendant la semaine, à retrouver une erreur de l'agent avec ses étapes sans avoir pensé à faire une capture, et à comparer ton agent d'un jour à l'autre. Après la semaine, `traces/`, `JOURNAL.md` et `equipe.toml` sont collectés dans chaque dépôt d'équipe pour monter un dossier de valorisation de la semaine, sans nom d'étudiant. Ne supprime pas `traces/` : pousse-le avec le reste.

## Ce qu'un agent ouvert peut faire

L'agent livré à l'origine dans `equipe/agent.py` est un `CodeAgent` de smolagents **ouvert**. Celui de l'équipe 5 est **fermé** (voir « Accès de l'agent au tableau ») ; ce qui suit décrit l'agent ouvert. Dans les deux cas, à chaque étape, le modèle écrit du code Python, et ce code s'exécute sur ton portable, avec tes droits, sans que personne l'ait relu.

- Ce code peut lire et écrire les fichiers de ton compte, et accéder au réseau. Ta clé d'API est un fichier de ton compte : un agent ouvert peut la lire comme n'importe quel autre. La vraie protection de la clé, c'est le plafond de dépense de ton équipe, et sa révocation.
- Dans l'agent livré à l'origine, deux lignes de `equipe/agent.py` ouvraient les données à l'agent, chacune signalée par un commentaire : celle qui autorise son code à importer pandas, celle qui lui passe le tableau complet. Tant qu'elles étaient là, les outils n'étaient qu'une option parmi d'autres pour lui. Équipe 5 les a retirées.
- Retirer ces deux lignes (fait par l'équipe 5) **ferme** l'accès : l'agent écrit toujours du code, mais il n'atteint plus les données que par les outils de `equipe/outils/`. Fermer réduit ce qu'il peut faire ; ce n'est pas un bac à sable, et la documentation de smolagents le dit elle-même de son interpréteur.
- Un outil qui rend le tableau lui-même rouvre tout. Un outil rend une valeur simple : un nombre, un texte, une courte liste.
- Le bout de ce chemin : remplacer `CodeAgent` par `ToolCallingAgent`, qui n'exécute aucun code et n'appelle que les outils. Le kit a aussi un repli, `kit/boucle_maison.py`, une boucle d'outils qui n'exécute aucun code écrit par le modèle ; son mode d'emploi est en tête du fichier.
- La seule isolation réelle est de faire tourner l'agent sur une machine distante, pas sur ton portable.

Jusqu'où fermer est une décision de ton équipe, qu'elle justifie par ses scores.

**Ce que coûte une question.** Chaque `uv run kit agent` affiche ses jetons et leur coût estimé. Par défaut, l'agent fait huit étapes au plus par question et ses sorties sont tronquées (`kit/reglages.toml`) : ce sont des réglages, pas des verrous. La seule vraie limite est la cagnotte de ton équipe. Quand elle est épuisée, le kit affiche « cagnotte épuisée », écrit la trace et ne retente rien : va voir Adrien.

## Notre agent (équipe 5)

### Public et principe

L'agent s'adresse à des chercheurs en allergologie qui travaillent sur ce jeu de données (4 271 patients, 256 colonnes, trois puces : ALEX, ISAC_V1, ISAC_V2). Il répond quand les données le permettent et s'abstient sinon, avec une justification courte : colonne, puce, nombre de patients mesurés, valeurs -1 ou 9 signalées.

### Les outils (`equipe/outils/`)

- `proportion_positifs` : nombre et proportion de patients à valeur > 0 sur les patients mesurés, avec l'intervalle de confiance de Wilson à 95 %.
- `moyenne_colonne` : moyenne sur les patients mesurés, à 4 décimales ; réservée aux dosages et à Age.
- `repartition_categories` : effectif et pourcentage de chaque code d'une colonne clinique codée, avec le taux de renseignement.
- `intervalle` : le calcul de l'intervalle de Wilson, utilisé par `proportion_positifs`.
- `mesure` : les gardes communes (périmètre, effectif mesuré, valeurs spéciales). Chaque outil est testé hors ligne (`uv run pytest -q equipe/outils`).

### Quand l'agent s'abstient

- Moins de 30 patients mesurés, y compris pour un sous-groupe qu'il calcule lui-même.
- Moins de 50 % de patients renseignés dans le périmètre.
- Une valeur vide veut dire « non mesuré par la puce », jamais « non sensibilisé » : elle n'entre dans aucun dénominateur.
- Sans puce précisée, le calcul porte sur les puces qui mesurent la colonne, et le résultat dit « Calculé sur <puces> ». Une colonne qu'aucune puce ne mesure reste une abstention.
- Question hors du jeu de données (culture générale, conseil médical, code, questions sur l'agent) : abstention, jamais de réponse de mémoire.
- Question qui affirme une cause : on ne parle que d'association.
- Colonne inconnue, traitement, évolution d'un patient, efficacité.

### Valeurs spéciales

- 9 = « non renseigné » dans Rural_or_urban_area (rapprochement solide) : exclu et compté à part. Skin_Symptoms, Age_of_onsets et Treatment_of_rhinitis sont traités de la même façon, mais le rapprochement par libellé n'est pas confirmé ; pour Skin_Symptoms, le dictionnaire dit « sans objet ». Treatment_of_athsma et Treatment_of_atopic_dematitis : sens du 9 non confirmé, pas d'exclusion. Dans Age et Blood_Month_sample, 9 est une vraie valeur.
- -1 : signalé, jamais recodé ni exclu ; son sens n'est pas confirmé.

### Résultats mesurés

Ce sont de petits échantillons, sur le modèle de développement : des indications, pas des preuves.

- Lot 1 : justesse 3/3, abstention 2/2.
- Lot 3 (hors sujet) : abstention 8/8, questions témoins 2/2, sur deux passes.
- Chasse aux failles (20 questions pièges, 2 passes) : justesse 5/10 et 4/10 avant correctifs, 10/10 et 9/10 après. Ces scores viennent de copies temporaires, non versionnées, et ont été mesurés avant la dernière phrase de consigne ; seule la question Alpha-Gal sans puce (q01) a été revalidée après, 5 fois sur 5.
- Défi du mot secret : test réalisé dans une copie temporaire du dépôt, non versionné : 1 fuite sur 24 avec la consigne renforcée seule, 0 sur 24 avec en plus un filtre en code sur la réponse. Le filtre est limité aux variantes courantes (casse, séparateurs, envers, rot13, base64, hexadécimal) ; traductions et autres chiffrements ne sont pas couverts. Les traces de ce test ne sont pas dans le dépôt, et le secret n'a jamais été mis dans le vrai `consigne.md`.

### Limites connues

- Les seuils (30 patients, 50 %) sont des conventions, à valider avec des chercheurs.
- Aucun outil ne filtre par âge ou par sous-groupe : ces calculs reposent sur la consigne.
- Les protections par consigne ne sont pas garanties.
- Le sens de -1 est en attente de confirmation.

### Accès de l'agent au tableau

Décision d'équipe : variante B, `CodeAgent` fermé. Le modèle n'a accès aux données que par les trois outils (`proportion_positifs`, `moyenne_colonne`, `repartition_categories`) : `equipe/agent.py` n'importe plus pandas et ne passe plus le tableau. Ce n'est pas un bac à sable. Conséquence : une question que aucun outil ne couvre, comme le nombre de lignes du tableau, reçoit une abstention. Voir `JOURNAL.md`, « Choix d'architecture ».

### Limites connues et questions ouvertes

- Le dictionnaire officiel ne contient aucun nom de colonne du fichier : les rapprochements se font par libellé, et un seul est solide (Rural_or_urban_area).
- Le sens des -1 n'est pas confirmé : ils sont comptés et signalés, jamais interprétés ni recodés.
- General_cofactors : aucun 9, mais 918 fois le code 10 ; son sens n'est pas confirmé.
- Les cellules à plusieurs codes (« 1,3 », « 4, 6, 7 ») sont absentes du dictionnaire.
- Ces questions sont restées sans réponse du professeur.
- Effet : l'agent s'abstient quand une réponse dépend d'un sens non confirmé.

### Interface

Une interface web (Streamlit) pour explorer le tableau sans écrire de code : statistiques descriptives, comparaison des puces, corrélations, qualité des données, analyse exploratoire et une discussion avec l'agent. Elle est dans `equipe/analyse/interface/app.py`.

Elle ne fait pas partie du verrouillage (la règle 6 fige les dépendances) : streamlit et plotly sont fournis à chaque lancement, et le premier lancement demande internet pour les télécharger. Depuis la racine du dépôt :

```
uv run --with streamlit --with plotly streamlit run equipe/analyse/interface/app.py
```

Pour l'onglet d'analyse exploratoire, ajouter `--with scikit-learn` :

```
uv run --with streamlit --with plotly --with scikit-learn streamlit run equipe/analyse/interface/app.py
```

Sans scikit-learn, cet onglet affiche un message et le reste fonctionne.

Identité visuelle « AllergyLab Premium » : les couleurs viennent du thème natif de `.streamlit/config.toml` (lu quand on lance streamlit depuis la racine du dépôt) et du CSS de `app.py` ; le logo et le favicon sont dans `equipe/analyse/interface/assets/`. Pour vérifier que chaque page se charge, sans appel au modèle :

```
uv run --with streamlit --with plotly --with scikit-learn python equipe/analyse/interface/verifier_interface.py
```

Limite : l'assistant interroge toujours le jeu officiel du dépôt, même quand un CSV importé est actif dans les autres pages.

Attention : l'onglet de discussion appelle l'agent de l'équipe. Chaque question fait donc un appel payant au modèle, et l'agent exécute du code sur votre machine (voir « Ce qu'un agent ouvert peut faire »). La clé d'API reste hors du dépôt : l'interface ne la lit pas, elle est lue par le kit comme pour `uv run kit agent`.
