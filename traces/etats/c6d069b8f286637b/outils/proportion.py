"""Outil : proportion de patients positifs (valeur > 0) pour une colonne de dosage.

Le dénominateur est toujours l'effectif mesuré (patients dont la colonne est
renseignée), jamais les 4 271 lignes : un vide veut dire « non mesuré par la
puce », pas « non sensibilisé ». Rend un texte court, jamais le tableau.
Signé : équipe 5.
"""

import pandas as pd
from smolagents import tool

from equipe.outils import intervalle, mesure


def _fr(nombre):
    """Un pourcentage à une décimale, à la française : 3,7."""
    return f"{nombre:.1f}".replace(".", ",")


def _entier(nombre):
    """Un entier avec une espace entre les milliers : 3 132."""
    return f"{nombre:,}".replace(",", " ")


@tool
def proportion_positifs(colonne: str, puce: str | None = None) -> str:
    """Rend le nombre et la proportion de patients positifs (valeur > 0) pour une colonne.

    Le calcul ne porte que sur les patients mesurés. Si les données ne
    permettent pas de conclure, le texte rendu commence par « abstention » :
    reprends alors cette raison dans ta réponse, sans calculer toi-même.

    Args:
        colonne: nom exact de la colonne, par exemple « Act_d_1 ».
        puce: type de puce (Chip_Type) à étudier ; None pour tout le fichier.
    """
    # Une colonne clinique est un code (0 = rural, 1 = urbain...) : « positif »
    # n'y a pas de sens. Seules les colonnes de dosage ont un seuil à 0.
    if mesure.est_clinique(colonne):
        return (
            "abstention : colonne clinique codée, « positif » n'a pas de sens ; "
            "une répartition par catégorie serait nécessaire."
        )

    # La garde ensuite : colonne inconnue, non mesurée, effectif trop faible.
    garde = mesure.verifier_perimetre(colonne, puce)
    if isinstance(garde, str):
        return garde

    valeurs, _, _ = mesure._lire(colonne, puce)
    mesures = valeurs.dropna()
    nombres = pd.to_numeric(mesures, errors="coerce")
    if nombres.isna().any():
        return f"abstention : la colonne {colonne!r} contient des valeurs non numériques, une proportion de positifs n'a pas de sens."

    # -1 : son sens n'est pas confirmé (absent du dictionnaire officiel). On le
    # signale, on ne le recode pas et on ne l'exclut pas. Les 9 n'ont pas à
    # être signalés ici : une colonne de dosage n'est pas dans la liste des
    # colonnes où 9 = non renseigné, c'est une vraie valeur.
    moins_un = mesure.valeurs_speciales(colonne, puce)[0]
    positifs = int((nombres > 0).sum())
    perimetre = "tout le fichier" if puce is None else f"la puce {puce}"
    # Un petit effectif n'est pas une certitude : on rend toujours l'intervalle.
    basse, haute = intervalle.intervalle_wilson(positifs, garde)
    texte = (
        f"{_fr(100 * positifs / garde)} % (IC 95 % : {_fr(basse)} à {_fr(haute)}), "
        f"{_entier(positifs)} positifs sur {_entier(garde)} mesurés "
        f"pour {colonne!r} ({perimetre}), positif = valeur > 0."
    )
    if moins_un:
        texte += (
            f" Attention : {moins_un} valeurs -1 sont dans ces patients mesurés, "
            "leur sens n'est pas confirmé, elles n'ont pas été recodées."
        )
    return texte
