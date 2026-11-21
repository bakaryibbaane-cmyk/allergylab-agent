"""Tests de patients_selon_dosages.py, hors ligne, sur la table inventée de kit/exemple/.

Chaque attendu est recalculé ici, à la main, sur la table inventée. Le seuil
réel (30) n'est jamais atteint par cette table : on le baisse le temps du
test. Signé : équipe 5.
"""

import re
from pathlib import Path

import pandas as pd
import pytest

from equipe.outils import communs, mesure
from equipe.outils import patients_selon_dosages as module
from kit import donnees

outil = module.patients_selon_dosages
MINI = Path(__file__).resolve().parents[2] / "kit" / "exemple" / "mini.csv"


@pytest.fixture
def tableau(monkeypatch):
    table = donnees.charger(MINI)
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    return table


def _modifie(monkeypatch, table, ligne, colonne, valeur):
    table = table.copy()
    table[colonne] = table[colonne].astype(object) if isinstance(valeur, str) else table[colonne]
    table.loc[ligne, colonne] = valeur
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    return table


def _dosages(table, colonnes=None):
    noms = [c for c in communs.dosages() if c in table.columns]
    return table[noms if colonnes is None else colonnes]


def _attendu(table, regle, seuil, inclusif=False, colonnes=None, garde=None):
    """(nombre, dénominateur) calculés à la main : patients évalués = au moins un dosage non vide."""
    cadre = _dosages(table, colonnes)
    evalues = cadre.notna().any(axis=1)
    positifs = ((cadre >= seuil) if inclusif else (cadre > seuil)).any(axis=1)
    verifie = positifs if regle == "au_moins_un_positif" else ~positifs
    population = evalues if garde is None else evalues & garde
    return int((population & verifie).sum()), int(population.sum())


def _lire(texte):
    """Le nombre et le dénominateur de la première phrase : « 4 patients sur 12 (33,3 %) »."""
    trouve = re.search(r"(\d+) patients sur (\d+) ", texte.replace(" ", " "))
    return int(trouve.group(1)), int(trouve.group(2))


def test_arguments_invalides(tableau):
    assert outil("toutes", 0.35, "moyenne").startswith("abstention")
    assert outil("toutes", 0.35, "aucun_positif", puce="PUCE_INVENTEE").startswith("abstention")
    assert outil("Colonne_Inventee", 0.35, "aucun_positif").startswith("abstention")
    assert outil("Age", 0.35, "aucun_positif").startswith("abstention")  # une colonne clinique n'est pas un dosage
    assert outil("  , ", 0.35, "aucun_positif").startswith("abstention")
    assert outil("toutes", 0.35, "aucun_positif", filtre_colonne="Sensitization").startswith("abstention")  # sans code
    assert outil("toutes", 0.35, "aucun_positif", filtre_codes="1").startswith("abstention")  # sans colonne
    assert outil("toutes", 0.35, "aucun_positif", exclure_codes="9").startswith("abstention")  # sans colonne
    assert outil("toutes", 0.35, "aucun_positif", filtre_colonne="Sensitization", filtre_codes="a").startswith("abstention")
    assert outil("toutes", 0.35, "aucun_positif", filtre_colonne="Act_d_1", filtre_codes="1").startswith("abstention")
    assert outil("toutes", 0.35, "aucun_positif", filtre_colonne="French_Region", filtre_codes="1").startswith("abstention")


def test_aucun_et_au_moins_un_se_completent(tableau):
    aucun = outil("toutes", 0.35, "aucun_positif")
    au_moins = outil("toutes", 0.35, "au_moins_un_positif")
    assert _lire(aucun) == _attendu(tableau, "aucun_positif", 0.35)
    assert _lire(au_moins) == _attendu(tableau, "au_moins_un_positif", 0.35)
    assert _lire(aucun)[0] + _lire(au_moins)[0] == _lire(aucun)[1] == 12
    assert "strictement supérieur à 0,35" in aucun and "jamais zéro" in aucun


def test_liste_de_colonnes_et_doublons(tableau):
    texte = outil("Act_d_1, Aln_g_1, Act_d_1", 0.35, "au_moins_un_positif")
    assert _lire(texte) == _attendu(tableau, "au_moins_un_positif", 0.35, colonnes=["Act_d_1", "Aln_g_1"])
    assert "2 colonnes choisies" in texte
    assert "1 colonne choisie" in outil("Act_d_1", 0.35, "au_moins_un_positif")


