"""Tests de compter_patients.py, hors ligne, sur la table inventée de kit/exemple/.

Signé : équipe 5.
"""

from pathlib import Path

import pytest

from equipe.outils import compter_patients
from kit import donnees

MINI = Path(__file__).resolve().parents[2] / "kit" / "exemple" / "mini.csv"


@pytest.fixture
def tableau(monkeypatch):
    table = donnees.charger(MINI)
    monkeypatch.setattr(compter_patients.donnees, "charger", lambda: table)
    return table


def test_total_et_detail_par_puce(tableau):
    texte = compter_patients.compter_patients()
    assert texte.startswith("12 patients au total")
    # Le détail est calculé sur le tableau : sa somme redonne le total.
    comptes = tableau[donnees.COLONNE_PUCE].value_counts()
    for puce, n in comptes.items():
        assert f"{puce} : {n}" in texte


def test_une_puce(tableau):
    n = int((tableau[donnees.COLONNE_PUCE] == "ALEX").sum())
    assert compter_patients.compter_patients("ALEX") == f"{n} patients pour la puce ALEX."


def test_puce_inconnue(tableau):
    texte = compter_patients.compter_patients("PUCE_INVENTEE")
    assert texte.startswith("abstention") and "inconnue" in texte


def test_aucune_donnee_individuelle(tableau):
    # La sortie ne contient que des effectifs : aucun nom de colonne du tableau.
    texte = compter_patients.compter_patients()
    assert not any(colonne in texte for colonne in tableau.columns if colonne != donnees.COLONNE_PUCE)
