"""Chargement du fichier de données et de son dictionnaire des colonnes.

charger() rend le tableau tel que le fichier le contient. Il règle la façon
de lire chaque colonne et ne fait rien d'autre : aucun recodage, aucun
filtrage, aucune colonne retirée ou renommée, aucune valeur manquante
comblée. Ce que les valeurs veulent dire reste à la charge de l'équipe.
"""

from pathlib import Path

import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
NOM_FICHIER = "allergenchipchallenge-data-corrected-final-hdh-sfa.csv"
FICHIER = RACINE / "donnees" / NOM_FICHIER
DICTIONNAIRE = RACINE / "kit" / "colonnes.csv"

# Les quinze premières colonnes forment le bloc clinique ; toutes les
# suivantes forment le bloc dosage.
NB_CLINIQUES = 15

# La colonne qui donne le type de puce de chaque patient.
COLONNE_PUCE = "Chip_Type"

# Une virgule, ou une lettre accentuée ou non.
VIRGULE_OU_LETTRE = r",|[^\W\d_]"


def charger(chemin=FICHIER):
    """Rend le tableau complet, une colonne par colonne du fichier.

    Règles de lecture :
    - séparateur « ; », encodage UTF-8 (le BOM éventuel est retiré du nom
      de la première colonne) ;
    - seule une cellule vide devient une valeur manquante ;
    - bloc dosage : nombres, avec la virgule comme séparateur décimal ;
    - bloc clinique : une colonne dont une cellule contient une virgule ou
      une lettre reste en texte, telle quelle ; les autres sont des nombres.
    """
    # Tout est d'abord lu en texte, pour décider ensuite colonne par colonne.
    # keep_default_na=False : un texte comme « NA » reste un texte.
    tableau = pd.read_csv(
        chemin,
        sep=";",
        encoding="utf-8-sig",
        dtype=str,
        keep_default_na=False,
        na_values=[""],
    )
    for position, nom in enumerate(tableau.columns):
        cellules = tableau[nom]
        if position >= NB_CLINIQUES:
            nombres = cellules.str.replace(",", ".", regex=False)
            tableau[nom] = _en_nombres(nombres, nom)
        elif cellules.str.contains(VIRGULE_OU_LETTRE, regex=True, na=False).any():
            pass  # une virgule ou une lettre : la colonne reste en texte
        else:
            tableau[nom] = _en_nombres(cellules, nom)
    return tableau


def lecture(colonne):
    """« nombre » ou « texte », selon la façon dont charger() a lu la colonne."""
    return "nombre" if pd.api.types.is_numeric_dtype(colonne) else "texte"


def colonnes(chemin=DICTIONNAIRE):
    """Rend le dictionnaire des colonnes (kit/colonnes.csv) sous forme de tableau.

    Une ligne par colonne du fichier : colonne, bloc (clinique ou dosage),
    lecture (nombre ou texte), puis une colonne puce_<type> par type de
    puce, vraie si la colonne est renseignée pour au moins un patient de
    cette puce.
    """
    return pd.read_csv(
        chemin,
        encoding="utf-8",
        dtype={"colonne": str, "bloc": str, "lecture": str},
        true_values=["vrai"],
        false_values=["faux"],
    )


def _en_nombres(cellules, nom):
    """Convertit une colonne en nombres, avec un message clair si c'est impossible."""
    try:
        return pd.to_numeric(cellules)
    except ValueError as erreur:
        raise ValueError(
            f"Colonne {nom} : une cellule ne se lit pas comme un nombre ({erreur})."
        ) from None
