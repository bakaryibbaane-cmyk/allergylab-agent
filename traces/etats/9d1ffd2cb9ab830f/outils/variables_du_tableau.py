"""Outil : nombre de variables (colonnes) du tableau, et recherche d'une variable par son nom.

L'agent est fermé : il ne voit pas le tableau. Cet outil lui donne la forme du
tableau, calculée sur le tableau lui-même (jamais de mémoire). Il rend des noms
de colonnes et des nombres, jamais une valeur de patient, et n'écrit rien
sur le disque.
Signé : équipe 5.
"""

from smolagents import tool

from kit import donnees

# Au plus ce nombre de noms dans la réponse : le reste est compté, pas listé.
MAX_NOMS = 30


@tool
def variables_du_tableau(motif: str = "") -> str:
    """Rend le nombre de variables (colonnes) du tableau, ou les noms de colonnes qui contiennent un motif.

    Sans motif, rend le nombre de variables, sans lister les noms. Avec un
    motif, rend les noms de colonnes qui le contiennent (majuscules et
    minuscules ignorées), 30 au plus, avec le nombre total de correspondances.
    Ne rend que des noms et des nombres, jamais la valeur d'un patient, et ne
    dit rien du sens ni du contenu des colonnes.

    Args:
        motif: texte à chercher dans les noms de colonnes, par exemple « age » ; vide pour obtenir seulement le nombre de variables.
    """
    noms = list(donnees.charger().columns)
    motif = (motif or "").strip()

    if not motif:
        return f"Le tableau contient {len(noms)} variables (colonnes). Les noms ne sont pas listés : donne un motif pour chercher une variable."

    trouvees = [nom for nom in noms if motif.lower() in nom.lower()]
    if not trouvees:
        return f"Aucune variable ne contient {motif!r} sur les {len(noms)} variables du tableau."

    texte = f"{len(trouvees)} variables contiennent {motif!r} sur les {len(noms)} du tableau : {', '.join(trouvees[:MAX_NOMS])}."
    if len(trouvees) > MAX_NOMS:
        texte += f" Liste tronquée : {MAX_NOMS} noms affichés sur {len(trouvees)}."
    return texte
