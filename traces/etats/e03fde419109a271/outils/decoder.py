"""Outil : dit ce que veut dire un code du dictionnaire officiel pour une colonne clinique.

Pourquoi un outil : le modèle ne doit jamais deviner le sens d'un code (1 = rural ou
urbain ?). La table ci-dessous vient du dictionnaire officiel. Le 9 n'est solide que pour
Rural_or_urban_area (« non renseigné » au dictionnaire) ; le 9 des autres colonnes cliniques
et le code 10 de General_cofactors restent non confirmés : l'outil le dit, il ne les interprète pas.
Un code absent de la table (le -1 par exemple) est signalé comme « non documenté » : l'agent
doit alors s'abstenir, pas inventer.

Les colonnes de traitement et de cofacteurs peuvent contenir plusieurs codes à la fois
(par exemple "1,3" ou "2, 3") : l'outil les sépare et décode chacun.
"""

import math

from smolagents import tool

# colonne du tableau -> {code: sens}. Rapprochements colonne/fiche par libellé.
NON_CONFIRME = "sens non confirmé (rapprochement colonne/dictionnaire par libellé)"
CODES = {
    "Gender": {"1": "masculin", "0": "féminin"},
    "Rural_or_urban_area": {"9": "non renseigné (dictionnaire)", "0": "rural", "1": "urbain"},
    "Treatment_of_atopic_dematitis": {
        "9": NON_CONFIRME,
        "0": "pas de traitement",
        "1": "émollients",
        "2": "dermocorticoïdes",
        "3": "Protopic",
        "4": "ciclosporine voie générale",
        "5": "dupilumab",
        "6": "upadacitinib",
        "7": "baricitinib",
    },
    "General_cofactors": {
        "9": NON_CONFIRME,
        "0": "aucun cofacteur connu",
        "1": "effort / activité sportive",
        "2": "AINS",
        "3": "alcool",
        "4": "moisissures (maison insalubre)",
        "5": "acariens (ancienne literie ou drap non changé)",
        "6": "animaux de compagnie : chat",
        "7": "animaux de compagnie : chien",
        "8": "animaux de compagnie : cheval",
        "10": NON_CONFIRME,
        "11": "mucoviscidose",
        "12": "IPP",
    },
    "Age_of_onsets": {
        "9": NON_CONFIRME,
        "0": "pas d'AA",
        "1": "avant 6 mois",
        "2": "entre 6 mois et 2 ans",
        "3": "entre 2 et 3 ans",
        "4": "entre 3 et 10 ans",
        "5": "entre 10 et 20 ans",
        "6": "après 20 ans",
    },
}


def sens(colonne, code):
    """Le sens d'un code, ou 'non documenté' si la table ne le connaît pas."""
    table = CODES.get(colonne)
    if table is None:
        return "colonne non documentée dans cet outil"
    texte = str(code).strip()
    if texte.endswith(".0"):  # un code lu comme nombre : 1.0 devient 1
        texte = texte[:-2]
    return table.get(texte, f"code {texte} non documenté")


@tool
def decoder(colonne: str, valeur: str) -> str:
    """Donne le sens d'un code du dictionnaire officiel pour une colonne clinique du tableau.

    Args:
        colonne: le nom exact de la colonne, par exemple "Rural_or_urban_area".
        valeur: le code à décoder, par exemple "0", ou plusieurs codes séparés par des virgules, par exemple "1,3".
    """
    if valeur is None:
        return "valeur manquante"

    try:
        if math.isnan(valeur):
            return "valeur manquante"
    except (TypeError, ValueError, OverflowError):
        pass

    morceaux = [m for m in str(valeur).split(",") if m.strip()]
    if not morceaux:
        return "valeur vide"
    return " ; ".join(
        f"{m.strip()[:-2] if m.strip().endswith('.0') else m.strip()} = {sens(colonne, m)}"
        for m in morceaux
    )
