"""Outil : décomptes sur l'ensemble des colonnes de dosage, au total et par puce.

Cellules non vides, égales à zéro, négatives, ou patients dont tous les
dosages mesurés sont à zéro. Une cellule vide veut dire « non mesuré » : elle
n'est jamais comptée comme un zéro. Les valeurs -1 sont comptées comme
négatives et signalées, jamais recodées. Rend un texte court, jamais le
tableau. Signé : équipe 5.
"""

import pandas as pd
from smolagents import tool

from equipe.outils import communs
from equipe.outils import mesure as lecture_mesure

MESURES = ("cellules_non_vides", "cellules_egales_zero", "cellules_negatives", "patients_tous_zero")


def _dosages_de_la_puce(puce, table):
    """Le tableau des dosages des patients d'une puce : une colonne par dosage, lue par mesure.py."""
    colonnes = {}
    for colonne in communs.dosages():
        if colonne not in table.columns:
            continue
        valeurs, _, _ = lecture_mesure._lire(colonne, puce)
        colonnes[colonne] = pd.to_numeric(valeurs, errors="coerce")
    return pd.DataFrame(colonnes)


def _compter(cadre, nom):
    """Rend (compte, dénominateur, nombre de -1) d'un tableau de dosages."""
    non_vides = int(cadre.notna().sum().sum())
    moins_un = int((cadre == -1).sum().sum())
    if nom == "cellules_non_vides":
        return non_vides, int(cadre.size), 0
    if nom == "cellules_egales_zero":
        return int((cadre == 0).sum().sum()), non_vides, 0
    if nom == "cellules_negatives":
        return int((cadre < 0).sum().sum()), non_vides, moins_un
    # patients_tous_zero : au moins un dosage mesuré, et tous les mesurés à zéro.
    mesures = cadre.notna().any(axis=1)
    tous_zero = (cadre.fillna(0) == 0).all(axis=1) & mesures
    return int(tous_zero.sum()), int(mesures.sum()), 0


@tool
def agregat_dosages(mesure: str, puce: str | None = None) -> str:
    """Rend un décompte sur toutes les colonnes de dosage, au total et par puce.

    Mesures : « cellules_non_vides », « cellules_egales_zero », « cellules_negatives »
    (les -1 en font partie, signalés à part) ou « patients_tous_zero » (patients
    ayant au moins un dosage mesuré, tous les dosages mesurés étant à zéro). Une
    cellule vide veut dire « non mesuré », jamais zéro. Sans puce, le détail par
    puce est rendu. Si les données ne permettent pas de conclure, le texte rendu
    commence par « abstention » : reprends alors cette raison.

    Args:
        mesure: l'une des quatre mesures ci-dessus.
        puce: type de puce (Chip_Type) à étudier ; None pour toutes les puces, avec le détail par puce.
    """
    if mesure not in MESURES:
        return f"abstention : la mesure doit être l'une de : {', '.join(MESURES)}."
    toutes = communs.puces()
    if puce is not None and puce not in toutes:
        return f"abstention : la puce {puce!r} est inconnue (puces : {', '.join(toutes)})."

    with communs.table_en_memoire() as table:
        par_puce = {nom: _dosages_de_la_puce(nom, table) for nom in toutes if puce in (None, nom)}
    resultats = {nom: _compter(cadre, mesure) for nom, cadre in par_puce.items()}
    total = sum(r[0] for r in resultats.values())
    denominateur = sum(r[1] for r in resultats.values())
    moins_un = sum(r[2] for r in resultats.values())

    if mesure == "patients_tous_zero":
        sujet, unite = "patients dont tous les dosages mesurés sont à zéro", "patients ayant au moins un dosage mesuré"
    else:
        sujet = {"cellules_non_vides": "cellules de dosage non vides", "cellules_egales_zero": "cellules de dosage égales à zéro",
                 "cellules_negatives": "cellules de dosage strictement négatives"}[mesure]
        unite = "cellules de dosage" if mesure == "cellules_non_vides" else "cellules non vides"
    cadre_texte = f"la puce {puce}" if puce else "toutes les puces"
    if mesure == "cellules_non_vides":
        # Un pourcentage de cellules non vides n'a pas de sens : un vide veut dire « non mesuré ».
        texte = (
            f"{communs.entier(total)} {sujet} sur {communs.entier(denominateur)} {unite} du tableau, {cadre_texte} ; "
            "les cellules vides sont non mesurées, jamais comptées comme zéro."
        )
    else:
        texte = (
            f"{communs.entier(total)} {sujet} sur {communs.entier(denominateur)} {unite} "
            f"({communs.fr(100 * total / denominateur, 2) if denominateur else '0'} %), {cadre_texte}, "
            "cellules vides jamais comptées comme zéro."
        )
    if puce is None:
        detail = " ; ".join(f"{nom} : {communs.entier(r[0])} sur {communs.entier(r[1])}" for nom, r in resultats.items())
        texte += f"\nPar puce : {detail}."
    if mesure == "cellules_negatives" and moins_un:
        texte += (
            f"\nDont {communs.entier(moins_un)} valeurs -1 : comptées comme négatives, "
            "leur sens n'est pas confirmé, elles n'ont pas été recodées."
        )
    return texte
