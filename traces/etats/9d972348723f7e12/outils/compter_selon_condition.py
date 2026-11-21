"""Outil : nombre de patients mesurés dont une colonne numérique vérifie une condition.

Le dénominateur est toujours l'effectif mesuré (colonne renseignée) : un vide
veut dire « non mesuré », jamais zéro. Les valeurs -1 sont comptées et
signalées, jamais recodées. L'outil compare des nombres, il n'interprète
aucun code. Rend un texte court, jamais le tableau. Signé : équipe 5.
"""

import pandas as pd
from smolagents import tool

from equipe.outils import communs, mesure


@tool
def compter_selon_condition(colonne: str, operateur: str, valeur: float, puce: str | None = None) -> str:
    """Rend le nombre de patients mesurés dont une colonne numérique vérifie une condition.

    Colonnes permises : une colonne de dosage, Age, Blood_Month_sample ou
    Sensitization. Le dénominateur est le nombre de patients mesurés. Si les
    données ne permettent pas de conclure, le texte rendu commence par
    « abstention » : reprends alors cette raison. Le sens d'un code vient de
    l'outil decoder, jamais de celui-ci.

    Args:
        colonne: nom exact de la colonne, par exemple « Age ».
        operateur: l'un de ==, !=, <, <=, > ou >= (> est strict, >= ne l'est pas).
        valeur: le nombre auquel on compare, par exemple 18.
        puce: type de puce (Chip_Type) à étudier ; None pour les puces qui mesurent la colonne.
    """
    operateur = operateur.strip()
    if operateur not in communs.OPERATEURS:
        return f"abstention : l'opérateur {operateur!r} n'existe pas (permis : {', '.join(communs.OPERATEURS)})."
    comparer, en_mots = communs.OPERATEURS[operateur]

    # Seules les vraies mesures se comparent à un seuil : les autres colonnes
    # cliniques sont des codes, dont l'ordre ne veut rien dire.
    if colonne not in communs.COLONNES_CLINIQUES_NUMERIQUES and colonne not in communs.dosages():
        if mesure.est_clinique(colonne):
            return (
                f"abstention : {colonne!r} est une colonne clinique codée, une comparaison à un seuil n'a pas de sens ; "
                "utiliser compter_par_code ou repartition_categories."
            )
        return f"abstention : la colonne {colonne!r} n'existe pas dans le fichier ou n'est pas numérique."

    with communs.table_en_memoire():
        garde = mesure.verifier_perimetre(colonne, puce)
        if isinstance(garde, str):
            return garde
        valeurs, _, _ = mesure._lire(colonne, puce)
        nombres = pd.to_numeric(valeurs.dropna(), errors="coerce")
        if nombres.isna().any():
            return f"abstention : la colonne {colonne!r} contient des valeurs non numériques."
        moins_un = mesure.valeurs_speciales(colonne, puce)[0]
        cadre = mesure.perimetre(colonne, puce)
        prefixe = mesure.prefixe(colonne, puce)

    retenus = int(comparer(nombres, valeur).sum())
    texte = (
        f"{prefixe}{communs.entier(retenus)} patients sur {communs.entier(garde)} mesurés "
        f"({communs.fr(100 * retenus / garde)} %) ont {colonne!r} {en_mots} {communs.valeur_texte(valeur)} "
        f"({operateur}) ; dénominateur = patients mesurés ({cadre}), cellules vides exclues."
    )
    if moins_un:
        texte += (
            f" Attention : {moins_un} valeurs -1 sont dans ces patients mesurés, comparées comme le nombre -1 ; "
            "leur sens n'est pas confirmé, elles n'ont pas été recodées."
        )
    return texte
