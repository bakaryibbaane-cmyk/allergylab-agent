"""Outil : nombre de patients dont aucun, ou au moins un, de plusieurs dosages dépasse un seuil.

Un patient n'est évalué que sur les colonnes que sa puce mesure (une cellule
vide veut dire « non mesuré », jamais zéro) et n'est compté que s'il en a au
moins une. Une clause clinique facultative restreint les patients à ceux dont
une colonne clinique porte certains codes (ou une valeur, pour Sensitization,
l'âge ou le mois), en écartant au besoin d'autres codes. L'outil ne dit jamais
ce qu'un code veut dire : le sens vient de decoder. Rend un texte court, jamais
le tableau. Signé : équipe 5.
"""

import pandas as pd
from smolagents import tool

from equipe.outils import communs, mesure
from equipe.outils.compter_par_code import _jetons
from kit import donnees

REGLES = ("aucun_positif", "au_moins_un_positif")


def _codes(texte):
    """Les codes d'un texte « 1, 3 », ou None si l'un n'est pas un nombre entier."""
    jetons = _jetons(texte) if texte.strip() else []
    return jetons if all(jeton.isdigit() for jeton in jetons) else None


def _liste_de_colonnes(colonnes, table):
    """Rend (noms des colonnes de dosage, libellé, raison d'échec)."""
    connues = communs.dosages()
    if colonnes.strip().lower() == "toutes":
        noms = [nom for nom in connues if nom in table.columns]
        return noms, "toutes les colonnes de dosage", None
    noms = list(dict.fromkeys(nom.strip() for nom in colonnes.split(",") if nom.strip()))
    if not noms:
        return [], "", "il faut des noms de colonnes de dosage séparés par une virgule, ou « toutes »."
    inconnus = [nom for nom in noms if nom not in connues]
    if inconnus:
        return [], "", f"{', '.join(repr(nom) for nom in inconnus)} n'est pas une colonne de dosage du fichier."
    absentes = [nom for nom in noms if nom not in table.columns]
    if absentes:
        return [], "", f"{', '.join(repr(nom) for nom in absentes)} n'existe pas dans le fichier."
    pluriel = "s" if len(noms) > 1 else ""
    return noms, f"{len(noms)} colonne{pluriel} choisie{pluriel}", None


def _perimetre(evalues, table, puce):
    """« Calculé sur ALEX seule : » si toutes les puces ne comptent pas des patients évalués ; sinon rien."""
    if puce is not None:
        return ""
    presentes = set(table.loc[evalues, donnees.COLONNE_PUCE])
    ordre = [nom for nom in communs.puces() if nom in presentes]
    if not ordre or len(ordre) == len(communs.puces()):
        return ""
    return f"Calculé sur {ordre[0] + ' seule' if len(ordre) == 1 else ' et '.join(ordre)} : "


