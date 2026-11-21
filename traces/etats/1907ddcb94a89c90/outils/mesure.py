"""Mesure : ce que les données permettent de dire d'une colonne, avant tout calcul.

Dans ce fichier, une colonne de dosage est renseignée pour toute une puce
(Chip_Type) ou vide pour toute la puce. Un vide veut donc dire « non mesuré »,
jamais « non sensibilisé » : un patient sans mesure ne doit pas entrer dans un
dénominateur. Ces fonctions rendent un nombre ou un texte, jamais le tableau.

Elles ne devinent rien : un nom de colonne ou de puce inconnu donne 0 ou une
abstention, jamais la colonne « la plus proche ».
Signé : équipe 5.
"""

from kit import donnees

# Sous 30 patients mesurés, une proportion est trop instable : à 50 %, son
# intervalle de confiance fait environ ±18 points. Convention à confirmer
# avec les chercheurs.
EFFECTIF_MINIMAL = 30

# Si moins de la moitié des patients du périmètre ont la colonne renseignée,
# le résultat ne parle que d'une minorité : on s'abstient plutôt que de
# présenter ce chiffre comme celui de tout le périmètre.
TAUX_RENSEIGNEMENT_MINIMAL = 0.5


def _lire(colonne, puce):
    """Rend (valeurs de la colonne pour le périmètre, mesurée ?, raison d'échec).

    La raison vaut None quand la colonne et la puce existent. « Mesurée »
    vient du dictionnaire des colonnes : vraie si au moins une puce du
    périmètre la renseigne.
    """
    tableau = donnees.charger()
    dictionnaire = donnees.colonnes().set_index("colonne")
    if colonne not in dictionnaire.index or colonne not in tableau.columns:
        return None, False, f"la colonne {colonne!r} n'existe pas dans le fichier."
    puces = [nom[len("puce_"):] for nom in dictionnaire.columns if nom.startswith("puce_")]
    if puce is not None and puce not in puces:
        return None, False, f"la puce {puce!r} est inconnue (puces : {', '.join(puces)})."
    concernees = puces if puce is None else [puce]
    mesuree = any(dictionnaire.loc[colonne, "puce_" + nom] for nom in concernees)
    lignes = tableau if puce is None else tableau[tableau[donnees.COLONNE_PUCE] == puce]
    return lignes[colonne], bool(mesuree), None


def effectif_mesure(colonne, puce=None):
    """Nombre de patients du périmètre dont la colonne est renseignée.

    Rend 0 si la colonne est inconnue ou si aucune puce du périmètre ne la mesure.
    """
    valeurs, mesuree, raison = _lire(colonne, puce)
    if raison or not mesuree:
        return 0
    return int(valeurs.notna().sum())


def valeurs_speciales(colonne, puce=None):
    """Rend [nombre de valeurs -1, nombre de valeurs 9] de la colonne.

    Le sens de -1 et de 9 n'est pas confirmé : on les compte pour les
    signaler, on ne les recode pas et on ne les exclut pas. Une colonne
    inconnue donne [0, 0] ; c'est verifier_perimetre qui la refuse.
    """
    valeurs, _, raison = _lire(colonne, puce)
    if raison:
        return [0, 0]

    def compter(special):
        # Les colonnes en nombres se comparent au nombre, celles restées en
        # texte (« 9 », « 1, 3 ») à leur écriture.
        return int(((valeurs == special) | (valeurs.astype(str).str.strip() == str(special))).sum())

    return [compter(-1), compter(9)]


def verifier_perimetre(colonne, puce=None):
    """Rend « abstention : <raison> », ou le nombre de patients mesurés.

    À appeler avant toute proportion ou moyenne : si la réponse est un
    texte, l'agent s'abstient et reprend cette raison dans sa justification.
    """
    valeurs, mesuree, raison = _lire(colonne, puce)
    if raison:
        return f"abstention : {raison}"
    perimetre = "tout le fichier" if puce is None else f"la puce {puce}"
    if not mesuree:
        return f"abstention : la colonne {colonne!r} n'est mesurée par aucune puce de {perimetre}."
    effectif = int(valeurs.notna().sum())
    if effectif < EFFECTIF_MINIMAL:
        return f"abstention : {effectif} patients mesurés pour {colonne!r} sur {perimetre}, minimum {EFFECTIF_MINIMAL}."
    taux = effectif / len(valeurs)
    if taux < TAUX_RENSEIGNEMENT_MINIMAL:
        return (
            f"abstention : {colonne!r} n'est renseignée que pour {taux:.0%} des patients de {perimetre}, "
            f"minimum {TAUX_RENSEIGNEMENT_MINIMAL:.0%}."
        )
    return effectif
