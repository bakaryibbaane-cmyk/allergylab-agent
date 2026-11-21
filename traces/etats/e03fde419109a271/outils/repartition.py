"""Outil : répartition des patients par code, pour une colonne clinique codée.

Une colonne clinique comme Rural_or_urban_area (0 = rural, 1 = urbain...) est un
code : ni proportion de « positifs », ni moyenne n'ont de sens. On rend
l'effectif et le pourcentage de chaque code, sur les patients renseignés. Les 9
des colonnes listées dans mesure.py (rapprochement par libellé, un seul solide)
sont déjà exclus. Aucun recodage, un texte
rendu, jamais le tableau. Signé : équipe 5.
"""

from smolagents import tool

from equipe.outils import mesure

# Au-delà, ce n'est plus une colonne codée (Age a une soixantaine de valeurs).
NB_CODES_MAX = 20


def _fr(nombre):
    """Un pourcentage à une décimale, à la française : 38,5."""
    return f"{nombre:.1f}".replace(".", ",")


def _entier(nombre):
    """Un entier avec une espace entre les milliers : 3 132."""
    return f"{nombre:,}".replace(",", " ")


@tool
def repartition_categories(colonne: str, puce: str | None = None) -> str:
    """Rend l'effectif et le pourcentage de chaque code d'une colonne clinique codée.

    Réservé aux colonnes cliniques lues en nombre (Rural_or_urban_area,
    Skin_Symptoms...). Si les données ne permettent pas de conclure, le texte
    rendu commence par « abstention » : reprends alors cette raison.

    Args:
        colonne: nom exact de la colonne clinique, par exemple « Skin_Symptoms ».
        puce: type de puce (Chip_Type) à étudier ; None pour tout le fichier.
    """
    # Colonne ou puce inconnue : la raison vient de mesure.py.
    valeurs, mesuree, raison = mesure._lire(colonne, puce)
    if raison:
        return f"abstention : {raison}"
    if not mesure.est_clinique(colonne):
        return (
            f"abstention : {colonne!r} est une colonne de dosage, une répartition par code n'a pas de sens ; "
            "utiliser proportion_positifs ou moyenne_colonne."
        )
    lecture = mesure.donnees.colonnes().set_index("colonne").loc[colonne, "lecture"]
    if lecture != "nombre":
        return f"abstention : {colonne!r} est lue en texte (valeurs multiples possibles), une répartition par code n'est pas fiable."
    cadre = mesure.perimetre(colonne, puce)
    if not mesuree:
        return f"abstention : la colonne {colonne!r} n'est mesurée par aucune puce de {cadre}."

    # Les 9 = non renseigné sont déjà vides ici ; les autres codes restent tels quels.
    renseignes = valeurs.dropna()
    effectif = len(renseignes)
    if effectif < mesure.EFFECTIF_MINIMAL:
        return f"abstention : {effectif} patients renseignés pour {colonne!r} sur {cadre}, minimum {mesure.EFFECTIF_MINIMAL}."
    comptes = renseignes.value_counts().sort_index()
    if len(comptes) > NB_CODES_MAX:
        return f"abstention : {colonne!r} compte {len(comptes)} valeurs différentes, ce n'est pas une colonne codée."

    taux = effectif / len(valeurs)
    codes = " ; ".join(
        f"code {int(code) if float(code).is_integer() else code} : {_entier(int(n))} ({_fr(100 * n / effectif)} %)"
        for code, n in comptes.items()
    )
    texte = (
        f"{mesure.prefixe(colonne, puce)}Répartition de {colonne!r} ({cadre}) sur {_entier(effectif)} patients renseignés "
        f"(taux de renseignement {_fr(100 * taux)} %) : {codes}."
    )
    neuf = mesure.valeurs_speciales(colonne, puce)[1]
    if neuf:
        texte += f" Hors {_entier(neuf)} valeurs 9 traitées comme non renseignées (sens non confirmé), exclues."
    if taux < mesure.TAUX_RENSEIGNEMENT_MINIMAL:
        texte += (
            f" Attention : renseignée pour {round(100 * taux)} % des patients seulement, "
            "résultat non représentatif de toute la cohorte."
        )
    return texte