def test_ex_aequo_du_seuil(tableau):
    # La table a une valeur égale à 0,6 dans Act_d_1 : strict, elle ne compte pas ; inclusif, elle compte.
    assert (tableau["Act_d_1"] == 0.6).sum() == 1
    strict = outil("Act_d_1", 0.6, "au_moins_un_positif")
    inclusif = outil("Act_d_1", 0.6, "au_moins_un_positif", inclusif=True)
    assert _lire(strict)[0] == _attendu(tableau, "au_moins_un_positif", 0.6, colonnes=["Act_d_1"])[0]
    assert _lire(inclusif)[0] == _lire(strict)[0] + 1
    assert "strictement supérieur à 0,6" in strict and "supérieur ou égal à 0,6" in inclusif


def test_patient_sans_colonne_mesuree_n_est_jamais_compte(tableau, monkeypatch):
    table = tableau.copy()
    colonnes = [c for c in communs.dosages() if c in table.columns]
    table.loc[0, colonnes] = float("nan")
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    for regle in ("aucun_positif", "au_moins_un_positif"):
        nombre, denominateur = _lire(outil("toutes", 0.35, regle))
        assert (nombre, denominateur) == _attendu(table, regle, 0.35)
        assert denominateur == 11  # le patient sans mesure n'est évalué dans aucun des deux sens


def test_une_cellule_vide_n_est_pas_un_zero(tableau, monkeypatch):
    # Un patient dont les seuls dosages sont vides sauf un zéro : évalué, et aucun positif. Un patient tout vide : pas évalué.
    table = tableau.copy()
    colonnes = [c for c in communs.dosages() if c in table.columns]
    table.loc[1, colonnes] = float("nan")
    table.loc[1, "Act_d_1"] = 0.0
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    assert _lire(outil("toutes", 0.35, "aucun_positif")) == _attendu(table, "aucun_positif", 0.35)
    assert _lire(outil("toutes", 0.35, "aucun_positif"))[1] == 12


def test_colonne_mesuree_par_certaines_puces_seulement(tableau):
    # Act_d_8 n'est pas mesurée par ALEX : les patients ALEX ne sont pas évalués, et le texte le dit.
    texte = outil("Act_d_8", 0.35, "au_moins_un_positif")
    assert texte.startswith("Calculé sur ISAC_V1 et ISAC_V2 : ")
    garde = tableau["Chip_Type"] != "ALEX"
    assert _lire(texte) == _attendu(tableau, "au_moins_un_positif", 0.35, colonnes=["Act_d_8"], garde=garde)
    assert _lire(texte)[1] == 8
    # Avec une puce : le périmètre est cette puce, sans préfixe.
    seule = outil("Act_d_8", 0.35, "au_moins_un_positif", puce="ISAC_V1")
    assert not seule.startswith("Calculé sur") and _lire(seule)[1] == 4 and "la puce ISAC_V1" in seule
    # Une puce qui ne mesure pas la colonne : abstention.
    assert outil("Act_d_8", 0.35, "au_moins_un_positif", puce="ALEX").startswith("abstention")


def test_filtre_sur_sensitization(tableau):
    texte = outil("toutes", 0.35, "aucun_positif", filtre_colonne="Sensitization", filtre_codes="1")
    garde = tableau["Sensitization"] == 1
    assert _lire(texte) == _attendu(tableau, "aucun_positif", 0.35, garde=garde)
    assert "parmi ceux qui vérifient le filtre" in texte and "dénominateur = patients évalués qui vérifient le filtre" in texte
    assert "'Sensitization' porte au moins un des codes 1" in texte


def test_filtre_sur_cellule_a_codes_multiples(tableau, monkeypatch):
    # « 1, 3 » porte le code 1 et le code 3 ; « 10 » n'est pas le code 1.
    table = _modifie(monkeypatch, tableau, 11, "Treatment_of_athsma", "10")
    jetons = table["Treatment_of_athsma"].astype(str).map(lambda c: [j for j in re.split(r"[,\s]+", c.strip()) if j])
    garde = jetons.map(lambda liste: "1" in liste)
    assert garde.sum() == 4 and any("1" not in liste and "10" in liste for liste in jetons)
    texte = outil("toutes", 0.35, "au_moins_un_positif", filtre_colonne="Treatment_of_athsma", filtre_codes="1")
    assert _lire(texte) == _attendu(table, "au_moins_un_positif", 0.35, garde=garde)
    # Plusieurs codes demandés : au moins un des deux, séparés par une virgule ou un espace.
    garde13 = jetons.map(lambda liste: "1" in liste or "3" in liste)
    assert _lire(outil("toutes", 0.35, "au_moins_un_positif", filtre_colonne="Treatment_of_athsma", filtre_codes="1 3")) == _attendu(
        table, "au_moins_un_positif", 0.35, garde=garde13
    )


