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
