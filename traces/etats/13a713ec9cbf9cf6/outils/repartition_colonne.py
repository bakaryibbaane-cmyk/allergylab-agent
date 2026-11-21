"""Outil : compte les valeurs d'une colonne, éventuellement pour une puce.

NON BRANCHÉ dans l'agent (equipe/agent.py). Il n'a pas la garde de
repartition_categories (equipe/outils/repartition.py), qui est la version à
utiliser : ici rien ne traite la colonne multi-codes General_cofactors
(« 1, 3 » compté comme une seule valeur), dont le sens du code 10 n'est pas
confirmé, et rien ne signale les 9 ni les -1. Module gardé et testé, mais
l'agent ne l'appelle pas.

Les patients dont la puce ne mesure pas la colonne sont exclus du calcul.
Ils ne doivent pas être confondus avec des patients ayant une mesure manquante.
Les cellules vides sont comptées séparément des autres valeurs.
Repris d'une version du binôme. Signé : équipe 5.
"""

from smolagents import tool

from kit.donnees import COLONNE_PUCE, charger, colonnes

NB_VALEURS_MAX = 12
PUCES_ORDRE = ("ALEX", "ISAC_V1", "ISAC_V2")
PUCES = set(PUCES_ORDRE)


@tool
def repartition_colonne(colonne: str, puce: str) -> str:
    """Compte les patients par valeur dans une colonne du tableau.

    Args:
        colonne: nom exact de la colonne, par exemple "Che_a".
        puce: "ALEX", "ISAC_V1", "ISAC_V2", ou "toutes".
    """
    if puce != "toutes" and puce not in PUCES:
        return f"{puce} : puce inconnue (ALEX, ISAC_V1, ISAC_V2 ou toutes)"

    tableau = charger()

    if colonne not in tableau.columns:
        return f"{colonne} : colonne absente du tableau"

    if COLONNE_PUCE not in tableau.columns:
        return f"Colonne de type de puce absente : {COLONNE_PUCE}"

    dictionnaire = colonnes().set_index("colonne")

    if colonne not in dictionnaire.index:
        return f"{colonne} : colonne absente du dictionnaire des colonnes"

    definition = dictionnaire.loc[colonne]

    puces_mesurantes = [nom for nom in PUCES_ORDRE if bool(definition[f"puce_{nom}"])]

    if not puces_mesurantes:
        return f"{colonne} : aucune puce ne mesure cette colonne"

    if puce != "toutes":
        if puce not in puces_mesurantes:
            return f"{colonne} : non mesurée par {puce} ; répartition non calculée"
        tableau = tableau[tableau[COLONNE_PUCE] == puce]
        libelle = puce
    else:
        tableau = tableau[tableau[COLONNE_PUCE].isin(puces_mesurantes)]
        libelle = f"toutes (puces mesurantes : {', '.join(puces_mesurantes)})"

    serie = tableau[colonne]
    vides = int(serie.isna().sum())
    comptes = serie.value_counts().head(NB_VALEURS_MAX)
    valeurs = " ; ".join(f"{valeur} -> {int(nombre)}" for valeur, nombre in comptes.items())
    autres = int(serie.nunique()) - len(comptes)

    texte = f"{colonne}, {len(serie)} patients ({libelle}) : {valeurs or 'aucune valeur'} ; cellules vides -> {vides}"
    if autres > 0:
        texte += f" ; {autres} autres valeurs non listées"
    return texte
