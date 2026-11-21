"""Outil : moyenne d'une colonne numérique sur les patients mesurés.

Pour les colonnes de dosage et Age, même garde que proportion.py. Les vides ne comptent pas : ils veulent dire
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
    # Une colonne clinique est un code : sa moyenne n'a pas de sens. Seule Age,
    # une vraie mesure en années, fait exception.
    if mesure.est_clinique(colonne) and colonne != "Age":
        return "abstention : colonne clinique codée, une moyenne de codes n'a pas de sens ; utiliser repartition_categories"

    garde = mesure.verifier_perimetre(colonne, puce)
    if isinstance(garde, str):
        return garde

    valeurs, _, _ = mesure._lire(colonne, puce)
    nombres = pd.to_numeric(valeurs.dropna(), errors="coerce")
    if nombres.isna().any():
        return f"abstention : la colonne {colonne!r} contient des valeurs non numériques, une moyenne n'a pas de sens."

    # Colonnes de dosage seulement : 9 y est une vraie valeur, pas signalée.
    # -1 : sens non confirmé, signalé mais laissé dans la moyenne.
    moins_un = mesure.valeurs_speciales(colonne, puce)[0]
    perimetre = "tout le fichier" if puce is None else f"la puce {puce}"
    texte = f"Moyenne de {colonne!r} ({perimetre}) : {nombres.mean():.4g} sur {garde} patients mesurés."
    if moins_un:
        texte += (
            f" Attention : {moins_un} valeurs -1 sont comptées dans cette moyenne, "
            "leur sens n'est pas confirmé, elles n'ont pas été recodées."
        )
    return texte
