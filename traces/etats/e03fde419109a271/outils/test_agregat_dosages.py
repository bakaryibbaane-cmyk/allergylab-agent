"""Tests de agregat_dosages.py, hors ligne, sur la table inventée de kit/exemple/.

Signé : équipe 5.
"""

from pathlib import Path

import pytest

from equipe.outils import agregat_dosages as outil
from equipe.outils import communs, mesure
from kit import donnees

MINI = Path(__file__).resolve().parents[2] / "kit" / "exemple" / "mini.csv"


@pytest.fixture
def tableau(monkeypatch):
    table = donnees.charger(MINI)
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    return table


def _dosages(table, puce=None):
    colonnes = [c for c in communs.dosages() if c in table.columns]
    lignes = table if puce is None else table[table[donnees.COLONNE_PUCE] == puce]
    return lignes[colonnes]


def test_arguments_invalides(tableau):
    assert outil.agregat_dosages("moyenne").startswith("abstention")
    assert outil.agregat_dosages("cellules_non_vides", "PUCE_INVENTEE").startswith("abstention")


def test_cellules_non_vides_et_detail_par_puce(tableau):
    brut = _dosages(tableau)
    texte = outil.agregat_dosages("cellules_non_vides")
    assert texte.startswith(f"{int(brut.notna().sum().sum())} cellules de dosage non vides")
    for puce in communs.puces():
        n = int(_dosages(tableau, puce).notna().sum().sum())
        assert f"{puce} : {n} sur" in texte
    # Avec une puce : pas de détail par puce.
    assert "Par puce" not in outil.agregat_dosages("cellules_non_vides", "ALEX")


def test_zero_et_negatif_se_comptent_sur_les_cellules_non_vides(tableau):
    brut = _dosages(tableau)
    zeros = outil.agregat_dosages("cellules_egales_zero")
    assert zeros.startswith(f"{int((brut == 0).sum().sum())} cellules de dosage égales à zéro sur {int(brut.notna().sum().sum())} cellules non vides")
    # Une cellule vide n'est jamais un zéro : la somme des zéros reste sous le nombre de cellules non vides.
    assert int((brut == 0).sum().sum()) < brut.size


def test_negatives_et_moins_un_signales(tableau, monkeypatch):
    table = tableau.copy()
    table.loc[0, "Act_d_1"] = -1.0
    table.loc[1, "Aln_g_1"] = -0.5
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    texte = outil.agregat_dosages("cellules_negatives")
    assert texte.startswith("2 cellules de dosage strictement négatives")
    assert "Dont 1 valeurs -1" in texte and "pas été recodées" in texte


def test_patients_tous_zero(tableau):
    brut = _dosages(tableau)
    attendu = int(((brut.fillna(0) == 0).all(axis=1) & brut.notna().any(axis=1)).sum())
    mesures = int(brut.notna().any(axis=1).sum())
    texte = outil.agregat_dosages("patients_tous_zero")
    assert texte.startswith(f"{attendu} patients dont tous les dosages mesurés sont à zéro sur {mesures} patients")


def test_patient_sans_aucune_mesure_n_est_pas_tous_zero(tableau, monkeypatch):
    table = tableau.copy()
    colonnes = [c for c in communs.dosages() if c in table.columns]
    table.loc[0, colonnes] = float("nan")
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    mesures = int(table[colonnes].notna().any(axis=1).sum())
    assert f"sur {mesures} patients ayant au moins un dosage mesuré" in outil.agregat_dosages("patients_tous_zero")


def test_le_fichier_est_restitue(tableau):
    avant = mesure.donnees.charger
    outil.agregat_dosages("cellules_non_vides")
    assert mesure.donnees.charger is avant