@tool
def patients_selon_dosages(
    colonnes: str,
    seuil: float,
    regle: str,
    inclusif: bool = False,
    filtre_colonne: str = "",
    filtre_codes: str = "",
    exclure_codes: str = "",
    puce: str | None = None,
) -> str:
    """Rend le nombre de patients dont aucun, ou au moins un, des dosages choisis dépasse un seuil.

    Positif = dosage > seuil, ou >= seuil si inclusif est vrai. Un patient est
    évalué sur les colonnes que sa puce mesure et compté s'il en a au moins une.
    Clause clinique facultative : filtre_colonne et filtre_codes gardent les
    patients dont la cellule porte au moins un de ces codes (cellule à codes
    multiples, ou Sensitization, l'âge ou le mois en égalité) ; exclure_codes
    écarte ceux dont la cellule porte un de ces codes. Le texte rendu dit le
    dénominateur. Il donne aussi, quand un filtre est posé, la part des patients
    qui vérifient la règle et ont le filtre. Le sens d'un code vient de decoder.
    Si les données ne permettent pas de conclure, le texte rendu commence par
    « abstention » : reprends alors cette raison.

    Args:
        colonnes: noms de colonnes de dosage séparés par une virgule, ou « toutes ».
        seuil: le seuil de positivité, par exemple 0.35.
        regle: « aucun_positif » (aucun dosage évalué ne dépasse le seuil) ou « au_moins_un_positif ».
        inclusif: vrai si un dosage égal au seuil est positif (>=), faux si le seuil est strict (>).
        filtre_colonne: colonne clinique de la clause ; vide pour ne poser aucun filtre.
        filtre_codes: le ou les codes cherchés dans filtre_colonne, séparés par une virgule ou un espace.
        exclure_codes: le ou les codes qui écartent le patient (par exemple « 9 »), vide pour aucun.
        puce: type de puce (Chip_Type) à étudier ; None pour toutes les puces.
    """
    if regle not in REGLES:
        return f"abstention : la règle doit être l'une de : {', '.join(REGLES)}."
    toutes = communs.puces()
    if puce is not None and puce not in toutes:
        return f"abstention : la puce {puce!r} est inconnue (puces : {', '.join(toutes)})."
    filtre_colonne = filtre_colonne.strip()
    codes, exclus = _codes(filtre_codes), _codes(exclure_codes)
    if codes is None or exclus is None:
        return "abstention : les codes doivent être des nombres entiers séparés par une virgule ou un espace."
    if not filtre_colonne and (codes or exclus):
        return "abstention : des codes sont donnés sans colonne de filtre (filtre_colonne)."
    if filtre_colonne and not codes:
        return "abstention : le filtre demande au moins un code dans filtre_codes."
    if filtre_colonne and not mesure.est_clinique(filtre_colonne):
        return f"abstention : {filtre_colonne!r} n'est pas une colonne clinique du fichier."

    with communs.table_en_memoire() as table:
        noms, libelle, raison = _liste_de_colonnes(colonnes, table)
        if raison:
            return f"abstention : {raison}"
        lues, perimetre_lignes = {}, set()
        for nom in noms:
            valeurs, _, raison = mesure._lire(nom, puce)
            if raison:
                return f"abstention : {raison}"
            lues[nom] = pd.to_numeric(valeurs, errors="coerce")
            perimetre_lignes |= set(valeurs.index)  # les patients des puces qui mesurent cette colonne
        dosages = pd.DataFrame(lues).reindex(table.index)
        cellules_filtre = None
        if filtre_colonne:
            cellules_filtre, _, raison = mesure._lire(filtre_colonne, puce)
            if raison:
                return f"abstention : {raison}"
            cellules_filtre = cellules_filtre.reindex(table.index)

    # Évalué : au moins un dosage mesuré parmi ceux choisis, sur une puce qui le mesure.
    evalues = dosages.notna().any(axis=1)
    cadre = "la puce " + puce if puce else "tout le fichier"
    if int(evalues.sum()) == 0:
        return f"abstention : aucun patient n'a l'un de ces dosages mesuré ({cadre})."
    if int(evalues.sum()) < mesure.EFFECTIF_MINIMAL:
        return f"abstention : {int(evalues.sum())} patients évalués ({cadre}), minimum {mesure.EFFECTIF_MINIMAL}."
    taux_evalues = int(evalues.sum()) / len(perimetre_lignes)
    if taux_evalues < mesure.TAUX_RENSEIGNEMENT_MINIMAL:
        return (
            f"abstention : ces dosages ne sont mesurés que pour {taux_evalues:.0%} des patients ({cadre}), "
            f"minimum {mesure.TAUX_RENSEIGNEMENT_MINIMAL:.0%}."
        )

    positifs = (dosages >= seuil) if inclusif else (dosages > seuil)
    verifie = positifs.any(axis=1) if regle == "au_moins_un_positif" else ~positifs.any(axis=1)

    # Clause clinique : renseignée, sans code exclu, puis avec l'un des codes cherchés.
    base, avec_filtre, vides, ecartes = evalues, evalues, 0, 0
    if filtre_colonne:
        listes = cellules_filtre.dropna().map(_jetons)
        if not all(jeton.isdigit() for liste in listes for jeton in liste):
            return f"abstention : {filtre_colonne!r} n'est pas une colonne de codes (cellules non numériques)."
        renseignee = cellules_filtre.notna()
        porte_exclu = listes.map(lambda liste: any(code in liste for code in exclus)).reindex(table.index, fill_value=False).astype(bool)
        porte_code = listes.map(lambda liste: any(code in liste for code in codes)).reindex(table.index, fill_value=False).astype(bool)
        vides = int((evalues & ~renseignee).sum())
        ecartes = int((evalues & renseignee & porte_exclu).sum())
        base = evalues & renseignee & ~porte_exclu
        avec_filtre = base & porte_code
    population = avec_filtre
    denominateur = int(population.sum())
    if denominateur < mesure.EFFECTIF_MINIMAL:
        return (
            f"abstention : {denominateur} patients évalués vérifient le filtre ({cadre}), "
            f"minimum {mesure.EFFECTIF_MINIMAL}."
        )
    nombre = int((population & verifie).sum())
    moins_un = int((dosages[population] == -1).sum().sum())

    operateur = communs.OPERATEURS[">=" if inclusif else ">"][1]
    sujet = "n'ont aucun dosage" if regle == "aucun_positif" else "ont au moins un dosage"
    texte = (
        f"{_perimetre(evalues, table, puce)}{communs.entier(nombre)} patients sur {communs.entier(denominateur)} "
        f"({communs.fr(100 * nombre / denominateur)} %) {sujet} {operateur} {communs.valeur_texte(seuil)}"
        f" parmi {libelle}{', parmi ceux qui vérifient le filtre' if filtre_colonne else ''} ({cadre})."
    )
    texte += (
        f"\nDéfinition : positif = dosage {operateur} {communs.valeur_texte(seuil)} ; un patient est évalué sur les colonnes "
        "que sa puce mesure (cellule vide = non mesuré, jamais zéro) et compté s'il en a au moins une ; "
        f"dénominateur = patients évalués{' qui vérifient le filtre' if filtre_colonne else ''}."
    )
    if filtre_colonne:
        verifiant_regle = int((base & verifie).sum())
        texte += (
            f"\nFiltre : {filtre_colonne!r} porte au moins un des codes {', '.join(codes)}"
            f"{' ; cellule portant un des codes ' + ', '.join(exclus) + ' écartée (' + communs.entier(ecartes) + ' patients)' if exclus else ''}"
            f" ; {communs.entier(vides)} patients évalués à cellule vide écartés. "
            f"Parmi les {communs.entier(verifiant_regle)} patients évalués qui vérifient la règle et ont {filtre_colonne!r} renseignée, "
            f"{communs.entier(nombre)} ({communs.fr(100 * nombre / verifiant_regle) if verifiant_regle else '0'} %) portent le filtre."
        )
        taux = int(base.sum()) / int(evalues.sum())
        if taux < mesure.TAUX_RENSEIGNEMENT_MINIMAL:
            texte += (
                f" Attention : {filtre_colonne!r} n'est retenue que pour {round(100 * taux)} % des patients évalués, "
                "résultat non représentatif de toute la cohorte."
            )
    if moins_un:
        texte += (
            f" {communs.entier(moins_un)} valeurs -1 parmi ces patients : comptées comme mesures non positives, "
            "leur sens n'est pas confirmé, elles n'ont pas été recodées."
        )
    return texte
