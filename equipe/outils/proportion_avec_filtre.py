"""Outil : proportion de positifs d'un dosage parmi les patients qui vérifient un filtre.

Le filtre porte sur une colonne numérique (Age, mois, Sensitization ou un
autre dosage). Le dénominateur est le nombre de patients qui vérifient le
filtre ET dont le dosage est mesuré : un vide veut dire « non mesuré », il
n'entre ni dans le filtre ni dans le dénominateur. Les -1 sont comptés et
signalés, jamais recodés. Rend un texte court, jamais le tableau.
Signé : équipe 5.
"""

import pandas as pd
from smolagents import tool

from equipe.outils import communs, intervalle, mesure


def _numerique(colonne):
    """Vrai pour un dosage ou l'une des colonnes cliniques lues comme des mesures."""
    return colonne in communs.COLONNES_CLINIQUES_NUMERIQUES or colonne in communs.dosages()


@tool
def proportion_avec_filtre(
    colonne: str, seuil: float, filtre_colonne: str, operateur: str, valeur: float, puce: str | None = None
) -> str:
    """Rend la proportion de positifs (dosage > seuil) parmi les patients qui vérifient un filtre.

    Le filtre compare une colonne numérique (Age, Blood_Month_sample,
    Sensitization ou un dosage) à une valeur. Le dénominateur est le nombre
    de patients qui vérifient le filtre et dont le dosage est mesuré. Si les
    données ne permettent pas de conclure, le texte rendu commence par
    « abstention » : reprends alors cette raison. Le sens d'un code vient de decoder.

    Args:
        colonne: nom exact du dosage dont on cherche les positifs, par exemple « Ara_h_2 ».
        seuil: le seuil de positivité (positif = dosage > seuil, strict), par exemple 0.35.
        filtre_colonne: nom exact de la colonne du filtre, par exemple « Age ».
        operateur: l'un de ==, !=, <, <=, > ou >= pour le filtre.
        valeur: la valeur du filtre, par exemple 10.
        puce: type de puce (Chip_Type) à étudier ; None pour les puces qui mesurent les deux colonnes.
    """
    operateur = operateur.strip()
    if operateur not in communs.OPERATEURS:
        return f"abstention : l'opérateur {operateur!r} n'existe pas (permis : {', '.join(communs.OPERATEURS)})."
    comparer, en_mots = communs.OPERATEURS[operateur]
    if colonne not in communs.dosages():
        return f"abstention : {colonne!r} n'est pas une colonne de dosage, une proportion de positifs n'a pas de sens."
    if not _numerique(filtre_colonne):
        return f"abstention : le filtre porte sur {filtre_colonne!r}, qui n'est pas une colonne numérique (dosage, Age, mois, Sensitization)."

    with communs.table_en_memoire():
        for nom in (colonne, filtre_colonne):
            garde = mesure.verifier_perimetre(nom, puce)
            if isinstance(garde, str):
                return garde
        dosage, _, _ = mesure._lire(colonne, puce)
        filtre, _, _ = mesure._lire(filtre_colonne, puce)
        moins_un = mesure.valeurs_speciales(colonne, puce)[0]
        cadre = mesure.perimetre(colonne, puce)

    # Un patient compte s'il a le filtre ET le dosage renseignés (index communs).
    filtre = pd.to_numeric(filtre.dropna(), errors="coerce")
    dosage = pd.to_numeric(dosage.dropna(), errors="coerce")
    retenus = filtre[comparer(filtre, valeur)].index
    mesures = dosage.loc[dosage.index.intersection(retenus)]
    effectif = len(mesures)
    sans_dosage = len(retenus) - effectif
    if effectif < mesure.EFFECTIF_MINIMAL:
        return (
            f"abstention : {effectif} patients vérifient {filtre_colonne!r} {operateur} {communs.valeur_texte(valeur)} "
            f"avec {colonne!r} mesuré ({cadre}), minimum {mesure.EFFECTIF_MINIMAL}."
        )
    positifs = int((mesures > seuil).sum())
    basse, haute = intervalle.intervalle_wilson(positifs, effectif)
    texte = (
        f"{communs.fr(100 * positifs / effectif)} % (IC 95 % : {communs.fr(basse)} à {communs.fr(haute)}), "
        f"{communs.entier(positifs)} positifs sur {communs.entier(effectif)} patients mesurés pour {colonne!r} ({cadre}), "
        f"positif = valeur > {communs.valeur_texte(seuil)} (strict).\n"
        f"Filtre : {filtre_colonne!r} {en_mots} {communs.valeur_texte(valeur)} ({operateur}), dénominateur = patients "
        f"qui vérifient le filtre et dont {colonne!r} est mesuré ; {communs.entier(sans_dosage)} patients du filtre exclus faute de mesure."
    )
    if moins_un:
        texte += (
            f"\nAttention : {moins_un} valeurs -1 dans les mesures de {colonne!r} du périmètre, comparées comme le nombre -1, "
            "leur sens n'est pas confirmé, elles n'ont pas été recodées."
        )
    return texte
