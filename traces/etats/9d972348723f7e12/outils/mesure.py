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

# Colonnes cliniques codées dont le 9 est traité comme « non renseigné ». Le
# dictionnaire officiel (donnees/acc-dictionnaire-final.xls) ne contient aucun
# nom de colonne du fichier : les rapprochements se font par libellé.
# - Rural_or_urban_area (« Type d'habitat », 9 = « Non renseigné ») : solide.
# - Skin_Symptoms, Age_of_onsets, Treatment_of_rhinitis : rapprochement par
#   libellé non confirmé. Pour Skin_Symptoms, le dictionnaire dit « sans objet »
#   (même effet sur le dénominateur).
# Dans ces colonnes, un 9 n'est pas une mesure : il est exclu de l'effectif
# mesuré (donc du dénominateur et des moyennes) et compté à part. Ailleurs, 9
# est une vraie valeur (Age, Blood_Month_sample, dosages) : on n'y touche pas.
# Treatment_of_athsma et Treatment_of_atopic_dematitis ont aussi des 9, mais
# leur sens n'est pas confirmé : elles ne sont pas dans la liste.
COLONNES_9_NON_RENSEIGNE = (
    "Rural_or_urban_area",
    "Skin_Symptoms",
    "Age_of_onsets",
    "Treatment_of_rhinitis",
)


def _est_valeur(valeurs, special):
    """Cases égales à special. Les colonnes en nombres se comparent au nombre,
    celles restées en texte (« 9 », « 1, 3 ») à leur écriture."""
    return (valeurs == special) | (valeurs.astype(str).str.strip() == str(special))


def est_clinique(colonne):
    """Vrai si la colonne est du bloc clinique de kit/colonnes.csv."""
    dictionnaire = donnees.colonnes().set_index("colonne")
    return colonne in dictionnaire.index and dictionnaire.loc[colonne, "bloc"] == "clinique"


def _brut(colonne, puce):
    """Rend (valeurs brutes du périmètre, puces mesurantes, raison d'échec).

    Sans puce précisée, le périmètre est celui des puces qui mesurent la
    colonne (marquées vraies dans kit/colonnes.csv), pas les 4 271 lignes :
    un vide dû à une puce qui ne la mesure pas n'est pas un patient « non
    renseigné ». Si aucune puce ne la mesure, le périmètre reste tout le fichier.
    """
    tableau = donnees.charger()
    dictionnaire = donnees.colonnes().set_index("colonne")
    if colonne not in dictionnaire.index or colonne not in tableau.columns:
        return None, [], f"la colonne {colonne!r} n'existe pas dans le fichier."
    puces = [nom[len("puce_"):] for nom in dictionnaire.columns if nom.startswith("puce_")]
    if puce is not None and puce not in puces:
        return None, [], f"la puce {puce!r} est inconnue (puces : {', '.join(puces)})."
    concernees = puces if puce is None else [puce]
    mesurantes = [nom for nom in concernees if dictionnaire.loc[colonne, "puce_" + nom]]
    if puce is None and mesurantes:
        lignes = tableau[tableau[donnees.COLONNE_PUCE].isin(mesurantes)]
    elif puce is None:
        lignes = tableau
    else:
        lignes = tableau[tableau[donnees.COLONNE_PUCE] == puce]
    return lignes[colonne], mesurantes, None


def _lire(colonne, puce):
    """Rend (valeurs de la colonne pour le périmètre, mesurée ?, raison d'échec).

    La raison vaut None quand la colonne et la puce existent. « Mesurée »
    vient du dictionnaire des colonnes : vraie si au moins une puce du
    périmètre la renseigne. Dans COLONNES_9_NON_RENSEIGNE, les 9 sont
    rendus vides : un patient « non renseigné » n'est pas mesuré.
    """
    valeurs, mesurantes, raison = _brut(colonne, puce)
    if raison:
        return None, False, raison
    if colonne in COLONNES_9_NON_RENSEIGNE:
        valeurs = valeurs.mask(_est_valeur(valeurs, 9))
    return valeurs, bool(mesurantes), None


def perimetre(colonne, puce=None):
    """Le périmètre en mots : « la puce ALEX », « ALEX seule », « tout le fichier »."""
    if puce is not None:
        return f"la puce {puce}"
    _, mesurantes, raison = _brut(colonne, puce)
    toutes = [nom[len("puce_"):] for nom in donnees.colonnes().columns if nom.startswith("puce_")]
    if raison or not mesurantes or len(mesurantes) == len(toutes):
        return "tout le fichier"
    if len(mesurantes) == 1:
        return f"{mesurantes[0]} seule"
    return " et ".join(mesurantes)


def prefixe(colonne, puce=None):
    """« Calculé sur ALEX seule : » quand la puce n'est pas précisée et que
    toutes les puces ne mesurent pas la colonne ; sinon rien."""
    libelle = perimetre(colonne, puce)
    if puce is not None or libelle == "tout le fichier":
        return ""
    return f"Calculé sur {libelle} : "


def effectif_mesure(colonne, puce=None):
    """Nombre de patients du périmètre dont la colonne est renseignée.

    Rend 0 si la colonne est inconnue ou si aucune puce du périmètre ne la mesure.
    """
    valeurs, mesuree, raison = _lire(colonne, puce)
    if raison or not mesuree:
        return 0
    return int(valeurs.notna().sum())


def valeurs_speciales(colonne, puce=None):
    """Rend [nombre de valeurs -1, nombre de valeurs 9 exclues] de la colonne.

    Le sens de -1 n'est pas confirmé : on le compte pour le signaler, on ne
    le recode pas et on ne l'exclut pas. Les 9 ne sont comptés que dans
    COLONNES_9_NON_RENSEIGNE, où ils sont exclus ; ailleurs, 9 est une
    valeur ordinaire et le second nombre vaut 0. Une colonne inconnue donne
    [0, 0] ; c'est verifier_perimetre qui la refuse.
    """
    valeurs, _, raison = _lire(colonne, puce)
    if raison:
        return [0, 0]
    moins_un = int(_est_valeur(valeurs, -1).sum())
    neuf = 0
    if colonne in COLONNES_9_NON_RENSEIGNE:
        neuf = int(_est_valeur(_brut(colonne, puce)[0], 9).sum())
    return [moins_un, neuf]


def verifier_perimetre(colonne, puce=None):
    """Rend « abstention : <raison> », ou le nombre de patients mesurés.

    À appeler avant toute proportion ou moyenne : si la réponse est un
    texte, l'agent s'abstient et reprend cette raison dans sa justification.
    """
    valeurs, mesuree, raison = _lire(colonne, puce)
    if raison:
        return f"abstention : {raison}"
    cadre = perimetre(colonne, puce)
    if not mesuree:
        return f"abstention : la colonne {colonne!r} n'est mesurée par aucune puce de {cadre}."
    effectif = int(valeurs.notna().sum())
    if effectif < EFFECTIF_MINIMAL:
        return f"abstention : {effectif} patients mesurés pour {colonne!r} sur {cadre}, minimum {EFFECTIF_MINIMAL}."
    taux = effectif / len(valeurs)
    if taux < TAUX_RENSEIGNEMENT_MINIMAL:
        return (
            f"abstention : {colonne!r} n'est renseignée que pour {taux:.0%} des patients ({cadre}), "
            f"minimum {TAUX_RENSEIGNEMENT_MINIMAL:.0%}."
        )
    return effectif
