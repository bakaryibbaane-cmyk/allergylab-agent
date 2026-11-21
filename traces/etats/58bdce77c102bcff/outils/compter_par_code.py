"""Outil : nombre de patients dont la cellule d'une colonne clinique codée contient un code.

Une cellule peut porter plusieurs codes (« 1, 3 » ou « 1,3 ») : on la lit code
par code, séparateurs virgule ou espace, et le code « 1 » ne compte pas
dans « 10 ». L'outil ne dit jamais ce qu'un code veut dire : le sens vient
de decoder. Le dénominateur est le nombre de patients renseignés. Rend un
texte court, jamais le tableau. Signé : équipe 5.
"""

import re

from smolagents import tool

from equipe.outils import communs, mesure

SEPARATEURS = r"[,\s]+"


def _jetons(cellule):
    """Les codes d'une cellule, en texte : « 1, 3 » donne [« 1 », « 3 »], 1.0 donne [« 1 »]."""
    if not isinstance(cellule, str):
        nombre = float(cellule)
        cellule = str(int(nombre)) if nombre.is_integer() else str(nombre)
    return [jeton for jeton in re.split(SEPARATEURS, cellule.strip()) if jeton]


@tool
def compter_par_code(colonne: str, codes: str, puce: str | None = None) -> str:
    """Rend le nombre de patients dont la cellule d'une colonne clinique codée contient au moins un des codes demandés.

    La cellule peut porter plusieurs codes ; le code compte qu'il soit seul
    ou associé à d'autres. Le dénominateur est le nombre de patients
    renseignés. L'outil ne dit jamais ce qu'un code veut dire : appelle
    decoder pour cela. Si les données ne permettent pas de conclure, le
    texte rendu commence par « abstention » : reprends alors cette raison.

    Args:
        colonne: nom exact de la colonne clinique codée, par exemple « General_cofactors ».
        codes: le ou les codes cherchés, séparés par une virgule ou un espace, par exemple « 6, 7 ».
        puce: type de puce (Chip_Type) à étudier ; None pour les puces qui mesurent la colonne.
    """
    demandes = _jetons(codes) if codes.strip() else []
    if not demandes or not all(jeton.isdigit() for jeton in demandes):
        return "abstention : les codes demandés doivent être des nombres entiers séparés par une virgule ou un espace."
    if not mesure.est_clinique(colonne) or colonne in communs.COLONNES_CLINIQUES_NUMERIQUES:
        return (
            f"abstention : {colonne!r} n'est pas une colonne clinique codée ; "
            "utiliser compter_selon_condition pour un dosage, l'âge, le mois ou Sensitization."
        )

    with communs.table_en_memoire():
        valeurs, mesuree, raison = mesure._lire(colonne, puce)
        cadre = mesure.perimetre(colonne, puce)
        if raison:
            return f"abstention : {raison}"
        if not mesuree:
            return f"abstention : la colonne {colonne!r} n'est mesurée par aucune puce de {cadre}."
        cellules = valeurs.dropna()
        garde = len(cellules)
        # Comme repartition_categories : sous 30 patients renseignés, on s'abstient ;
        # sous 50 % de renseignement, on répond mais on le dit (un comptage avec son
        # dénominateur ne prétend pas parler de toute la cohorte).
        if garde < mesure.EFFECTIF_MINIMAL:
            return f"abstention : {garde} patients renseignés pour {colonne!r} sur {cadre}, minimum {mesure.EFFECTIF_MINIMAL}."
        taux = garde / len(valeurs)
        neuf = mesure.valeurs_speciales(colonne, puce)[1]
        prefixe = mesure.prefixe(colonne, puce)

    listes = [_jetons(cellule) for cellule in cellules]
    if not all(jeton.isdigit() for liste in listes for jeton in liste):
        return f"abstention : {colonne!r} n'est pas une colonne de codes (cellules non numériques)."

    trouves = sum(1 for liste in listes if any(code in liste for code in demandes))
    texte = (
        f"{prefixe}{communs.entier(trouves)} patients sur {communs.entier(garde)} renseignés "
        f"({communs.fr(100 * trouves / garde)} %) ont au moins un des codes {', '.join(demandes)} dans {colonne!r} "
        f"({cadre}) ; cellules lues code par code, le code compte seul ou associé, dénominateur = patients renseignés."
    )
    if colonne in mesure.COLONNES_9_NON_RENSEIGNE:
        texte += f" {communs.entier(neuf)} valeurs 9 exclues (non renseigné, sens non confirmé sauf Rural_or_urban_area)."
    else:
        texte += " Aucun 9 exclu : cette colonne n'est pas dans la liste des colonnes où 9 est traité comme non renseigné."

    # Cellules qu'on ne peut pas trancher : un code à plusieurs chiffres qui
    # contient le code cherché (« 10 » pour « 1 ») est lu comme un seul code,
    # et un 9 associé à d'autres codes n'est pas exclu.
    longs = sum(
        1 for liste in listes
        if not any(code in liste for code in demandes)
        and any(len(jeton) > 1 and any(code in jeton for code in demandes) for jeton in liste)
    )
    neuf_associe = 0
    if colonne in mesure.COLONNES_9_NON_RENSEIGNE:
        neuf_associe = sum(1 for liste in listes if len(liste) > 1 and "9" in liste)
    if taux < mesure.TAUX_RENSEIGNEMENT_MINIMAL:
        texte += (
            f" Attention : colonne renseignée pour {round(100 * taux)} % des patients seulement, "
            "résultat non représentatif de toute la cohorte."
        )
    if longs:
        texte += (
            f" Ambigu : {communs.entier(longs)} cellules ont un code à plusieurs chiffres contenant le code cherché ; "
            "elles sont lues comme un seul code et ne sont pas comptées."
        )
    if neuf_associe:
        texte += f" Ambigu : {communs.entier(neuf_associe)} cellules associent un 9 à d'autres codes ; elles restent comptées."
    return texte
