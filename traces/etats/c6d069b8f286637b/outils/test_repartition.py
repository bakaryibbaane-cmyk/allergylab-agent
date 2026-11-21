"""Tests de repartition.py, hors ligne, sur la table inventée de kit/exemple/.

La table inventée a 12 patients : pour tester un cas normal, on baisse le seuil
de 30 le temps du test. Signé : équipe 5.
"""

from pathlib import Path

import pytest

from equipe.outils import mesure, repartition
from kit import donnees

MINI = Path(__file__).resolve().parents[2] / "kit" / "exemple" / "mini.csv"


@pytest.fixture
def tableau(monkeypatch):
    table = donnees.charger(MINI)
    monkeypatch.setattr(mesure.donnees, "charger", lambda: table)
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 3)
    return table


def test_cas_normal(tableau):
    # Rural_or_urban_area : six patients de code 1, six de code 2.
    texte = repartition.repartition_categories("Rural_or_urban_area")
    assert "12 patients renseignés" in texte and "taux de renseignement 100,0 %" in texte
    assert "code 1 : 6 (50,0 %) ; code 2 : 6 (50,0 %)" in texte
    assert "9 =" not in texte and "Attention" not in texte
    # Un vide n'est pas un code : Skin_Symptoms compte 11 renseignés sur 12.
    assert "11 patients renseignés" in repartition.repartition_categories("Skin_Symptoms")


def test_9_exclu(tableau):
    for ligne in (0, 1, 2):
        tableau.loc[ligne, "Rural_or_urban_area"] = 9
    # Restent 9 patients : codes 2,1,2,1,2,1,2,1,2 = quatre 1 et cinq 2.
    texte = repartition.repartition_categories("Rural_or_urban_area")
    assert "9 patients renseignés" in texte
    assert "code 1 : 4 (44,4 %) ; code 2 : 5 (55,6 %)" in texte
    assert "Hors 3 valeurs 9 = non renseigné, exclues" in texte


def test_9_conserve_hors_de_la_liste(tableau):
    # Blood_Month_sample : 9 est un mois (déjà un patient en septembre, plus celui-ci).
    tableau.loc[0, "Blood_Month_sample"] = 9
    texte = repartition.repartition_categories("Blood_Month_sample")
    assert "code 9 : 2" in texte and "exclues" not in texte


def test_effectif_sous_le_seuil(tableau, monkeypatch):
    monkeypatch.setattr(mesure, "EFFECTIF_MINIMAL", 30)
    texte = repartition.repartition_categories("Rural_or_urban_area")
    assert texte.startswith("abstention") and "minimum 30" in texte


def test_taux_sous_50_pour_cent(tableau):
    for ligne in range(7):
        tableau.loc[ligne, "Rural_or_urban_area"] = 9
    # 5 patients renseignés sur 12 : 42 %, résultat rendu mais avec une mise en garde.
    texte = repartition.repartition_categories("Rural_or_urban_area")
    assert "5 patients renseignés" in texte and "taux de renseignement 41,7 %" in texte
    assert "Attention : renseignée pour 42 % des patients seulement" in texte
    assert "non représentatif de toute la cohorte" in texte


def test_colonne_de_dosage(tableau):
    texte = repartition.repartition_categories("Act_d_1")
    assert texte.startswith("abstention") and "dosage" in texte


def test_colonne_en_texte(tableau):
    texte = repartition.repartition_categories("Age_of_onsets")
    assert texte.startswith("abstention") and "texte" in texte


def test_colonne_inconnue_et_puce_inconnue(tableau):
    assert repartition.repartition_categories("Colonne_Inventee").startswith("abstention")
    assert "inconnue" in repartition.repartition_categories("Skin_Symptoms", "ISAC_V3")


def test_pas_une_colonne_codee(tableau, monkeypatch):
    monkeypatch.setattr(repartition, "NB_CODES_MAX", 5)
    texte = repartition.repartition_categories("Age")
    assert texte.startswith("abstention") and "pas une colonne codée" in texte
