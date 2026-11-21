"""Outil : dit quelles puces mesurent une colonne (kit/colonnes.csv).

Pourquoi un outil : une colonne de dosage vide pour une puce ne veut pas dire « donnée
manquante », mais « molécule non mesurée par cette puce ». Avant de calculer sur une
molécule et une puce, l'agent doit savoir si la puce la mesure. Sinon il s'abstient.
"""

from smolagents import tool

from kit.donnees import colonnes


@tool
def puces_qui_mesurent(colonne: str) -> str:
    """Dit quelles puces (ALEX, ISAC_V1, ISAC_V2) mesurent une colonne du tableau.

    Args:
        colonne: le nom exact de la colonne, par exemple "Che_a".
    """
    dico = colonnes().set_index("colonne")
    if colonne not in dico.index:
        return f"{colonne} : colonne absente du tableau"
    ligne = dico.loc[colonne]
    puces = [c for c in dico.columns if c.startswith("puce_")]
    oui = [c[len("puce_"):] for c in puces if ligne[c]]
    non = [c[len("puce_"):] for c in puces if not ligne[c]]
    texte = f"{colonne} ({ligne['bloc']}) : mesurée par {', '.join(oui) or 'aucune puce'}"
    if non:
        texte += f" ; non mesurée par {', '.join(non)}"
    return texte
