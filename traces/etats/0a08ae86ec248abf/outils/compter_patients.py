"""Outil : nombre de patients (lignes du tableau), au total ou pour une puce.

Un patient est une ligne du tableau. Sans puce, l'outil rend aussi le détail
par puce, calculé sur le tableau : on ne le recopie jamais de mémoire. Il
rend un texte court (des effectifs), jamais une donnée individuelle.
Signé : équipe 5.
"""

from smolagents import tool

from kit import donnees


def _entier(nombre):
    """Un entier avec une espace entre les milliers : 4 271."""
    return f"{nombre:,}".replace(",", " ")


@tool
def compter_patients(puce: str | None = None) -> str:
    """Rend le nombre de patients (lignes du tableau), au total ou pour une puce.

    Sans puce, rend le total et le détail par puce. Si la puce est inconnue,
    le texte rendu commence par « abstention » : reprends alors cette raison
    dans ta réponse.

    Args:
        puce: type de puce (Chip_Type) à compter, par exemple « ALEX » ; None pour toutes les puces.
    """
    tableau = donnees.charger()
    # Les puces connues viennent de kit/colonnes.csv, comme dans mesure.py.
    dictionnaire = donnees.colonnes()
    puces = [nom[len("puce_"):] for nom in dictionnaire.columns if nom.startswith("puce_")]
    if puce is not None and puce not in puces:
        return f"abstention : la puce {puce!r} est inconnue (puces : {', '.join(puces)})."

    if puce is not None:
        n = int((tableau[donnees.COLONNE_PUCE] == puce).sum())
        return f"{_entier(n)} patients pour la puce {puce}."

    comptes = tableau[donnees.COLONNE_PUCE].value_counts()
    detail = " ; ".join(f"{nom} : {_entier(int(comptes.get(nom, 0)))}" for nom in puces)
    return f"{_entier(len(tableau))} patients au total. Par puce : {detail}."
