"""Outil : combien de valeurs d'une colonne clinique sont associées à plusieurs valeurs d'une autre.

On regarde les patients dont les deux cellules sont renseignées, puis on compte,
pour chaque valeur distincte de `colonne`, les valeurs distinctes de `par` qui
l'accompagnent. Une valeur est « associée » à `minimum` valeurs de `par` ou plus
si elle apparaît avec au moins ce nombre de valeurs différentes. La valeur est
la cellule entière, lue telle quelle (« 1, 3 » est une valeur, pas deux codes).
Rend un texte court, jamais le tableau. Signé : équipe 5.
"""

from smolagents import tool

from equipe.outils import communs, mesure


def _texte(valeurs):
    """Les cellules en texte : 1.0 devient « 1 », « deptA » reste « deptA », les espaces de bord sont retirés."""
    def une(cellule):
        if isinstance(cellule, str):
            return cellule.strip()
        nombre = float(cellule)
        return str(int(nombre)) if nombre.is_integer() else str(nombre)

    return valeurs.map(une)


@tool
def croiser_colonnes(colonne: str, par: str, minimum: int = 2) -> str:
    """Rend combien de valeurs distinctes d'une colonne clinique sont associées à au moins `minimum` valeurs distinctes d'une autre.

    Seuls les patients dont les deux cellules sont renseignées comptent (une
    cellule vide veut dire « non renseigné »). Le dénominateur est le nombre de
    valeurs distinctes de `colonne` parmi ces patients. L'outil ne dit jamais ce
    qu'une valeur veut dire. Si les données ne permettent pas de conclure, le
    texte rendu commence par « abstention » : reprends alors cette raison.

    Args:
        colonne: nom exact de la colonne clinique dont on compte les valeurs distinctes.
        par: nom exact de l'autre colonne clinique, celle dont on compte les valeurs associées.
        minimum: nombre minimal de valeurs distinctes de `par` (2 par défaut).
    """
    if colonne == par:
        return "abstention : les deux colonnes sont la même ; il en faut deux différentes."
    if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 1:
        return "abstention : le minimum doit être un nombre entier supérieur ou égal à 1."
    for nom in (colonne, par):
        if not mesure.est_clinique(nom):
            return f"abstention : {nom!r} n'est pas une colonne clinique du fichier (dosages : utiliser les outils de dosage)."

    with communs.table_en_memoire():
        lues = {}
        for nom in (colonne, par):
            # mesure.py décide de ce qui est « renseigné » : un vide, et le 9 des colonnes de sa liste, ne le sont pas.
            controle = mesure.verifier_perimetre(nom)
            if isinstance(controle, str):
                return controle
            lues[nom] = mesure._lire(nom, None)[0]
    duo = lues[colonne].to_frame("a").join(lues[par].rename("b")).dropna()
    ecartes = len(lues[colonne]) - len(duo)
    if len(duo) < mesure.EFFECTIF_MINIMAL:
        return (
            f"abstention : {len(duo)} patients ont {colonne!r} et {par!r} renseignées, "
            f"minimum {mesure.EFFECTIF_MINIMAL}."
        )
    duo = duo.assign(a=_texte(duo["a"]), b=_texte(duo["b"]))
    associees = duo.groupby("a")["b"].nunique()
    total = len(associees)
    retenues = int((associees >= minimum).sum())
    texte = (
        f"{communs.entier(retenues)} valeurs distinctes de {colonne!r} sur {communs.entier(total)} sont associées "
        f"à au moins {minimum} valeurs distinctes de {par!r}, tout le fichier."
    )
    texte += (
        f"\nDéfinition : les patients dont l'une des deux cellules est vide ({communs.entier(ecartes)}) sont écartés, "
        f"une valeur est la cellule entière, dénominateur = valeurs distinctes de {colonne!r} parmi "
        f"{communs.entier(len(duo))} patients renseignés."
    )
    neufs = [nom for nom in (colonne, par) if nom in mesure.COLONNES_9_NON_RENSEIGNE]
    if neufs:
        texte += f" Les 9 de {', '.join(neufs)} sont traités comme non renseignés (liste de mesure.py)."
    return texte
