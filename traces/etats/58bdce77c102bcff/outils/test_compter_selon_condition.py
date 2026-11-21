"""Tests de compter_selon_condition.py, hors ligne, sur la table inventée de kit/exemple/.

Le seuil réel (30) n'est jamais atteint par la table inventée : pour le cas
normal, on le baisse le temps du test. Signé : équipe 5.
"""

from pathlib import Path

import pytest

from equipe.outils import compter_selon_condition as outil
from equipe.outils import communs, mesure
from kit import donnees

MINI = Path(__file__).resolve().parents[2] / "kit" / "exemple" / "mini.csv"


@pytest.fixture
def tableau(monkeypatch):
    table = donnees.charger(MINI)
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    return table


def test_operateur_inconnu(tableau):
    assert outil.compter_selon_condition("Age", "~", 18).startswith("abstention")


def test_colonne_inconnue_ou_codee(tableau):
    assert outil.compter_selon_condition("Colonne_Inventee", ">", 1).startswith("abstention")
    texte = outil.compter_selon_condition("Rural_or_urban_area", ">", 0)
    assert texte.startswith("abstention") and "codée" in texte


def test_seuil_strict_ou_non(tableau):
    ages = tableau["Age"]
    strict = outil.compter_selon_condition("Age", "<", 18)
    large = outil.compter_selon_condition("Age", "<=", 18)
    assert f"{int((ages < 18).sum())} patients sur 12 mesurés" in strict
    assert f"{int((ages <= 18).sum())} patients sur 12 mesurés" in large
    assert "strictement inférieur à 18 (<)" in strict


def test_egalite_et_difference_se_completent(tableau):
    egal = outil.compter_selon_condition("Age", "==", 34)
    diff = outil.compter_selon_condition("Age", "!=", 34)
    n_egal = int(egal.split(" patients")[0])
    n_diff = int(diff.split(" patients")[0])
    assert n_egal + n_diff == 12


def test_denominateur_mesure_pas_les_lignes(tableau):
    # Aca_m, ALEX seule : 4 patients mesurés, pas les 12 lignes.
    texte = outil.compter_selon_condition("Aca_m", ">", 0, "ALEX")
    assert "sur 4 mesurés" in texte and "la puce ALEX" in texte


def test_effectif_sous_le_seuil(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 30)
    texte = outil.compter_selon_condition("Act_d_1", ">", 0, "ALEX")
    assert texte.startswith("abstention") and "minimum 30" in texte


def test_prefixe_quand_la_puce_n_est_pas_precisee(tableau):
    texte = outil.compter_selon_condition("Aca_m", ">=", 0)
    assert texte.startswith("Calculé sur ")


def test_le_fichier_n_est_lu_qu_une_fois_et_restitue(tableau):
    avant = mesure.donnees.charger
    outil.compter_selon_condition("Age", ">", 0)
    assert mesure.donnees.charger is avant


def test_aucune_donnee_individuelle(tableau):
    texte = outil.compter_selon_condition("Age", ">", 0)
    assert "EX01" not in texte
    assert communs.valeur_texte(0.35) == "0,35"
