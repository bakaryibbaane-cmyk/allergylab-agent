"""Outil : moyenne d'une colonne numérique sur les patients mesurés.

Même garde que proportion.py. Les vides ne comptent pas : ils veulent dire
« non mesuré », ce ne sont pas des zéros. Rend un texte court, jamais le
tableau. Signé : équipe 5.
"""

import pandas as pd
from smolagents import tool

from equipe.outils import mesure


@tool
def moyenne_colonne(colonne: str, puce: str | None = None) -> str:
    """Rend la moyenne d'une colonne sur les patients mesurés, avec l'effectif.

    Si les données ne permettent pas de conclure, le texte rendu commence par
    « abstention » : reprends alors cette raison dans ta réponse.

    Args:
        colonne: nom exact de la colonne numérique, par exemple « Act_d_1 ».
        puce: type de puce (Chip_Type) à étudier ; None pour tout le fichier.
    """
    garde = mesure.verifier_perimetre(colonne, puce)
    if isinstance(garde, str):
        return garde

    valeurs, _, _ = mesure._lire(colonne, puce)
    nombres = pd.to_numeric(valeurs.dropna(), errors="coerce")
    if nombres.isna().any():
        return f"abstention : la colonne {colonne!r} contient des valeurs non numériques, une moyenne n'a pas de sens."

    # -1 et 9 : sens non confirmé, donc signalés mais laissés dans la moyenne.
    # Si l'un d'eux code « non disponible », la moyenne en est faussée : le dire.
    moins_un, neuf = mesure.valeurs_speciales(colonne, puce)
    perimetre = "tout le fichier" if puce is None else f"la puce {puce}"
    texte = f"Moyenne de {colonne!r} ({perimetre}) : {nombres.mean():.4g} sur {garde} patients mesurés."
    if moins_un or neuf:
        texte += (
            f" Attention : {moins_un} valeurs -1 et {neuf} valeurs 9 sont comptées dans cette moyenne, "
            "leur sens n'est pas confirmé, elles n'ont pas été recodées."
        )
    return texte
