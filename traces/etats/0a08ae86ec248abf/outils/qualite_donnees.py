"""Outil : diagnostic de qualité d'une colonne (ou des colonnes cliniques) pour une puce.

Il décrit, il ne modifie rien. Il sépare trois sortes de cellules vides ou particulières :
- colonne non mesurée par la puce (vide structurel : ce n'est pas un patient qui n'a pas répondu) ;
- cellule vide dans une colonne mesurée (donnée réellement absente) ;
- valeurs -1 (partout) et 9 (dosages), comptées et signalées, jamais exclues ni recodées.

Seule exception : le 9 des colonnes de COLONNES_9_NON_RENSEIGNE (equipe/outils/mesure.py),
traité comme non renseigné et donc retiré des cellules exploitables, comme le font
les autres outils de l'équipe. Pour toutes sauf Rural_or_urban_area, ce sens n'est pas
confirmé par le dictionnaire.
Il ne dit jamais qu'une variable est « valide » pour une étude : il donne des indicateurs.
Repris d'une version du binôme, adapté à la règle de l'équipe. Signé : équipe 5.
"""

from smolagents import tool

from kit.donnees import COLONNE_PUCE, charger, colonnes
from equipe.outils.mesure import COLONNES_9_NON_RENSEIGNE

NB_PLUS_INCOMPLETES = 5


def effectifs(serie, colonne, bloc):
    """Rend (non vides, vides, codes -1, codes 9 exclus, codes 9 signalés).

    Les -1 sont comptés dans tous les blocs, jamais exclus. Les 9 d'un dosage
    sont comptés mais restent des valeurs. Les 9 de COLONNES_9_NON_RENSEIGNE
    sont comptés et exclus. Ailleurs, 9 est une valeur ordinaire.
    """
    renseignees = int(serie.notna().sum())
    vides = len(serie) - renseignees
    texte = serie.astype("string").str.strip()

    moins_un = int(texte.isin(["-1", "-1.0"]).sum())
    neuf = int(texte.isin(["9", "9.0"]).sum())
    neuf_exclus = neuf if colonne in COLONNES_9_NON_RENSEIGNE else 0
    neuf_signales = neuf if bloc == "dosage" else 0
    return renseignees, vides, moins_un, neuf_exclus, neuf_signales


@tool
def qualite_donnees(colonne: str, puce: str) -> str:
    """Diagnostic de qualité d'une colonne du tableau pour une puce, sans rien modifier.

    Args:
        colonne: le nom exact de la colonne, par exemple "Bet_v_4", ou "toutes" pour un résumé des colonnes cliniques.
        puce: "ALEX", "ISAC_V1", "ISAC_V2", ou "toutes" pour tous les patients.
    """
    tableau = charger()
    dico = colonnes().set_index("colonne")
    if puce != "toutes":
        if puce not in set(tableau[COLONNE_PUCE]):
            return f"{puce} : puce inconnue (ALEX, ISAC_V1, ISAC_V2 ou toutes)"
        tableau = tableau[tableau[COLONNE_PUCE] == puce]
    if colonne == "toutes":
        return resume(tableau, dico, puce)
    if colonne not in tableau.columns:
        return f"{colonne} : colonne absente du tableau"
    bloc = dico.loc[colonne, "bloc"]
    if puce != "toutes" and not dico.loc[colonne, f"puce_{puce}"]:
        return (
            f"{colonne} ({bloc}), {len(tableau)} patients {puce} : colonne non mesurée par cette puce. "
            "Les cellules vides sont structurelles, pas des réponses manquantes."
        )
    renseignees, vides, moins_un, neuf_exclus, neuf_signales = effectifs(tableau[colonne], colonne, bloc)
    reelles = renseignees - neuf_exclus
    taux = round(100 * reelles / len(tableau), 1) if len(tableau) else 0.0
    texte = (
        f"{colonne} ({bloc}), {len(tableau)} patients ({puce}) : "
        f"{reelles} cellules exploitables ({taux} %), {vides} cellules vides."
    )
    if moins_un:
        texte += f" Valeurs -1 : {moins_un} (comptées, ni exclues ni recodées, sens non confirmé)."
    if neuf_signales:
        texte += f" Valeurs 9 : {neuf_signales} (comptées, non exclues)."
    if neuf_exclus:
        if colonne == "Rural_or_urban_area":
            sens = "non renseigné selon le dictionnaire"
        else:
            sens = "traité comme non renseigné (sens non confirmé)"
        texte += f" Parmi les non vides, {neuf_exclus} sont au code 9 ({sens}) et sont exclues."
    return texte


def resume(tableau, dico, puce):
    """Résumé : colonnes mesurées par la puce, et colonnes cliniques les moins complètes."""
    cliniques = [c for c in dico.index if dico.loc[c, "bloc"] == "clinique" and c in tableau.columns]
    taux = {}
    for c in cliniques:
        _, _, _, neuf_exclus, _ = effectifs(tableau[c], c, "clinique")
        taux[c] = (tableau[c].notna().sum() - neuf_exclus) / len(tableau) * 100
    incompletes = sorted((c for c in taux if taux[c] < 99.95), key=taux.get)[:NB_PLUS_INCOMPLETES]
    ligne = ", ".join(f"{c} ({taux[c]:.1f} %)" for c in incompletes) or "aucune, toutes sont complètes"
    texte = (
        f"{len(tableau)} patients ({puce}). Colonnes cliniques les moins réellement renseignées "
        f"(cellules vides et 9 traités comme non renseignés exclus, sens non confirmé sauf Rural_or_urban_area) : {ligne}."
    )
    if puce != "toutes":
        mesurees = int(dico[f"puce_{puce}"].sum())
        texte += f" {mesurees} colonnes mesurées par cette puce, les {len(dico) - mesurees} autres sont non mesurées."
    return texte
