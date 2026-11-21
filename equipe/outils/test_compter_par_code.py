"""Tests de compter_par_code.py, hors ligne, sur la table inventée de kit/exemple/.

Le seuil réel (30) n'est jamais atteint par la table inventée : on le baisse
le temps du test. Signé : équipe 5.
"""

from pathlib import Path

import pytest

from equipe.outils import compter_par_code as outil
from equipe.outils import mesure
from kit import donnees

MINI = Path(__file__).resolve().parents[2] / "kit" / "exemple" / "mini.csv"


@pytest.fixture
def tableau(monkeypatch):
    table = donnees.charger(MINI)
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    return table


def test_codes_mal_ecrits(tableau):
    assert outil.compter_par_code("Treatment_of_athsma", "").startswith("abstention")
    assert outil.compter_par_code("Treatment_of_athsma", "a").startswith("abstention")


def test_colonne_inconnue_dosage_ou_mesure(tableau):
    assert outil.compter_par_code("Colonne_Inventee", "1").startswith("abstention")
    assert outil.compter_par_code("Act_d_1", "1").startswith("abstention")
    assert outil.compter_par_code("Age", "1").startswith("abstention")


def test_code_seul_ou_associe(tableau):
    # Dans la table, 1 figure seul dans quatre cellules et associé dans « 1, 3 ».
    texte = outil.compter_par_code("Treatment_of_athsma", "1")
    assert "5 patients sur 12 renseignés" in texte
    # Plusieurs codes : au moins un des deux, séparés par une virgule ou un espace.
    assert "au moins un des codes 3, 4" in outil.compter_par_code("General_cofactors", "3 4")
    assert "3 patients sur 12" in outil.compter_par_code("General_cofactors", "3, 4")


def test_colonne_lue_en_nombre(tableau):
    # Skin_Symptoms est lue en nombres (0.0, 1.0) : le code 1 compte, 1.0 ne se confond pas avec 10.
    texte = outil.compter_par_code("Skin_Symptoms", "1")
    assert "5 patients sur 11 renseignés" in texte


def test_le_sens_d_un_code_n_est_jamais_dit(tableau):
    texte = outil.compter_par_code("Treatment_of_athsma", "1").lower()
    assert "signifie" not in texte and "veut dire" not in texte


def test_neuf_exclus_et_cellules_ambigues(tableau, monkeypatch):
    table = tableau.copy()
    table["Treatment_of_rhinitis"] = table["Treatment_of_rhinitis"].astype(str)
    table.loc[0, "Treatment_of_rhinitis"] = "9"
    table.loc[1, "Treatment_of_rhinitis"] = "1, 9"
    table.loc[2, "Treatment_of_rhinitis"] = "10"
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    texte = outil.compter_par_code("Treatment_of_rhinitis", "1")
    # Le « 9 » seul est exclu du dénominateur (11 renseignés) ; « 10 » n'est pas le code 1.
    assert "3 patients sur 11 renseignés" in texte
    assert "1 valeurs 9 exclues" in texte
    assert "Ambigu : 1 cellules ont un code à plusieurs chiffres" in texte
    assert "Ambigu : 1 cellules associent un 9" in texte


def test_colonne_hors_liste_ne_retire_aucun_neuf(tableau):
    texte = outil.compter_par_code("Treatment_of_athsma", "1")
    assert "Aucun 9 exclu" in texte


def test_faible_renseignement_prevenu_sans_abstention(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "TAUX_RENSEIGNEMENT_MINIMAL", 0.99)
    texte = outil.compter_par_code("Skin_Symptoms", "1")
    assert not texte.startswith("abstention") and "Attention : colonne renseignée pour 92 %" in texte


def test_effectif_sous_le_seuil(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 30)
    texte = outil.compter_par_code("Treatment_of_athsma", "1", "ALEX")
    assert texte.startswith("abstention") and "minimum 30" in texte
