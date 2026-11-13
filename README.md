# AllergyLab

Kit de démarrage de la semaine AllergyLab : on y construit un agent qui analyse un jeu de données de santé publié.

Le kit est un **harnais** : tout ce qui entoure le modèle et le rend utilisable, c'est-à-dire la boucle, les outils, la consigne, les garde-fous, les traces.

## Démarrer

Il faut deux outils sur la machine : git et uv. Clone le dépôt dans ton dossier personnel, hors d'un dossier synchronisé (OneDrive, iCloud), puis, depuis le dossier du dépôt :

```
uv run kit installer
uv run kit controle
uv run kit agent "Combien de lignes compte le tableau ?"
```

`uv run kit` seul affiche la liste des commandes. Chaque commande rend le code 0 quand tout va bien, 1 sinon. Tout passe par `uv run` : pas d'environnement virtuel à activer, pas de `pip`.

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
