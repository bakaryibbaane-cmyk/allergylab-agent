"""Outil : classement des colonnes de dosage par taux ou par nombre de patients positifs.

Chaque colonne est comptée sur les seuls patients dont la puce la mesure
(cellule renseignée) : un vide veut dire « non mesuré », jamais « négatif ».
Les ex æquo sont signalés. Rend un texte court, jamais le tableau.
Signé : équipe 5.
"""

from fractions import Fraction

import pandas as pd
from smolagents import tool

from equipe.outils import communs, mesure

RANG_MAXIMAL = 20


@tool
def classer_allergenes(critere: str, seuil: float, inclusif: bool, rang_max: int = 5, puce: str | None = None) -> str:
    """Rend les premiers dosages classés par taux de positivité ou par nombre de patients positifs.

    Positif = dosage > seuil, ou >= seuil si inclusif est vrai. Chaque colonne
    est comptée sur les patients mesurés (puces qui la mesurent). Les colonnes
    dont l'effectif mesuré est trop faible sont écartées et comptées. Si les
    données ne permettent pas de conclure, le texte rendu commence par
    « abstention » : reprends alors cette raison.

    Args:
        critere: « taux » (positifs sur mesurés) ou « effectif » (nombre de positifs).
        seuil: le seuil de positivité, par exemple 0.35.
        inclusif: vrai si un dosage égal au seuil est positif (>=), faux si le seuil est strict (>).
        rang_max: nombre de colonnes à rendre, de 1 à 20 (5 par défaut).
        puce: type de puce (Chip_Type) à étudier ; None pour toutes les puces qui mesurent chaque colonne.
    """
    if critere not in ("taux", "effectif"):
        return "abstention : le critère doit être « taux » ou « effectif »."
    if not 1 <= rang_max <= RANG_MAXIMAL:
        return f"abstention : rang_max doit être compris entre 1 et {RANG_MAXIMAL}."
    if puce is not None and puce not in communs.puces():
        return f"abstention : la puce {puce!r} est inconnue (puces : {', '.join(communs.puces())})."

    lignes = []  # (colonne, positifs, mesurés)
    ecartees = 0
    moins_un = 0
    with communs.table_en_memoire():
        for colonne in communs.dosages():
            # Même garde que partout : colonne non mesurée, moins de 30 patients
            # mesurés ou moins de 50 % de renseignement donnent une abstention.
            garde = mesure.verifier_perimetre(colonne, puce)
            if isinstance(garde, str):
                ecartees += 1
                continue
            valeurs, _, _ = mesure._lire(colonne, puce)
            nombres = pd.to_numeric(valeurs.dropna(), errors="coerce")
            positifs = int((nombres >= seuil).sum() if inclusif else (nombres > seuil).sum())
            lignes.append((colonne, positifs, garde))
            moins_un += mesure.valeurs_speciales(colonne, puce)[0]
    if not lignes:
        return "abstention : aucune colonne de dosage n'a assez de patients mesurés dans ce périmètre."

    # Le classement se fait sur des fractions exactes : deux taux égaux sont de vrais ex æquo.
    def valeur(ligne):
        return Fraction(ligne[1], ligne[2]) if critere == "taux" else ligne[1]

    lignes.sort(key=lambda ligne: (-valeur(ligne), ligne[0]))
    premiers = lignes[:rang_max]
    detail = " ; ".join(
        f"{rang}. {colonne} : "
        + (f"{communs.fr(100 * positifs / mesures, 2)} % ({communs.entier(positifs)} sur {communs.entier(mesures)})"
           if critere == "taux" else f"{communs.entier(positifs)} positifs (sur {communs.entier(mesures)} mesurés)")
        for rang, (colonne, positifs, mesures) in enumerate(premiers, start=1)
    )
    cadre = f"la puce {puce}" if puce else "toutes les puces, chaque colonne sur les puces qui la mesurent"
    operateur = ">=" if inclusif else ">"
    texte = (
        f"Classement par {'taux de positivité' if critere == 'taux' else 'nombre de patients positifs'} "
        f"de {len(lignes)} colonnes de dosage ({cadre}), positif = dosage {operateur} {communs.valeur_texte(seuil)} "
        f"({'inclusif' if inclusif else 'strict'}), dénominateur = patients mesurés :\n{detail}."
    )

    # Ex æquo : toute valeur partagée par plusieurs colonnes dont une est dans le haut du classement.
    notes = []
    deja_vus = []
    for ligne in premiers:
        if valeur(ligne) in deja_vus:
            continue
        deja_vus.append(valeur(ligne))
        egales = [autre[0] for autre in lignes if valeur(autre) == valeur(ligne)]
        if len(egales) > 1:
            notes.append(f"ex æquo : {', '.join(egales)}")
    if notes:
        texte += f"\nAttention, {' ; '.join(notes)}."
    if ecartees:
        texte += f"\n{ecartees} colonnes écartées (non mesurées ici, moins de 30 patients mesurés ou moins de 50 % de renseignement)."
    if moins_un:
        texte += f" {moins_un} valeurs -1 dans les colonnes classées, comparées comme le nombre -1, non recodées (sens non confirmé)."
    return texte
