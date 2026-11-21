"""Petites fonctions partagées par les outils de comptage (pas un outil).

Elles ne portent aucune logique de mesure : celle-ci reste dans mesure.py.
Signé : équipe 5.
"""

import operator
from contextlib import contextmanager

from equipe.outils import mesure

# Les six comparaisons permises, avec leur nom en mots pour les sorties.
OPERATEURS = {
    "==": (operator.eq, "égal à"),
    "!=": (operator.ne, "différent de"),
    "<": (operator.lt, "strictement inférieur à"),
    "<=": (operator.le, "inférieur ou égal à"),
    ">": (operator.gt, "strictement supérieur à"),
    ">=": (operator.ge, "supérieur ou égal à"),
}

# Colonnes cliniques lues comme de vraies mesures ou des rangs ordonnés. Les
# autres colonnes cliniques sont des codes : on les compte avec compter_par_code.
COLONNES_CLINIQUES_NUMERIQUES = ("Age", "Blood_Month_sample", "Sensitization")


def fr(nombre, decimales=1):
    """Un nombre à la française : 3,7."""
    return f"{nombre:.{decimales}f}".replace(".", ",")


def entier(nombre):
    """Un entier avec une espace entre les milliers : 3 132."""
    return f"{nombre:,}".replace(",", " ")


def valeur_texte(valeur):
    """Un seuil sans zéro inutile, à la française : 0,35 ; 18."""
    return f"{valeur:g}".replace(".", ",")


def dosages():
    """Les colonnes du bloc dosage, d'après kit/colonnes.csv."""
    dictionnaire = mesure.donnees.colonnes()
    return dictionnaire.loc[dictionnaire["bloc"] == "dosage", "colonne"].tolist()


def puces():
    """Les types de puce connus, d'après kit/colonnes.csv."""
    return [nom[len("puce_"):] for nom in mesure.donnees.colonnes().columns if nom.startswith("puce_")]


@contextmanager
def table_en_memoire():
    """Le temps du bloc with, le fichier n'est lu qu'une fois.

    mesure.py relit le CSV à chaque appel (0,5 s). Les outils qui passent en
    revue plusieurs colonnes lisent donc le tableau une fois et le rendent
    à chaque appel de mesure.py, qui garde sa logique.
    """
    lecture = mesure.donnees.charger
    table = lecture()
    mesure.donnees.charger = lambda *args, **kwargs: table
    try:
        yield table
    finally:
        mesure.donnees.charger = lecture