def test_codes_exclus_ecartent_le_patient_meme_avec_le_code_cherche(tableau):
    jetons = tableau["Treatment_of_athsma"].astype(str).map(lambda c: [j for j in re.split(r"[,\s]+", c.strip()) if j])
    garde = jetons.map(lambda liste: "1" in liste and "3" not in liste)
    texte = outil(
        "toutes", 0.35, "au_moins_un_positif", filtre_colonne="Treatment_of_athsma", filtre_codes="1", exclure_codes="3"
    )
    assert _lire(texte) == _attendu(tableau, "au_moins_un_positif", 0.35, garde=garde)
    assert "cellule portant un des codes 3 écartée (1 patients)" in texte


def test_neuf_de_la_liste_de_mesure_est_non_renseigne_et_part_du_denominateur(tableau, monkeypatch):
    # Treatment_of_rhinitis est dans COLONNES_9_NON_RENSEIGNE : son 9 vaut « vide » et le patient est écarté, comme les vides.
    table = _modifie(monkeypatch, tableau, 0, "Treatment_of_rhinitis", "9")
    texte = outil("toutes", 0.35, "au_moins_un_positif", filtre_colonne="Treatment_of_rhinitis", filtre_codes="0 1 2")
    codes = table["Treatment_of_rhinitis"].astype(str).map(lambda c: [j for j in re.split(r"[,\s]+", c.strip()) if j])
    garde = codes.map(lambda liste: any(j in liste for j in ("0", "1", "2")))
    garde[0] = False
    assert _lire(texte) == _attendu(table, "au_moins_un_positif", 0.35, garde=garde)
    assert "1 patients évalués à cellule vide écartés" in texte


def test_part_des_patients_qui_verifient_la_regle_et_portent_le_filtre(tableau):
    texte = outil("toutes", 0.35, "au_moins_un_positif", filtre_colonne="Sensitization", filtre_codes="1")
    renseignes = tableau["Sensitization"].notna()
    nombre, _ = _attendu(tableau, "au_moins_un_positif", 0.35, garde=tableau["Sensitization"] == 1)
    parmi, _ = _attendu(tableau, "au_moins_un_positif", 0.35, garde=renseignes)
    assert f"Parmi les {parmi} patients évalués qui vérifient la règle" in texte
    assert f"{nombre} (" in texte.split("Parmi les")[1]


def test_moins_un_compte_signale_et_jamais_recode(tableau, monkeypatch):
    table = tableau.copy()
    colonnes = [c for c in communs.dosages() if c in table.columns]
    table.loc[0, colonnes] = float("nan")
    table.loc[0, "Act_d_1"] = -1.0  # le seul dosage de ce patient : mesuré, non positif
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    texte = outil("toutes", 0.35, "aucun_positif")
    assert _lire(texte) == _attendu(table, "aucun_positif", 0.35)
    assert "1 valeurs -1" in texte and "pas été recodées" in texte


def test_abstentions_de_seuil(tableau, monkeypatch):
    # Aucun patient ne porte ce code : zéro patient qui vérifie le filtre.
    assert outil("toutes", 0.35, "aucun_positif", filtre_colonne="Treatment_of_athsma", filtre_codes="8").startswith("abstention")
    # Sous le minimum réel de 30 patients, la table inventée entière s'abstient.
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 30)
    assert outil("toutes", 0.35, "aucun_positif").startswith("abstention")


def test_taux_de_mesure_sous_la_moitie_des_patients_des_puces_mesurantes(tableau, monkeypatch):
    # Une colonne mesurée par les trois puces mais vide pour 7 patients sur 12 : sous 50 %, on s'abstient.
    table = tableau.copy()
    table.loc[table.index[:7], "Cor_a_14"] = float("nan")
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    assert outil("Cor_a_14", 0.35, "au_moins_un_positif").startswith("abstention")


def test_le_texte_rendu_n_est_jamais_le_tableau_et_ne_dit_pas_le_sens_d_un_code(tableau):
    texte = outil("toutes", 0.35, "au_moins_un_positif", filtre_colonne="Treatment_of_athsma", filtre_codes="1")
    assert "EX01" not in texte
    assert "signifie" not in texte.lower() and "veut dire" not in texte.lower()
    assert texte.count("\n") <= 2
